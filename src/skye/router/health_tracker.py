"""Health and rate limit tracking for model router.

This module contains classes for tracking model health, rate limits, and performance metrics. All
state is stored via the storage backend. Storage backend is initialized by the ModelRouter.
"""

import time
from dataclasses import dataclass, field
from typing import Any

from skye.base.interfaces import StorageBackend
from skye.store.memory import InMemoryBackend

#: The window of the allowed-fails policy: only the failures of the last minute count.
RECENT_FAILURES_WINDOW_SECONDS = 60.0
#: How long the health counts live after their last update.
HEALTH_TTL_SECONDS = 86400


@dataclass
class RateLimitTracker:
    """Track rate limits for a model deployment.

    All state is stored via the storage backend for consistency across both traditional and
    serverless environments.
    """

    tpm_limit: int | None = None  # Tokens per minute
    rpm_limit: int | None = None  # Requests per minute
    model_id: str = ""
    storage: StorageBackend = field(default_factory=InMemoryBackend)
    window_seconds: int = 60  # Rate limit window

    def _get_window_key(self, metric_type: str) -> str:
        """Get storage key for current time window."""
        current_window = int(time.time()) // self.window_seconds
        return f"rate_limit:{self.model_id}:{metric_type}:{current_window}"

    def _get_active_requests_key(self) -> str:
        """Get storage key for active requests counter."""
        return f"active_requests:{self.model_id}"

    async def can_accept_request(self, estimated_tokens: int = 0) -> bool:
        """Check if request can be accepted within rate limits."""
        # Check RPM limit
        if self.rpm_limit:
            rpm_key = self._get_window_key("rpm")
            rpm_data = await self.storage.get(rpm_key)
            current_rpm = rpm_data.get("count", 0) if rpm_data else 0
            if current_rpm >= self.rpm_limit:
                return False

        # Check TPM limit
        if self.tpm_limit and estimated_tokens > 0:
            tpm_key = self._get_window_key("tpm")
            tpm_data = await self.storage.get(tpm_key)
            current_tpm = tpm_data.get("count", 0) if tpm_data else 0
            if current_tpm + estimated_tokens > self.tpm_limit:
                return False

        return True

    async def record_request(self, tokens_used: int) -> None:
        """Record a completed request."""
        # Update both RPM and TPM counters atomically
        rpm_key = self._get_window_key("rpm")
        await self.storage.increment(rpm_key, 1, ttl=self.window_seconds * 2)

        if tokens_used > 0:
            tpm_key = self._get_window_key("tpm")
            await self.storage.increment(tpm_key, tokens_used, ttl=self.window_seconds * 2)

    async def increment_active_requests(self) -> int:
        """Increment active requests counter."""
        active_key = self._get_active_requests_key()
        return await self.storage.increment(active_key, 1, ttl=3600)  # 1 hour TTL

    async def decrement_active_requests(self) -> int:
        """Decrement active requests counter."""
        active_key = self._get_active_requests_key()
        return await self.storage.increment(active_key, -1, ttl=3600)  # 1 hour TTL

    async def get_current_usage(self) -> dict[str, Any]:
        """Get current usage statistics."""
        rpm_key = self._get_window_key("rpm")
        tpm_key = self._get_window_key("tpm")
        active_key = self._get_active_requests_key()

        data = await self.storage.get_multiple([rpm_key, tpm_key, active_key])

        return {
            "rpm_used": (data.get(rpm_key) or {}).get("count", 0),
            "tpm_used": (data.get(tpm_key) or {}).get("count", 0),
            "rpm_limit": self.rpm_limit,
            "tpm_limit": self.tpm_limit,
            "active_requests": (data.get(active_key) or {}).get("count", 0),
        }


@dataclass
class ModelHealth:
    """Health tracking for a model deployment.

    All state is stored via the storage backend for consistency across both traditional and
    serverless environments. Every count is an atomic ``increment`` of the store (``CounterStore``),
    so two processes that record at the same time lose no count; only the latest times and the
    lowest and highest latency are plain values (the last writer wins).

    Keys (``<id>`` is the model id; health keys live 24 hours from the last update):

    - ``health:<id>:success``, ``health:<id>:failure``: the counts;
    - ``health:<id>:latency_us``: the total latency of the successes, in microseconds;
    - ``health:<id>:reason:<error type>``: the failures of one error type, and
      ``health:<id>:reasons`` the names seen;
    - ``health:<id>:last``: the time of the last success and of the last failure, and the lowest and
      highest latency;
    - ``recent_failures:<id>:<error type>:<second>``: the failures of one second, for the
      allowed-fails window;
    - ``cooldown:<id>``: the end of the cooldown.
    """

    model_id: str
    storage: StorageBackend = field(default_factory=InMemoryBackend)
    tags: list[str] = field(default_factory=list)

    def _key(self, name: str) -> str:
        return f"health:{self.model_id}:{name}"

    def _get_cooldown_key(self) -> str:
        """Get storage key for cooldown data."""
        return f"cooldown:{self.model_id}"

    def _recent_key(self, reason: str, second: int) -> str:
        """The key of the failures of one error type in one second."""
        return f"recent_failures:{self.model_id}:{reason}:{second}"

    async def _merge_last(self, **values: float) -> None:
        """Write the latest times and the latency range (a lost update loses a time, never a count)."""
        key = self._key("last")
        data = await self.storage.get(key) or {}
        for name, value in values.items():
            if name == "min_latency_ms":
                value = min(data.get(name, value), value)
            elif name == "max_latency_ms":
                value = max(data.get(name, value), value)
            data[name] = value
        await self.storage.set(key, data, ttl=HEALTH_TTL_SECONDS)

    async def record_success(self, latency_ms: float) -> None:
        """Record a successful request."""
        await self.storage.increment(self._key("success"), 1, ttl=HEALTH_TTL_SECONDS)
        await self.storage.increment(
            self._key("latency_us"), max(0, round(latency_ms * 1000)), ttl=HEALTH_TTL_SECONDS
        )
        await self._merge_last(
            last_success_time=time.time(), min_latency_ms=latency_ms, max_latency_ms=latency_ms
        )

    async def record_failure(
        self, reason: str = "unknown", window_reason: str | None = None
    ) -> None:
        """Record a failed request.

        Args:
            reason: The error type, counted in ``failure_reasons``.
            window_reason: The name the allowed-fails window counts this failure under (the policy
                entry that matched the error); ``reason`` when not given.
        """
        current_time = time.time()
        await self.storage.increment(self._key("failure"), 1, ttl=HEALTH_TTL_SECONDS)
        await self.storage.increment(self._key(f"reason:{reason}"), 1, ttl=HEALTH_TTL_SECONDS)
        reasons_key = self._key("reasons")
        known = await self.storage.get(reasons_key) or {}
        names = list(known.get("names", []))
        if reason not in names:
            # Add-only: a name lost to a concurrent write is added again by the next failure of that
            # type.
            await self.storage.set(reasons_key, {"names": [*names, reason]}, ttl=HEALTH_TTL_SECONDS)
        else:
            await self.storage.set(reasons_key, known, ttl=HEALTH_TTL_SECONDS)
        await self._merge_last(last_failure_time=current_time)
        # The allowed-fails policy counts per minute: one counter per second, kept twice the window.
        await self.storage.increment(
            self._recent_key(window_reason or reason, int(current_time)),
            1,
            ttl=int(RECENT_FAILURES_WINDOW_SECONDS) * 2,
        )

    async def recent_failure_count(
        self, reason: str, window_seconds: float = RECENT_FAILURES_WINDOW_SECONDS
    ) -> int:
        """The number of failures of this error type in the last ``window_seconds`` (whole seconds).

        Only the failures of the recorded window (``RECENT_FAILURES_WINDOW_SECONDS``) are kept.
        """
        now = time.time()
        newest = int(now)
        oldest = int(now - min(window_seconds, RECENT_FAILURES_WINDOW_SECONDS)) + 1
        keys = [self._recent_key(reason, second) for second in range(oldest, newest + 1)]
        data = await self.storage.get_multiple(keys)
        return sum(int((value or {}).get("count", 0)) for value in data.values())

    async def set_cooldown(self, duration_seconds: float) -> None:
        """Set cooldown period."""
        cooldown_key = self._get_cooldown_key()
        cooldown_until = time.time() + duration_seconds

        await self.storage.set(
            cooldown_key,
            {"cooldown_until": cooldown_until},
            ttl=int(duration_seconds) + 60,  # TTL slightly longer than cooldown
        )

    async def is_in_cooldown(self) -> bool:
        """Check if model is in cooldown."""
        cooldown_data = await self.storage.get(self._get_cooldown_key())
        if not cooldown_data:
            return False
        cooldown_until = cooldown_data.get("cooldown_until", 0)
        return bool(time.time() < cooldown_until)

    async def _counts(self) -> tuple[int, int, float]:
        """The success count, the failure count and the total latency in milliseconds."""
        data = await self.storage.get_multiple(
            [self._key("success"), self._key("failure"), self._key("latency_us")]
        )
        success, failure, latency_us = (int((data[k] or {}).get("count", 0)) for k in data)
        return success, failure, latency_us / 1000.0

    async def get_success_rate(self) -> float:
        """Get success rate from storage."""
        success_count, failure_count, _ = await self._counts()
        total = success_count + failure_count
        if total == 0:
            return 1.0
        return success_count / total

    async def get_avg_latency_ms(self) -> float:
        """Get average latency from storage."""
        success_count, _, total_latency_ms = await self._counts()
        if success_count == 0:
            return float("inf")
        return total_latency_ms / success_count

    async def get_health_metrics(self) -> dict[str, Any]:
        """Get comprehensive health metrics."""
        success_count, failure_count, total_latency_ms = await self._counts()
        data = await self.storage.get_multiple(
            [self._key("last"), self._key("reasons"), self._get_cooldown_key()]
        )
        last = data[self._key("last")] or {}
        cooldown_data = data[self._get_cooldown_key()] or {}
        names = list((data[self._key("reasons")] or {}).get("names", []))
        reason_counts = await self.storage.get_multiple([self._key(f"reason:{n}") for n in names])
        failure_reasons = {
            name: int((reason_counts[self._key(f"reason:{name}")] or {}).get("count", 0))
            for name in names
        }
        total_requests = success_count + failure_count

        return {
            "model_id": self.model_id,
            "success_count": success_count,
            "failure_count": failure_count,
            "total_requests": total_requests,
            "success_rate": success_count / total_requests if total_requests > 0 else 1.0,
            "average_latency_ms": total_latency_ms / success_count if success_count > 0 else 0.0,
            "min_latency_ms": last.get("min_latency_ms"),
            "max_latency_ms": last.get("max_latency_ms"),
            "last_success_time": last.get("last_success_time"),
            "last_failure_time": last.get("last_failure_time"),
            "is_in_cooldown": cooldown_data.get("cooldown_until", 0) > time.time(),
            "cooldown_until": cooldown_data.get("cooldown_until"),
            "failure_reasons": {name: count for name, count in failure_reasons.items() if count},
            "tags": self.tags,
        }
