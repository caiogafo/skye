"""``ModelRouter({"alias": ["provider/model", ...]})`` builds the full form (Requirement 22.8 of steering, property 14)."""

from __future__ import annotations

import pytest

from skye.base.exceptions import ConfigurationError
from skye.base.messages import UserMessage
from skye.router import FallbackConfig, ModelRouter, ModelTarget, RouteConfig
from tests.examples.fake_network import patched


@pytest.fixture(autouse=True)
def _keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")


def _explicit(**kwargs) -> ModelRouter:
    return ModelRouter(
        routes=[
            RouteConfig(alias="smart", targets=[ModelTarget(model="gpt-4o", provider="openai", api_key="k")]),
            RouteConfig(alias="smart/fallback1", targets=[ModelTarget(model="claude-3-5-sonnet", provider="anthropic", api_key="k")]),
        ],
        fallbacks=[FallbackConfig(primary="smart", fallbacks=["smart/fallback1"])],
        **kwargs,
    )


def test_the_shorthand_builds_the_same_router_as_the_full_form():
    short = ModelRouter({"smart": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"]})
    full = _explicit()
    assert short.aliases == full.aliases
    assert short.model_targets == full.model_targets
    assert short.fallbacks == full.fallbacks
    assert list(short.models) == list(full.models)


def test_the_first_entry_is_the_primary_and_the_shorthand_runs():
    router = ModelRouter({"smart": ["openai/gpt-4o"]})
    with patched():
        assert router.complete(messages=[UserMessage(content="hi")], model="smart").content


def test_an_explicit_fallback_wins_over_the_shorthand():
    explicit = [FallbackConfig(primary="smart", fallbacks=["other"])]
    router = ModelRouter({"smart": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"]}, fallbacks=explicit)
    assert router.fallbacks["smart"] == ["other"]


@pytest.mark.parametrize("bad", [{"a": ["gpt-4o"]}, {"a": []}])
def test_a_malformed_entry_is_a_configuration_error(bad):
    with pytest.raises(ConfigurationError):
        ModelRouter(bad)
