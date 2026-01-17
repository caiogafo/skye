"""Health and rate limit tracking for model router.

This module contains classes for tracking model health, rate limits,
and performance metrics. All state is stored via the storage backend.
Storage backend is initialized by the ModelRouter.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .storage_backends import StorageBackend, InMemoryBackend


@dataclass
class RateLimitTracker:
    """Track rate limits for a model deployment.
    
    All state is stored via the storage backend for consistency across
    both traditional and serverless environments.
    """

    tpm_limit: Optional[int] = None  # Tokens per minute
    rpm_limit: Optional[int] = None  # Requests per minute
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
            current_rpm = rpm_data.get('count', 0) if rpm_data else 0
            if current_rpm >= self.rpm_limit:
                return False
        
        # Check TPM limit
        if self.tpm_limit and estimated_tokens > 0:
            tpm_key = self._get_window_key("tpm")
            tpm_data = await self.storage.get(tpm_key)
            current_tpm = tmp_data.get('count', 0) if tmp_data else 0
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

    async def get_current_usage(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        rpm_key = self._get_window_key("rpm")
        tpm_key = self._get_window_key("tpm")
        active_key = self._get_active_requests_key()
        
        data = await self.storage.get_multiple([rpm_key, tpm_key, active_key])
        
        return {
            'rpm_used': data.get(rpm_key, {}).get('count', 0) if data.get(rpm_key) else 0,
            'tpm_used': data.get(tpm_key, {}).get('count', 0) if data.get(tpm_key) else 0,
            'rpm_limit': self.rpm_limit,
            'tpm_limit': self.tpm_limit,
            'active_requests': data.get(active_key, {}).get('count', 0) if data.get(active_key) else 0,
        }


@dataclass
class ModelHealth:
    """Health tracking for a model deployment.
    
    All state is stored via the storage backend for consistency across
    both traditional and serverless environments.
    """

    model_id: str
    storage: StorageBackend = field(default_factory=InMemoryBackend)
    tags: List[str] = field(default_factory=list)

    def _get_health_key(self) -> str:
        """Get storage key for health data."""
        return f"health:{self.model_id}"
    
    def _get_cooldown_key(self) -> str:
        """Get storage key for cooldown data."""
        return f"cooldown:{self.model_id}"

    async def record_success(self, latency_ms: float) -> None:
        """Record a successful request."""
        health_key = self._get_health_key()
        current_time = time.time()
        
        # Get current health data
        health_data = await self.storage.get(health_key) or {}
        
        # Update metrics
        health_data.update({
            'success_count': health_data.get('success_count', 0) + 1,
            'total_latency_ms': health_data.get('total_latency_ms', 0.0) + latency_ms,
            'min_latency_ms': min(health_data.get('min_latency_ms', float('inf')), latency_ms),
            'max_latency_ms': max(health_data.get('max_latency_ms', 0.0), latency_ms),
            'last_success_time': current_time,
        })
        
        # Store with 24 hour TTL
        await self.storage.set(health_key, health_data, ttl=86400)

    async def record_failure(self, reason: str = "unknown") -> None:
        """Record a failed request."""
        health_key = self._get_health_key()
        current_time = time.time()
        
        # Get current health data
        health_data = await self.storage.get(health_key) or {}
        failure_reasons = health_data.get('failure_reasons', {})
        
        # Update metrics
        health_data.update({
            'failure_count': health_data.get('failure_count', 0) + 1,
            'last_failure_time': current_time,
            'failure_reasons': {**failure_reasons, reason: failure_reasons.get(reason, 0) + 1}
        })
        
        # Store with 24 hour TTL
        await self.storage.set(health_key, health_data, ttl=86400)

    async def set_cooldown(self, duration_seconds: float) -> None:
        """Set cooldown period."""
        cooldown_key = self._get_cooldown_key()
        cooldown_until = time.time() + duration_seconds
        
        await self.storage.set(
            cooldown_key, 
            {'cooldown_until': cooldown_until}, 
            ttl=int(duration_seconds) + 60  # TTL slightly longer than cooldown
        )

    async def is_in_cooldown(self) -> bool:
        """Check if model is in cooldown."""
        cooldown_key = self._get_cooldown_key()
        cooldown_data = await self.storage.get(cooldown_key)
        
        if not cooldown_data:
            return False
        
        cooldown_until = cooldown_data.get('cooldown_until', 0)
        return time.time() < cooldown_until

    async def get_success_rate(self) -> float:
        """Get success rate from storage."""
        health_data = await self.storage.get(self._get_health_key()) or {}
        success_count = health_data.get('success_count', 0)
        failure_count = health_data.get('failure_count', 0)
        total = success_count + failure_count
        if total == 0:
            return 1.0
        return success_count / total

    async def get_avg_latency_ms(self) -> float:
        """Get average latency from storage."""
        health_data = await self.storage.get(self._get_health_key()) or {}
        success_count = health_data.get('success_count', 0)
        total_latency_ms = health_data.get('total_latency_ms', 0.0)
        if success_count == 0:
            return float("inf")
        return total_latency_ms / success_count

    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics."""
        health_key = self._get_health_key()
        cooldown_key = self._get_cooldown_key()
        
        data = await self.storage.get_multiple([health_key, cooldown_key])
        health_data = data.get(health_key, {})
        cooldown_data = data.get(cooldown_key, {})
        
        success_count = health_data.get('success_count', 0)
        failure_count = health_data.get('failure_count', 0)
        total_requests = success_count + failure_count
        
        return {
            'model_id': self.model_id,
            'success_count': success_count,
            'failure_count': failure_count,
            'total_requests': total_requests,
            'success_rate': success_count / total_requests if total_requests > 0 else 1.0,
            'average_latency_ms': (
                health_data.get('total_latency_ms', 0.0) / success_count 
                if success_count > 0 else 0.0
            ),
            'min_latency_ms': health_data.get('min_latency_ms'),
            'max_latency_ms': health_data.get('max_latency_ms'),
            'last_success_time': health_data.get('last_success_time'),
            'last_failure_time': health_data.get('last_failure_time'),
            'is_in_cooldown': cooldown_data.get('cooldown_until', 0) > time.time(),
            'cooldown_until': cooldown_data.get('cooldown_until'),
            'failure_reasons': health_data.get('failure_reasons', {}),
            'tags': self.tags,
        }