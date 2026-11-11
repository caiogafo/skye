"""Every store backend passes the public conformance suite (store tasks 2.1 to 2.3, Requirement 12,
D95, D98).

The external stores run against offline fakes (``fakes.py``); the SQL of PostgreSQL is not executed,
only its parameters are checked.
"""

from __future__ import annotations

import asyncio
import itertools
from pathlib import Path

import pytest

from skye.store import (
    DurableFunctionBackend,
    DynamoDBBackend,
    FileSystemBackend,
    InMemoryBackend,
    PostgreSQLBackend,
    RedisBackend,
)
from skye.store.conformance import FakeClock, check_backend
from tests.unit.store.fakes import FakeDynamoResource, FakeRedis, FakeSqlExecutor


class Context:
    """A durable context: ``get_state`` and ``set_state``."""

    def __init__(self) -> None:
        self.state: dict[str, object] = {}

    def get_state(self, name: str) -> object:
        return self.state.get(name)

    def set_state(self, name: str, value: object) -> None:
        self.state[name] = value


def _makers(tmp_path: Path) -> dict[str, tuple[object, list[str]]]:
    folders = itertools.count()
    return {
        "memory": (lambda clock: InMemoryBackend(clock=clock), ["key_value", "counter", "scan"]),
        "file": (
            lambda clock: FileSystemBackend(str(tmp_path / str(next(folders))), clock=clock),
            ["key_value", "counter", "scan"],
        ),
        "dynamodb": (
            lambda clock: DynamoDBBackend("t", resource=FakeDynamoResource(), clock=clock),
            ["key_value", "counter", "scan"],
        ),
        "redis": (
            lambda clock: RedisBackend(client=FakeRedis(clock)),
            ["key_value", "counter", "scan"],
        ),
        "postgres": (
            lambda clock: PostgreSQLBackend(executor=FakeSqlExecutor(), clock=clock),
            ["key_value", "counter", "scan"],
        ),
        "durable_function": (
            lambda clock: DurableFunctionBackend(Context(), clock=clock),
            ["key_value", "counter"],
        ),
    }


@pytest.mark.parametrize(
    "name", ["memory", "file", "dynamodb", "redis", "postgres", "durable_function"]
)
def test_backend_conforms(name: str, tmp_path: Path) -> None:
    make, expected = _makers(tmp_path)[name]
    assert asyncio.run(check_backend(make)) == expected


def test_the_suite_is_not_blind() -> None:
    """A backend that keeps expired values fails the suite."""

    class Forgetful(InMemoryBackend):
        async def get(self, key: str):  # type: ignore[override]
            entry = self._data.get(key)
            return None if entry is None else dict(entry[0])

    with pytest.raises(AssertionError, match="expired"):
        asyncio.run(check_backend(lambda clock: Forgetful(clock=clock)))


def test_fake_clock_moves_only_when_told() -> None:
    clock = FakeClock(10)
    assert clock() == 10
    clock.advance(5)
    assert clock() == 15
