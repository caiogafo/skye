"""Async and streaming usage of a client created with ``skye.provider``.

- ``acomplete`` is the async form of ``complete``.
- ``stream`` yields chunks as the model writes them; each chunk has a ``delta``.

With OPENAI_API_KEY set the example calls OpenAI; without a key it runs a scripted client and says so.
"""

import asyncio

from skye import UserMessage

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


async def async_completion(client) -> None:
    response = await client.acomplete(
        messages=[UserMessage(content="Explain async/await in one sentence")],
        model="gpt-4",
    )
    print("async:", response.content)


def streaming(client) -> None:
    print("stream: ", end="")
    for chunk in client.stream(messages=[UserMessage(content="Write a short story")], model="gpt-4"):
        print(chunk.delta, end="", flush=True)
    print()


def main() -> None:
    client = get_client("openai")
    asyncio.run(async_completion(client))
    streaming(client)


if __name__ == "__main__":
    main()
