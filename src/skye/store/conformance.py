"""The public conformance suite of the storage Ports (Requirement 12.6, decision D98).

Every promise of ``KeyValueStore``, ``CounterStore`` and ``ScanStore`` written once, as code anyone
can run against a backend, Skye's
or their own. ``check_backend`` takes a function that builds a fresh, empty backend from a clock and
runs every check that the backend's
capabilities allow; it raises ``AssertionError`` naming the first broken promise. The clock is a
``FakeClock``, so expiry is checked
without sleeping; a backend that keeps time on its server (Redis) passes the clock to its fake
client instead.

Example:
    >>> import asyncio
    >>> from skye.store import InMemoryBackend
    >>> from skye.store import check_backend
    >>> asyncio.run(check_backend(lambda clock: InMemoryBackend(clock=clock)))
    ['key_value', 'counter', 'scan']

In a test of your own backend::

    def test_my_backend_conforms():
        asyncio.run(check_backend(lambda clock: MyBackend(clock=clock)))

Raises: ``AssertionError`` naming the broken promise.
Missing: not applicable.
Concurrency: the counter check runs 50 concurrent increments and expects no lost update.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from skye.base.exceptions import ValidationError
from skye.base.interfaces.storage import CounterStore, KeyValueStore, ScanStore


class FakeClock:
    """A clock that moves only when told to; call it to read the time."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        """Start at ``start`` seconds since the epoch."""
        self.now = start

    def __call__(self) -> float:
        """The current fake time."""
        return self.now

    def advance(self, seconds: float) -> None:
        """Move the time forward."""
        self.now += seconds


Make = Callable[[FakeClock], Any]


def _require(store: Any, port: type, message: str) -> None:
    if not isinstance(store, port):
        raise AssertionError(message)


async def _rejects(call: Callable[[], Awaitable[Any]], what: str) -> None:
    try:
        await call()
    except ValidationError:
        return
    raise AssertionError(f"{what} must raise ValidationError")


async def check_key_value(make: Make) -> None:
    """``get``, ``set``, ``delete``, ``get_multiple``, ``set_multiple`` and expiry (D95)."""
    clock = FakeClock()
    store: Any = make(clock)
    _require(store, KeyValueStore, "the backend must implement KeyValueStore")
    assert await store.get("absent") is None, "an absent key reads as None"
    await store.set("a", {"x": 1, "nested": {"y": [1, 2]}, "f": 1.5, "s": "text"})
    assert await store.get("a") == {
        "x": 1,
        "nested": {"y": [1, 2]},
        "f": 1.5,
        "s": "text",
    }, "set then get returns the value"
    await store.set("a", {"x": 2})
    assert await store.get("a") == {"x": 2}, "set replaces the whole value"

    await store.set("short", {"v": 1}, ttl=10)
    clock.advance(9)
    assert await store.get("short") == {"v": 1}, "a value is live before its ttl"
    clock.advance(2)
    assert await store.get("short") is None, "an expired value reads as None"
    await store.set("forever", {"v": 1}, ttl=None)
    clock.advance(10**6)
    assert await store.get("forever") == {"v": 1}, "ttl=None never expires"

    for bad in (0, -1, 1.5, True, "10"):

        def write(ttl: Any = bad) -> Awaitable[None]:
            result: Awaitable[None] = store.set("bad", {"v": 1}, ttl=ttl)
            return result

        await _rejects(write, f"set with ttl={bad!r}")
    assert await store.get("bad") is None, "a rejected set writes nothing"
    await _rejects(lambda: store.set("", {"v": 1}), "an empty key")
    await _rejects(lambda: store.set("bad", ["not", "a", "dict"]), "a value that is not a dict")

    assert await store.delete("a") is True, "delete of a live key returns True"
    assert await store.get("a") is None, "a deleted key reads as None"
    assert await store.delete("a") is False, "delete of an absent key returns False"

    await store.set_multiple({"m1": {"i": 1}, "m2": {"i": 2}}, ttl=5)
    got = await store.get_multiple(["m2", "missing", "m1"])
    assert list(got) == ["m2", "missing", "m1"], "get_multiple keeps the order of the keys"
    assert got == {"m2": {"i": 2}, "missing": None, "m1": {"i": 1}}, "get_multiple maps every key"
    clock.advance(6)
    assert await store.get_multiple(["m1", "m2"]) == {
        "m1": None,
        "m2": None,
    }, "set_multiple applies the ttl"
    assert await store.get_multiple([]) == {}, "get_multiple of no keys is empty"
    await _rejects(
        lambda: store.set_multiple({"ok": {"v": 1}, "": {"v": 2}}), "set_multiple with an empty key"
    )
    assert await store.get("ok") is None, "a rejected set_multiple writes nothing"


async def check_counter(make: Make) -> None:
    """``increment``: start at 0, add, expire, and no lost update under concurrent tasks."""
    clock = FakeClock()
    store: Any = make(clock)
    _require(store, CounterStore, "the backend must implement CounterStore")
    assert await store.increment("c") == 1, "an absent counter starts at 0"
    assert await store.increment("c", 4) == 5, "increment adds the amount"
    assert await store.increment("c", -2) == 3, "a negative amount subtracts"
    assert await store.get("c") == {"count": 3}, "a counter reads as {'count': n}"
    await store.set("preset", {"count": 10})
    assert await store.increment("preset") == 11, "increment continues a value set as {'count': n}"
    assert await store.increment("t", ttl=10) == 1
    clock.advance(11)
    assert await store.get("t") is None, "an expired counter reads as None"
    assert await store.increment("t") == 1, "an expired counter starts again"
    await _rejects(lambda: store.increment("t", ttl=0), "increment with ttl=0")
    await asyncio.gather(*(store.increment("busy") for _ in range(50)))
    assert await store.get("busy") == {"count": 50}, "concurrent increments lose no update"


async def check_scan(make: Make) -> None:
    """``keys``: prefix, order, limit, expiry, and keys with special characters."""
    clock = FakeClock()
    store: Any = make(clock)
    _require(store, ScanStore, "the backend must implement ScanStore")
    assert await store.keys("run:") == [], "no keys in an empty store"
    for key in ("run:2", "run:1", "other:1", "run:3"):
        await store.set(key, {"k": key})
    await store.set("run:old", {"k": 1}, ttl=1)
    await store.set("odd/%_*?[x]", {"k": 1})
    assert await store.keys("run:") == [
        "run:1",
        "run:2",
        "run:3",
        "run:old",
    ], "keys returns the matching keys, sorted"
    clock.advance(2)
    assert await store.keys("run:") == ["run:1", "run:2", "run:3"], "keys leaves out expired keys"
    assert await store.keys("run:", limit=2) == ["run:1", "run:2"], "keys honours the limit"
    assert await store.keys("odd/%_*?[") == [
        "odd/%_*?[x]"
    ], "a prefix with %, _, *, ?, [ matches literally"
    assert "other:1" in await store.keys(), "an empty prefix lists every key"


async def check_backend(make: Make) -> list[str]:
    """Run every check the backend's capabilities allow; return the names of the checks that ran."""
    probe = make(FakeClock())
    ran = []
    checks: list[tuple[str, type, Callable[[Make], Awaitable[None]]]] = [
        ("key_value", KeyValueStore, check_key_value),
        ("counter", CounterStore, check_counter),
        ("scan", ScanStore, check_scan),
    ]
    for name, port, check in checks:
        if isinstance(probe, port):
            await check(make)
            ran.append(name)
    if "key_value" not in ran:
        raise AssertionError("every backend must implement KeyValueStore")
    return ran


__all__ = ["FakeClock", "check_backend", "check_counter", "check_key_value", "check_scan"]
