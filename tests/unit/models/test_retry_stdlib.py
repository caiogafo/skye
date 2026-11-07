"""The standard-library retry: attempts, backoff, sync and async, exception behaviour."""

import asyncio

import pytest

from skye.base.exceptions import ProviderError
from skye.models.transport import retry
from skye.models.transport.retry import with_retry


@pytest.fixture
def sleeps(monkeypatch):
    waited: list[float] = []
    monkeypatch.setattr(retry.time, "sleep", waited.append)

    async def fake_sleep(seconds):
        waited.append(seconds)

    monkeypatch.setattr(retry.asyncio, "sleep", fake_sleep)
    return waited


def test_backoff_doubles_and_is_clamped(sleeps):
    calls = []

    @with_retry(max_retries=5, min_wait=1, max_wait=5, multiplier=1)
    def fail():
        calls.append(1)
        raise ProviderError("x", provider="p")

    with pytest.raises(ProviderError):
        fail()
    assert len(calls) == 5
    assert sleeps == [1, 2, 4, 5]


def test_other_exceptions_are_not_retried(sleeps):
    calls = []

    @with_retry(max_retries=3)
    def boom():
        calls.append(1)
        raise ValueError("no")

    with pytest.raises(ValueError):
        boom()
    assert calls == [1] and sleeps == []


def test_jitter_adds_a_bounded_delay(sleeps):
    @with_retry(max_retries=2, min_wait=1, max_wait=1, jitter=0.5)
    def fail():
        raise ProviderError("x", provider="p")

    with pytest.raises(ProviderError):
        fail()
    assert 1 <= sleeps[0] <= 1.5


def test_async_function_is_retried(sleeps):
    state = {"n": 0}

    @with_retry(max_retries=3, min_wait=1, max_wait=2)
    async def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise ProviderError("x", provider="p")
        return "ok"

    assert asyncio.run(flaky()) == "ok"
    assert state["n"] == 3 and sleeps == [1, 2]
