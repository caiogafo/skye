"""Tag routing of ``ModelRouter`` (task 5.2, Requirement 23.2): ``complete(..., tags=[...])`` only reaches targets with every tag."""

from __future__ import annotations

import pytest

from skye.base.exceptions import ProviderError
from skye.base.messages import UserMessage
from skye.router import ModelRouter, ModelTarget, RouteConfig
from tests.unit.router.fakes import FakeModel

MESSAGES = [UserMessage(content="hi")]


def _router() -> tuple[ModelRouter, dict[str, FakeModel]]:
    models = {
        "cheap": FakeModel("cheap"),
        "premium": FakeModel("premium"),
        "premium-eu": FakeModel("premium-eu"),
    }
    router = ModelRouter()
    router.register_model("cheap", models["cheap"], tags=["free"])
    router.register_model("premium", models["premium"], tags=["paid", "premium"])
    router.register_model("premium-eu", models["premium-eu"], tags=["paid", "premium", "eu"])
    return router, models


async def test_tags_alone_route_only_to_targets_with_every_tag() -> None:
    router, models = _router()
    for _ in range(6):
        response = await router.acomplete(messages=MESSAGES, tags=["paid", "eu"])
        assert response.content == "answer from premium-eu"
    assert models["cheap"].calls == 0
    assert models["premium"].calls == 0


async def test_tags_shared_by_several_targets_never_reach_one_without_them() -> None:
    router, models = _router()
    served = {
        (await router.acomplete(messages=MESSAGES, tags=["premium"])).content for _ in range(6)
    }
    assert served <= {"answer from premium", "answer from premium-eu"}
    assert models["cheap"].calls == 0


def test_the_sync_form_routes_by_tags_too() -> None:
    router, models = _router()
    assert router.complete(messages=MESSAGES, tags=["free"]).content == "answer from cheap"
    assert models["premium"].calls == models["premium-eu"].calls == 0


async def test_a_model_with_the_tags_is_used_as_named() -> None:
    router, _ = _router()
    response = await router.acomplete(messages=MESSAGES, model="premium", tags=["paid"])
    assert response.content == "answer from premium"


async def test_a_model_without_the_tags_is_refused() -> None:
    router, models = _router()
    with pytest.raises(ValueError, match="does not have required tags"):
        await router.acomplete(messages=MESSAGES, model="cheap", tags=["paid"])
    assert models["cheap"].calls == 0


async def test_tags_no_target_has_are_refused() -> None:
    router, _ = _router()
    with pytest.raises(ValueError, match="No models found with required tags"):
        await router.acomplete(messages=MESSAGES, tags=["gpu"])


async def test_neither_model_nor_tags_is_refused() -> None:
    router, _ = _router()
    with pytest.raises(ValueError):
        await router.acomplete(messages=MESSAGES)
    with pytest.raises(ValueError):
        router.complete(messages=MESSAGES)


async def test_set_model_tags_changes_what_a_tag_reaches() -> None:
    router, _ = _router()
    router.set_model_tags("cheap", ["free", "eu"])
    with pytest.raises(ValueError):
        await router.acomplete(messages=MESSAGES, tags=["free", "paid"])
    assert (
        await router.acomplete(messages=MESSAGES, tags=["free", "eu"])
    ).content == "answer from cheap"


async def test_the_registered_models_are_restored_after_a_tag_call_even_when_it_fails() -> None:
    router, models = _router()
    models["premium-eu"].always_fail = RuntimeError("down")
    before = dict(router.models)

    await router.acomplete(messages=MESSAGES, tags=["free"])
    assert router.models == before

    with pytest.raises(ProviderError):
        await router.acomplete(messages=MESSAGES, tags=["eu"])
    assert router.models == before


async def test_an_alias_with_tags_picks_only_its_targets_with_the_tags() -> None:
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="chat",
                targets=[
                    ModelTarget(model="small", provider="openai", api_key="k", tags=["free"]),
                    ModelTarget(model="large", provider="openai", api_key="k", tags=["paid"]),
                ],
            ),
            RouteConfig(
                alias="other",
                targets=[ModelTarget(model="x", provider="openai", api_key="k", tags=["paid"])],
            ),
        ]
    )
    # Replace the provider instances by fakes: no network.
    fakes = {model_id: FakeModel(model_id) for model_id in router.models}
    router.models.update(fakes)

    for _ in range(4):
        response = await router.acomplete(messages=MESSAGES, model="chat", tags=["paid"])
        assert response.content == "answer from chat:openai:large"
    assert fakes["chat:openai:small"].calls == 0
    assert fakes["other:openai:x"].calls == 0

    with pytest.raises(ValueError, match="No models found matching model 'chat'"):
        await router.acomplete(messages=MESSAGES, model="chat", tags=["eu"])
