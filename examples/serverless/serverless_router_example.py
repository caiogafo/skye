"""A router whose state survives between invocations of a serverless function.

A router tracks the health, the cooldown and the rate-limit usage of each model. In a long-lived process that state lives in memory; in a
function that is frozen or replaced between invocations it has to live in a store. The store is one argument: ``ModelRouter(storage=...)``.
This example uses the in-memory default and the file backend (two routers sharing one directory). Redis, DynamoDB, PostgreSQL and the AWS
Durable Function backend are used the same way: see ``docs/store/index.md``.
"""

import os
import sys
import tempfile
from pathlib import Path

from skye import UserMessage
from skye.router import ModelRouter
from skye.store import FileSystemBackend

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import router_provider  # noqa: E402


def handler(provider: str, storage=None) -> str:
    """What a function does on each invocation: build the router (cheap), answer, return."""
    router = ModelRouter({"chat": [f"{provider}/gpt-4o-mini"]}, storage=storage)
    print("  storage:", type(router.storage_backend).__name__)
    return router.complete(messages=[UserMessage(content="Hello!")], model="chat").content


def main() -> None:
    provider = router_provider("openai")
    print("mode:", "openai (real)" if os.getenv("OPENAI_API_KEY") else "scripted (set OPENAI_API_KEY to call openai)")

    print("default (memory):")
    print("  ", handler(provider))

    with tempfile.TemporaryDirectory() as directory:
        print("file backend, first invocation:")
        print("  ", handler(provider, FileSystemBackend(base_path=directory)))
        print("file backend, second invocation sees the same directory:")
        print("  ", handler(provider, FileSystemBackend(base_path=directory)))
        print("files written:", sorted(p.name for p in Path(directory).iterdir())[:3])


if __name__ == "__main__":
    main()
