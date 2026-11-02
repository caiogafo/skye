"""Backend selection (task 15.1, Req 17): precedence, defaults, single decision, warnings."""

import subprocess
import sys
import types
import warnings

import pytest

from nimbus.base import backend_select as bs
from nimbus.base.exceptions import ConfigurationError, MissingExtraError
from nimbus.base.sdk_versions import SDK_REFERENCE, SdkRef


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    bs._reset_warnings_for_tests()
    for k in ("NIMBUS_MCP_IMPL", "NIMBUS_OPENAI_IMPL", "NIMBUS_IMPL", "NIMBUS_CONFIG"):
        monkeypatch.delenv(k, raising=False)


def _fake_sdk(monkeypatch, name="fakesdk", dist="fakesdk-dist", version="2.0"):
    monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setattr(bs.importlib.metadata, "version", lambda d: version)
    return {"mcp": SdkRef(name, dist, "mcp", "1.0")}


def test_default_is_builtin_without_import():
    sel = bs.select_impl("mcp", config={})
    assert (sel.impl, sel.explicit, sel.sdk) == ("builtin", False, None)


def test_precedence_chain():
    cfg = {"impl": {"mcp": "builtin", "default": "sdk"}}
    assert bs.resolve_impl("mcp", env={}, config=cfg) == ("builtin", True)
    assert bs.resolve_impl("mcp", env={"NIMBUS_MCP_IMPL": "sdk"}, config=cfg) == ("sdk", True)
    # specific config beats global env; global env beats global config
    assert bs.resolve_impl("mcp", env={"NIMBUS_IMPL": "sdk"}, config={"impl": {"mcp": "builtin"}})[0] == "builtin"
    assert bs.resolve_impl("openai", env={"NIMBUS_IMPL": "builtin"}, config=cfg)[0] == "builtin"
    assert bs.resolve_impl("openai", env={}, config=cfg)[0] == "sdk"
    assert bs.resolve_impl("mcp", env={"NIMBUS_MCP_IMPL": " "}, config={}) == ("builtin", False)


def test_invalid_value_raises():
    with pytest.raises(ConfigurationError):
        bs.resolve_impl("mcp", env={"NIMBUS_MCP_IMPL": "rest"}, config={})


def test_config_file_is_read_via_loader(tmp_path, monkeypatch):
    f = tmp_path / "nimbus.yaml"
    f.write_text("impl:\n  mcp: sdk\n")
    monkeypatch.setenv("NIMBUS_CONFIG", str(f))
    assert bs.resolve_impl("mcp", env={"NIMBUS_CONFIG": str(f)}) == ("sdk", True)
    monkeypatch.setenv("NIMBUS_MCP_IMPL", "builtin")
    assert bs.resolve_impl("mcp") == ("builtin", True)  # env wins over the file


def test_missing_default_file_is_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert bs.resolve_impl("mcp", env={}) == ("builtin", False)


def test_sdk_selected_and_version_mismatch_warns_exactly_once(monkeypatch):
    ref = _fake_sdk(monkeypatch)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        a = bs.select_impl("mcp", env={"NIMBUS_MCP_IMPL": "sdk"}, config={}, reference=ref)
        b = bs.select_impl("mcp", env={"NIMBUS_MCP_IMPL": "sdk"}, config={}, reference=ref)
    assert a.impl == b.impl == "sdk" and a.sdk is sys.modules["fakesdk"]
    assert len(w) == 1 and issubclass(w[0].category, bs.SDKSelectionWarning)
    assert "2.0" in str(w[0].message) and "1.0" in str(w[0].message) and "fakesdk-dist" in str(w[0].message)


def test_matching_or_unrecorded_version_does_not_warn(monkeypatch):
    ref = _fake_sdk(monkeypatch, version="1.0")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        bs.select_impl("mcp", env={"NIMBUS_MCP_IMPL": "sdk"}, config={}, reference=ref)
        ref_none = {"mcp": SdkRef("fakesdk", "fakesdk-dist", "mcp", None)}  # version not recorded
        bs.select_impl("mcp", env={"NIMBUS_MCP_IMPL": "sdk"}, config={}, reference=ref_none)


def test_builtin_requested_never_imports_sdk(monkeypatch):
    monkeypatch.setitem(sys.modules, "fakesdk", None)  # import would fail loudly
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sel = bs.select_impl("mcp", config={}, reference={"mcp": SdkRef("fakesdk", "d", "mcp", "1")})
    assert sel.impl == "builtin"


def test_import_failure_falls_back_with_one_warning(monkeypatch):
    monkeypatch.setitem(sys.modules, "fakesdk", None)
    ref = {"mcp": SdkRef("fakesdk", "d", "mcp", "1")}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        sel = bs.select_impl("mcp", env={"NIMBUS_MCP_IMPL": "sdk"}, config={}, reference=ref)
    assert (sel.impl, sel.requested) == ("builtin", "sdk")
    assert len(w) == 1 and "fall" in str(w[0].message)


def test_selection_is_fixed_per_instance(monkeypatch):
    ref = _fake_sdk(monkeypatch, version="1.0")
    sel = bs.select_impl("mcp", env={"NIMBUS_MCP_IMPL": "sdk"}, config={}, reference=ref)
    monkeypatch.setenv("NIMBUS_MCP_IMPL", "builtin")  # later env change does not touch the decision
    with pytest.raises(AttributeError):
        sel.impl = "builtin"  # frozen
    assert sel.impl == "sdk"


def test_sdk_only_backend(monkeypatch):
    only = ("sdk",)
    assert bs.select_impl("openai", available=only, env={}, config={}).impl == "sdk"  # default, not probed
    assert bs.select_impl("openai", available=only, env={"NIMBUS_IMPL": "builtin"}, config={}).impl == "sdk"
    with pytest.raises(ConfigurationError):
        bs.select_impl("openai", available=only, env={"NIMBUS_OPENAI_IMPL": "builtin"}, config={})
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(MissingExtraError):
        bs.select_impl("openai", available=only, env={"NIMBUS_OPENAI_IMPL": "sdk"}, config={})


def test_reference_table_covers_backends():
    assert {"mcp", "openai", "anthropic", "bedrock", "google"} <= set(SDK_REFERENCE)


def test_import_nimbus_imports_no_sdk():
    code = (
        "import sys, nimbus, nimbus.tools, nimbus.models.llm, nimbus.base.backend_select;"
        "bad=[m for m in ('fastmcp','openai','anthropic','boto3','vertexai','google.cloud.aiplatform') if m in sys.modules];"
        "assert not bad, bad"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_providers_decide_once_at_construction(monkeypatch):
    from nimbus.models.llm import AnthropicProvider, OpenAIProvider

    assert OpenAIProvider(api_key="k").selection.impl == "sdk"
    assert AnthropicProvider(api_key="k").selection.backend == "anthropic"
    monkeypatch.setenv("NIMBUS_OPENAI_IMPL", "builtin")
    with pytest.raises(ConfigurationError):
        OpenAIProvider(api_key="k")


def test_embedding_providers_decide_once_at_construction(monkeypatch):
    """Req 17: embedding adapters select builtin-vs-SDK through the same mechanism, once."""
    from nimbus.models.embeddings.openai_embeddings import OpenAIEmbeddingProvider

    emb = OpenAIEmbeddingProvider(model="text-embedding-3-small", api_key="k")
    assert emb.selection is not None and emb.selection.impl == "sdk"
    monkeypatch.setenv("NIMBUS_OPENAI_IMPL", "builtin")  # no REST path -> explicit builtin rejected
    with pytest.raises(ConfigurationError):
        OpenAIEmbeddingProvider(model="text-embedding-3-small", api_key="k")


def test_mcp_factory_uses_selection(monkeypatch):
    from nimbus.tools.mcp_client import BuiltinMCPClient, create_mcp_client

    assert isinstance(create_mcp_client("http://x"), BuiltinMCPClient)
    monkeypatch.setitem(sys.modules, "fastmcp", None)  # not installed (even if another test leaked a fake)
    monkeypatch.setenv("NIMBUS_MCP_IMPL", "sdk")  # fastmcp not installed: warn + fall back
    with pytest.warns(bs.SDKSelectionWarning):
        assert isinstance(create_mcp_client("http://x"), BuiltinMCPClient)


def test_sdk_runtime_error_maps_to_nimbus_error_and_does_not_reset(monkeypatch):
    """Req 17.8: a selected SDK's runtime error maps to a Nimbus error and propagates; the
    instance is NOT reset to the built-in implementation for that call or afterwards."""
    import tenacity.nap

    from nimbus.base.completion import CompletionRequest
    from nimbus.base.exceptions import ProviderError
    from nimbus.base.messages import UserMessage
    from nimbus.models.llm import OpenAIProvider

    # Skip the retry backoff waits so the mapped error surfaces immediately.
    monkeypatch.setattr(tenacity.nap.time, "sleep", lambda *_a, **_k: None)

    provider = OpenAIProvider(api_key="k")
    assert provider.selection is not None and provider.selection.impl == "sdk"

    class _SdkApiError(RuntimeError):
        """Stands in for an incompatible-SDK runtime failure."""

    def _boom(_request):
        raise _SdkApiError("SDK changed its API")

    monkeypatch.setattr(provider, "_call_provider", _boom)

    request = CompletionRequest(messages=[UserMessage(content="hi")], model="gpt-4")
    with pytest.raises(ProviderError) as excinfo:
        provider.complete(request)

    # Mapped to a Nimbus error that preserves the underlying cause (not silently swallowed).
    assert isinstance(excinfo.value.__cause__, _SdkApiError)
    # The instance keeps the SDK selection for its whole life: no reset to builtin.
    assert provider.selection.impl == "sdk"
