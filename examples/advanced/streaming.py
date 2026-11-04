"""Streaming: tokens as the model writes them, with ``stream`` (sync) and ``astream`` (async).

Each chunk has a ``delta`` (the new text) and, on the last one, a ``finish_reason``. This example prints the text as it arrives,
counts the chunks and measures the time to the first token.

Set OPENAI_API_KEY.
"""

import asyncio
import os
import time

import skye
from skye import CompletionRequest
from skye import UserMessage


def stream_sync(client) -> None:
    started = time.perf_counter()
    first = None
    chunks = 0
    print("sync:  ", end="")
    for chunk in client.stream(messages=[UserMessage(content="Write a two-line poem")], model="gpt-4"):
        if chunk.delta and first is None:
            first = time.perf_counter() - started
        chunks += 1
        print(chunk.delta, end="", flush=True)
    print(f"\n       {chunks} chunk(s), first token after {0 if first is None else first * 1000:.0f} ms")


async def stream_async(client) -> None:
    request = CompletionRequest(messages=[UserMessage(content="Write a two-line poem")], model="gpt-4", stream=True)
    print("async: ", end="")
    async for chunk in client.astream(request):
        print(chunk.delta, end="", flush=True)
    print()


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    client = skye.provider("openai", api_key=api_key)
    stream_sync(client)
    asyncio.run(stream_async(client))


if __name__ == "__main__":
    main()
