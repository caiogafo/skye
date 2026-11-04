"""Async and streaming usage of a client created with ``skye.provider``.

- ``acomplete`` is the async form of ``complete``.
- ``stream`` yields chunks as the model writes them; each chunk has a ``delta``.

Set OPENAI_API_KEY.
"""

import asyncio
import os

import skye
from skye import UserMessage


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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    client = skye.provider("openai", api_key=api_key)
    asyncio.run(async_completion(client))
    streaming(client)


if __name__ == "__main__":
    main()
