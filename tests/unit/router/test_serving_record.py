"""The serving record of ``ModelRouter``: which configuration served each request (task 2.1).

After a successful call the record is in ``response.metadata["router"]`` and in
``router.last_serving``; it names the alias, provider, model, target index, attempts and fallbacks
tried, and never holds a key. Fake models only, no network.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest

from skye.base.completion import CompleteResponse, StreamChunk, TokenUsage
from skye.base.exceptions import ProviderError
from skye.base.interfaces.model import ModelInterface
from skye.base.messages import UserMessage
from skye.router import FallbackConfig, ModelRouter, ModelTarget, RetryPolicyConfig, RouteConfig

MESSAGES = [UserMessage(content="hi")]
SECRET = "sk-secret-value-never-in-the-record"


class UnknownError(Exception):
    """An error type the tests set a retry policy for."""


class FakeModel(ModelInterface):
    """Answers, or raises the queued errors first; ``fail_always`` makes every call fail."""

    def __init__(self, name: str, errors: list[BaseException] | None = None) -> None:
        self.name = name
        self.errors = list(errors or [])
        self.fail_always: BaseException | None = None
        self.calls = 0

    def _answer(self) -> CompleteResponse:
        self.calls += 1
        if self.fail_always is not None:
            raise self.fail_always
        if self.errors:
            raise self.errors.pop(0)
        return CompleteResponse(
            content=f"answer from {self.name}",
            role="assistant",
            model=self.name,
            provider="fake",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            metadata={"from_model": True},
        )

    def complete(self, *args: Any, **kwargs: Any) -> CompleteResponse:
        return self._answer()

    async def acomplete(self, *args: Any, **kwargs: Any) -> CompleteResponse:
        return self._answer()

    def stream(self, *args: Any, **kwargs: Any) -> Iterator[StreamChunk]:
        yield StreamChunk(delta=self._answer().content, model=self.name)

    async def astream(self, *args: Any, **kwargs: Any) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(delta=self._answer().content, model=self.name)

    def get_model_info(self) -> dict[str, Any]:
        return {"name": self.name, "provider": "fake"}


def _alias_router(**kwargs: Any) -> tuple[ModelRouter, dict[str, FakeModel]]:
    """Alias ``chat`` with two targets, alias ``backup`` with one; every model is a fake."""
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="chat",
                targets=[
                    ModelTarget(model="gpt-4o", provider="openai", api_key=SECRET),
                    ModelTarget(model="gpt-4o-mini", provider="openai", api_key=SECRET),
                ],
            ),
            RouteConfig(
                alias="backup",
                targets=[ModelTarget(model="claude", provider="anthropic", api_key=SECRET)],
            ),
        ],
        allowed_fails_policies=None,
        **kwargs,
    )
    fakes = {model_id: FakeModel(model_id) for model_id in router.models}
    router.models.update(fakes)
    return router, fakes


def test_no_record_before_the_first_request() -> None:
    assert ModelRouter().last_serving is None


def test_the_record_names_the_alias_target_and_index() -> None:
    router, _ = _alias_router()

    first = router.complete(messages=MESSAGES, model="chat")
    second = router.complete(messages=MESSAGES, model="chat")  # round robin: the second target

    assert first.metadata["router"] == {
        "requested": "chat",
        "alias": "chat",
        "model_id": "chat:openai:gpt-4o",
        "provider": "openai",
        "model": "gpt-4o",
        "target_index": 0,
        "attempts": 1,
        "total_attempts": 1,
        "tried": [],
        "fallbacks_tried": [],
        "fallback": False,
    }
    assert second.metadata["router"]["target_index"] == 1
    assert second.metadata["router"]["model"] == "gpt-4o-mini"


def test_the_model_metadata_is_kept() -> None:
    router, _ = _alias_router()
    response = router.complete(messages=MESSAGES, model="chat")
    assert response.metadata["from_model"] is True


def test_last_serving_is_the_record_of_the_last_response() -> None:
    router, _ = _alias_router()
    router.complete(messages=MESSAGES, model="chat")
    response = router.complete(messages=MESSAGES, model="backup")

    assert router.last_serving == response.metadata["router"]
    assert router.last_serving is not None and router.last_serving["alias"] == "backup"


def test_last_serving_is_a_copy() -> None:
    router, _ = _alias_router()
    router.complete(messages=MESSAGES, model="backup")
    record = router.last_serving
    assert record is not None
    record["tried"].append("tampered")
    record["alias"] = "tampered"
    assert router.last_serving == {**record, "tried": [], "alias": "backup"}


def test_a_fallback_is_recorded_with_what_was_tried() -> None:
    router, fakes = _alias_router(fallbacks=[FallbackConfig(primary="chat", fallbacks=["backup"])])
    for model_id in ("chat:openai:gpt-4o", "chat:openai:gpt-4o-mini"):
        fakes[model_id].fail_always = UnknownError("down")

    response = router.complete(messages=MESSAGES, model="chat")
    record = response.metadata["router"]

    assert response.content == "answer from backup:anthropic:claude"
    assert record["requested"] == "chat"
    assert record["alias"] == "backup"
    assert (record["provider"], record["model"], record["target_index"]) == (
        "anthropic",
        "claude",
        0,
    )
    # fallback_on_error (the default): the other target of "chat" is tried before the fallback chain
    assert record["tried"] == ["chat:openai:gpt-4o", "chat:openai:gpt-4o-mini"]
    assert record["fallbacks_tried"] == ["backup"]
    assert record["fallback"] is True
    assert (record["attempts"], record["total_attempts"]) == (1, 3)


def test_retries_are_counted_in_the_attempts() -> None:
    router, fakes = _alias_router(
        retry_policies=[RetryPolicyConfig(error_type="UnknownError", max_retries=3)]
    )
    fakes["backup:anthropic:claude"].errors = [UnknownError("a"), UnknownError("b")]

    record = router.complete(messages=MESSAGES, model="backup").metadata["router"]

    assert (record["attempts"], record["total_attempts"], record["tried"]) == (3, 3, [])


def test_a_model_registered_directly_has_no_alias() -> None:
    router = ModelRouter()
    router.register_model("direct", FakeModel("direct"))

    record = router.complete(messages=MESSAGES, model="direct").metadata["router"]

    assert record["alias"] is None and record["target_index"] is None
    assert (record["model_id"], record["provider"], record["model"]) == ("direct", "fake", "direct")


async def test_the_async_path_records_too() -> None:
    router, _ = _alias_router()
    response = await router.acomplete(messages=MESSAGES, model="backup")
    assert response.metadata["router"]["model_id"] == "backup:anthropic:claude"
    assert router.last_serving == response.metadata["router"]


def test_a_failed_request_keeps_the_previous_record() -> None:
    router, fakes = _alias_router()
    router.complete(messages=MESSAGES, model="backup")
    fakes["backup:anthropic:claude"].fail_always = UnknownError("down")

    with pytest.raises(ProviderError):
        router.complete(messages=MESSAGES, model="backup")

    assert router.last_serving is not None and router.last_serving["total_attempts"] == 1


def test_the_record_holds_no_secret() -> None:
    router, _ = _alias_router()
    response = router.complete(messages=MESSAGES, model="chat")
    assert SECRET not in repr(response.metadata["router"])
    assert SECRET not in repr(router.last_serving)
    assert "api_key" not in response.metadata["router"]
