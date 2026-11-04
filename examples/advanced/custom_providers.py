"""A custom provider: extend the base model provider, register it, and use it like any other.

``BaseModelProvider`` keeps what is common to every provider (the ``complete``/``stream``/``acomplete`` entry points, health tracking, retry)
and leaves the transformation to the subclass: how a request becomes the wire format, how the answer becomes a ``CompletionResponse``.
Once registered, ``skye.provider("shout")`` returns it, and a router can balance it with the others.

If you only need to wrap an SDK or a function, a ``Runnable`` is lighter: see ``examples/providers/bring_your_own_adapter.py``.
"""

from typing import Any

import skye
from skye import CompletionResponse, StreamChunk, TokenUsage
from skye import SkyeError
from skye import UserMessage
from skye.models import BaseModelProvider
from skye.models import ProviderRegistry


class ShoutProvider(BaseModelProvider):
    """A toy 'model' that answers by shouting the last message. The 'service' is a local function, so nothing leaves the process."""

    provider_name = "shout"

    # How the library's types become the wire format of the service
    def _initialize_client(self) -> Any:
        return None  # no SDK, no connection

    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        return [{"role": m.role, "text": m.content} for m in messages]

    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        return []  # this service has no tools

    def _transform_request(self, request) -> dict[str, Any]:
        return {"model": request.model, "messages": self._transform_messages(request.messages)}

    # The call itself (here a local function; in a real provider an HTTP call with `skye.base.http`)
    def _call_provider(self, request: dict[str, Any]) -> Any:
        text = request["messages"][-1]["text"]
        return {"id": "shout-1", "model": request["model"], "text": text.upper(), "tokens": len(text.split())}

    def _call_provider_stream(self, request: dict[str, Any]):
        for word in request["messages"][-1]["text"].upper().split():
            yield {"id": "shout-1", "delta": word + " "}

    # How the answer becomes the library's types
    def _transform_response(self, response: Any) -> CompletionResponse:
        return CompletionResponse(
            id=response["id"],
            model=response["model"],
            provider=self.provider_name,
            content=response["text"],
            role="assistant",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=response["tokens"], completion_tokens=response["tokens"], total_tokens=2 * response["tokens"]),
        )

    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        return StreamChunk(id=chunk["id"], delta=chunk["delta"], finish_reason=None, index=0)

    def _extract_capability_calls(self, response: Any) -> list[Any] | None:
        return None

    def format_capability_results(self, results: list[Any]) -> list[dict[str, Any]]:
        return []

    def get_model_info(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "name": "shout-1", "supports_streaming": True}


def main() -> None:
    # Registration: from now on the name "shout" is a provider like "openai"
    ProviderRegistry.register_model_provider("shout", ShoutProvider)

    client = skye.provider("shout")
    response = client.complete(messages=[UserMessage(content="hello from a custom provider")], model="shout-1")
    print(response.content, f"({response.usage.total_tokens} tokens)")

    print("stream:", "".join(chunk.delta for chunk in client.stream(messages=[UserMessage(content="one two three")], model="shout-1")))

    # Errors of the library are SkyeError: a call without messages is refused before any provider is reached
    try:
        client.complete(messages=None, model="shout-1")
    except (SkyeError, ValueError) as error:
        print("refused:", error)


if __name__ == "__main__":
    main()
