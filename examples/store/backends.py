"""Durable-state backends behind the StorageBackend Port (Live).

Skye keeps all durable state external. ``skye.store`` ships the core backends on the standard
library (``InMemoryBackend``, ``FileSystemBackend``) and optional ones that need a third-party
library (``DynamoDBBackend`` needs boto3, ``RedisBackend`` needs redis, ``PostgreSQLBackend`` needs
asyncpg). The optional backends are constructed inside a guard so the script stays green when the
extra is absent.

Every backend shares the same async API: ``connect``, ``set``, ``get``, ``increment``,
``get_multiple`` (and ``set_multiple``).
"""

import asyncio
import tempfile
from pathlib import Path

from skye import MissingExtraError
from skye.store import (
    DynamoDBBackend,
    FileSystemBackend,
    InMemoryBackend,
    PostgreSQLBackend,
    RedisBackend,
)


async def exercise(backend: object, label: str) -> None:
    """Run the same end-to-end sequence against any StorageBackend."""
    await backend.connect()
    await backend.set("user:1", {"name": "Ada", "role": "admin"})
    print(f"{label} get(user:1):", await backend.get("user:1"))

    await backend.set("hits", {"count": 0})
    print(f"{label} increment(hits):", await backend.increment("hits", amount=2))

    await backend.set("user:2", {"name": "Grace"})
    print(f"{label} get_multiple:", await backend.get_multiple(["user:1", "user:2", "missing"]))


async def main() -> None:
    # 1. In-memory backend: ideal for a single invocation or a test.
    await exercise(InMemoryBackend(), "InMemoryBackend")

    # 2. File-system backend: persistent local storage, cleaned up with tempfile.
    with tempfile.TemporaryDirectory() as tmp:
        await exercise(FileSystemBackend(base_path=str(Path(tmp) / "store")), "FileSystemBackend")

    # 3. Optional backends need an extra; guard their construction so the example stays green when
    #    boto3 / redis / asyncpg are not installed.
    try:
        DynamoDBBackend(table_name="skye-demo", region_name="us-east-1")
        print("DynamoDBBackend constructed (boto3 present)")
    except (ImportError, MissingExtraError):
        print("DynamoDBBackend skipped: boto3 not installed")

    try:
        RedisBackend(redis_url="redis://localhost:6379/0")
        print("RedisBackend constructed (redis present)")
    except (ImportError, MissingExtraError):
        print("RedisBackend skipped: redis not installed")

    try:
        PostgreSQLBackend(connection_string="postgresql://localhost/skye")
        print("PostgreSQLBackend constructed (asyncpg present)")
    except (ImportError, MissingExtraError):
        print("PostgreSQLBackend skipped: asyncpg not installed")


if __name__ == "__main__":
    asyncio.run(main())
