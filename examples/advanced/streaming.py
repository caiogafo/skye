"""Streaming: tokens as the model writes them, with ``stream`` (sync) and ``astream`` (async).

Each chunk has a ``delta`` (the new text) and, on the last one, a ``finish_reason``. This example prints the text as it arrives,
counts the chunks and measures the time to the first token.

With OPENAI_API_KEY set the example calls OpenAI; without a key it runs a scripted client and says so.
"""

import asyncio
import time

from skye import CompleteRequest, UserMessage

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402


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
    request = CompleteRequest(messages=[UserMessage(content="Write a two-line poem")], model="gpt-4", stream=True)
    print("async: ", end="")
    async for chunk in client.astream(request):
        print(chunk.delta, end="", flush=True)
    print()


def main() -> None:
    client = get_client("openai")
    stream_sync(client)
    asyncio.run(stream_async(client))


if __name__ == "__main__":
    main()
