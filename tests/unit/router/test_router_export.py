"""``ModelRouter.to_config`` and ``to_skye``: a router written back as a configuration dictionary or
a ``.skye`` block.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from skye.base.dsl import check_text
from skye.router import ModelRouter
from skye.router.model_router import DEFAULT_ALLOWED_FAILS_POLICY, DEFAULT_RETRY_POLICY

SOURCE = """
router "main" {
  strategy = "least_busy"
  cooldown = "2m"
  enable_pre_call_checks = false

  route "fast" = ["openai/gpt-4o-mini", "anthropic/claude-haiku"]

  route "pri" {
    strategy = "latency_based"
    fallback = ["fast"]
    target {
      model = "gpt-4"
      provider = "openai"
      api_key = env.SKYE_EXPORT_KEY
      api_base = "https://gateway.example/v1"
      timeout = "30s"
      tpm = 100000
      rpm = 1000
      tags = ["premium"]
      metadata = { location = "va" }
    }
    target { model = "gpt-4", provider = "openai", api_key = "literal-secret", weight = 20 }
  }

  retry_policy "RateLimitError" { max_retries = 5 }
  allowed_fails_policy "ServerError" { allowed_fails_per_minute = 7 }
}
"""


@pytest.fixture
def source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("SKYE_EXPORT_KEY", "key-from-the-environment")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic")
    path = tmp_path / "router.skye"
    path.write_text(SOURCE, encoding="utf-8")
    return path


def _without_keys(config: dict[str, Any]) -> dict[str, Any]:
    routes = [
        {
            **route,
            "targets": [{k: v for k, v in t.items() if k != "api_key"} for t in route["targets"]],
        }
        for route in config["routes"]
    ]
    return {**config, "routes": routes}


def test_the_text_passes_the_checker_and_builds_the_same_router(
    source: Path, tmp_path: Path
) -> None:
    router = ModelRouter.from_file(source, name="main")
    text = router.to_skye("main")
    assert check_text(text, "out.skye") == []
    out = tmp_path / "out.skye"
    out.write_text(text, encoding="utf-8")
    again = ModelRouter.from_file(out, name="main")
    assert _without_keys(again.to_config()) == _without_keys(router.to_config())
    # A key that was left out is read again from the provider's standard variable, so the second
    # text may name it
    # (env.OPENAI_API_KEY); from then on writing is stable.
    second = again.to_skye("main")
    third = out.with_name("third.skye")
    third.write_text(second, encoding="utf-8")
    assert ModelRouter.from_file(third, name="main").to_skye("main") == second


def test_the_config_rebuilds_the_router(source: Path) -> None:
    router = ModelRouter.from_file(source, name="main")
    config = router.to_config(include_secrets=True)
    assert ModelRouter.from_config_dict(config).to_config(include_secrets=True) == config
    assert config["strategy"] == "least_busy" and config["cooldown_seconds"] == 120.0
    assert config["enable_pre_call_checks"] is False
    assert config["fallbacks"] == [
        {"primary": "fast", "fallbacks": ["fast/fallback1"]},
        {"primary": "pri", "fallbacks": ["fast"]},
    ]


def test_secrets_are_not_exported_by_default(source: Path) -> None:
    router = ModelRouter.from_file(source, name="main")
    for text in (router.to_skye(), str(router.to_config())):
        assert "literal-secret" not in text
        assert "key-from-the-environment" not in text
        assert "sk-openai" not in text and "sk-anthropic" not in text


def test_a_key_written_as_env_comes_back_as_env(source: Path) -> None:
    router = ModelRouter.from_file(source, name="main")
    assert "api_key = env.SKYE_EXPORT_KEY" in router.to_skye()
    target = router.to_config()["routes"][2]["targets"][0]
    assert target["api_key"] == "${SKYE_EXPORT_KEY}"
    assert (
        router.aliases["pri"].targets[0].api_key == "key-from-the-environment"
    )  # the router itself holds the value


def test_include_secrets_writes_a_key_that_was_given_in_clear(source: Path) -> None:
    router = ModelRouter.from_file(source, name="main")
    assert "literal-secret" in router.to_skye(include_secrets=True)
    assert (
        router.to_config(include_secrets=True)["routes"][2]["targets"][1]["api_key"]
        == "literal-secret"
    )


def test_only_what_differs_from_the_defaults_is_written(source: Path) -> None:
    router = ModelRouter.from_file(source, name="main")
    config = router.to_config()
    assert config["retry_policies"] == [{"error_type": "RateLimitError", "max_retries": 5}]
    assert config["allowed_fails_policies"] == [
        {"error_type": "ServerError", "allowed_fails_per_minute": 7}
    ]
    plain = ModelRouter.from_file(_write(source.parent, 'router { route "x" = ["openai/gpt-4"] }'))
    assert (
        plain.to_config()["retry_policies"] == []
        and plain.to_config()["allowed_fails_policies"] == []
    )
    assert "retry_policy" not in plain.to_skye() and "cooldown" not in plain.to_skye()
    assert (
        plain.retry_policy == DEFAULT_RETRY_POLICY
        and plain.allowed_fails_policy == DEFAULT_ALLOWED_FAILS_POLICY
    )


def test_a_route_strategy_is_written_only_when_it_differs_from_the_routers(source: Path) -> None:
    text = ModelRouter.from_file(source, name="main").to_skye()
    assert text.count("strategy =") == 2  # the router's and the one route that differs
    assert 'strategy = "least_busy"' in text and 'strategy = "latency_based"' in text


def test_the_label_is_optional(source: Path) -> None:
    router = ModelRouter.from_file(source, name="main")
    assert router.to_skye().startswith("router {")
    assert router.to_skye("main").startswith('router "main" {')


def test_a_router_built_in_python_is_written_too(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic")
    router = ModelRouter({"fast": ["openai/gpt-4o-mini", "anthropic/claude-haiku"]})
    text = router.to_skye("main")
    assert check_text(text, "out.skye") == []
    assert 'route "fast"' in text and 'fallback = ["fast/fallback1"]' in text
    assert "sk-openai" not in text and "sk-anthropic" not in text


def test_durations_are_written_with_a_unit(source: Path) -> None:
    text = ModelRouter.from_file(source, name="main").to_skye()
    assert 'cooldown = "2m"' in text and 'timeout = "30s"' in text


def _write(folder: Path, text: str) -> Path:
    path = folder / "plain.skye"
    path.write_text(text, encoding="utf-8")
    return path
