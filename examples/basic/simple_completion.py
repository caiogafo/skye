"""The core types of Skye: messages, a completion, token usage and a multi-turn conversation.

Message types are ``SystemMessage``, ``UserMessage``, ``AssistantMessage`` and ``CapabilityMessage``. ``client.complete`` takes the
messages and returns a ``CompleteResponse`` with the text, the provider, the token usage and the finish reason. Structured output is in
``examples/advanced/structured_output.py``; one example per provider is in ``examples/providers/``.

With OPENAI_API_KEY set the example calls OpenAI; without a key a scripted client answers and the example says so.
"""

import sys
from pathlib import Path

from skye import AssistantMessage, CapabilityMessage, SystemMessage, UserMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


def completion(client) -> None:
    messages = [SystemMessage(content="You are a helpful AI assistant."), UserMessage(content="What is the capital of France?")]
    response = client.complete(messages=messages, model="gpt-4", temperature=0.7, max_tokens=100)
    print(f"provider={response.provider} finish={response.finish_reason} tokens={response.usage.total_tokens}")
    print("answer:", response.content)


def conversation(client) -> None:
    history = [UserMessage(content="My name is Ana."), AssistantMessage(content="Nice to meet you, Ana."),
               UserMessage(content="What is my name?")]
    print("turn 3:", client.complete(messages=history, model="gpt-4").content)


def message_types() -> None:
    user = UserMessage(content="What's the weather like?", metadata={"user_id": "user_123", "session_id": "session_456"})
    print("metadata:", user.metadata, "| id:", user.id)

    assistant = AssistantMessage(
        content="Let me check the weather for you.",
        capability_calls=[{"id": "call_123", "name": "get_weather", "arguments": {"location": "San Francisco"}}],
    )
    result = CapabilityMessage(content='{"temperature": 72}', capability_id="call_123", capability_name="get_weather")
    print("assistant asks for:", assistant.capability_calls[0]["name"], "| result:", result.content)


def main() -> None:
    client = get_client("openai")
    completion(client)
    conversation(client)
    message_types()


if __name__ == "__main__":
    main()
