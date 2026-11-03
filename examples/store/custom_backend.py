"""Your own durable-state backend behind the StorageBackend Port (Live).

``StorageBackend`` (``skye.base.interfaces.storage``) is the contract every store honours. Subclass
it, implement the abstract async methods, and the rest of Skye can use your backend anywhere a core
one would go. This example backs it with a plain dict to keep the focus on the shape of the Port.
"""

import asyncio
from typing import Any

from skye.base.interfaces import StorageBackend


class DictBackend(StorageBackend):
    """A minimal StorageBackend kept entirely in a dictionary."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    async def connect(self) -> None:
        """No connection to open for an in-process dict."""

    async def get(self, key: str) -> dict[str, Any] | None:
        return self._data.get(key)

    async def set(self, key: str, data: dict[str, Any], ttl: int | None = None) -> None:
        self._data[key] = dict(data)

    async def increment(self, key: str, amount: int = 1, ttl: int | None = None) -> int:
        current = await self.get(key) or {}
        new_value = current.get("count", 0) + amount
        await self.set(key, {"count": new_value}, ttl)
        return new_value

    async def get_multiple(self, keys: list[str]) -> dict[str, dict[str, Any] | None]:
        return {key: await self.get(key) for key in keys}

    async def set_multiple(self, data: dict[str, dict[str, Any]], ttl: int | None = None) -> None:
        for key, value in data.items():
            await self.set(key, value, ttl)


async def main() -> None:
    backend = DictBackend()
    await backend.connect()

    await backend.set_multiple({"user:1": {"name": "Ada"}, "user:2": {"name": "Grace"}})
    print("get(user:1):", await backend.get("user:1"))
    print("increment(hits):", await backend.increment("hits", amount=3))
    print("get_multiple:", await backend.get_multiple(["user:1", "user:2", "missing"]))


if __name__ == "__main__":
    asyncio.run(main())
