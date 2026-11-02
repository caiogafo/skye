"""``router.complete(messages=..., model=<alias>)`` resolves the alias to one of its targets (the documented call)."""

from __future__ import annotations

from skye.base.interfaces.router import RoutingStrategy
from skye.base.messages import UserMessage
from skye.router import FallbackConfig, ModelRouter, ModelTarget, RouteConfig
from tests.examples.fake_network import patched


def _router(**kwargs):
    return ModelRouter(
        routes=[
            RouteConfig(alias="gpt-4", targets=[ModelTarget(model="gpt-4", provider="openai", api_key="k")], strategy=RoutingStrategy.ROUND_ROBIN),
            RouteConfig(alias="fast", targets=[ModelTarget(model="gpt-3.5-turbo", provider="openai", api_key="k")]),
        ],
        **kwargs,
    )


def test_an_alias_is_resolved_to_a_target():
    with patched():
        response = _router().complete(messages=[UserMessage(content="hi")], model="gpt-4")
    assert response.content


def test_a_registered_model_id_is_used_as_is():
    router = _router()
    model_id = next(iter(router.models))
    with patched():
        assert router.complete(messages=[UserMessage(content="hi")], model=model_id).content


def test_the_fallback_of_an_alias_is_tried_when_the_primary_fails(monkeypatch):
    router = _router(fallbacks=[FallbackConfig(primary="gpt-4", fallbacks=["fast"])])
    primary = next(i for i in router.models if i.startswith("gpt-4:"))
    monkeypatch.setattr(router.models[primary], "complete", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    with patched():
        assert router.complete(messages=[UserMessage(content="hi")], model="gpt-4").content
