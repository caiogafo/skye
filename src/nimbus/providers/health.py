"""Health monitoring for providers.

This module provides health tracking and metrics collection for LLM providers,
including success/failure counters, latency tracking, and error rate calculation.

Example:
    >>> from nimbus.providers.health import HealthMetrics
    >>> metrics = HealthMetrics()
    >>> metrics.record_success(latency_ms=150)
    >>> metrics.record_failure()
    >>> health = metrics.get_health_metrics()
    >>> print(health.success_rate)
    0.5
"""

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HealthMetrics:
    """Health metrics for a provider.
    
    Tracks success/failure counts, latency statistics, and calculates
    health indicators like success rate and error rate.
    
    Attributes:
        success_count: Number of successful requests
        failure_count: Number of failed requests
        total_latency_ms: Total latency across all requests in milliseconds
        min_latency_ms: Minimum latency observed
        max_latency_ms: Maximum latency observed
        last_success_time: Timestamp of last successful request
        last_failure_time: Timestamp of last failed request
    """
    
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    last_success_time: float | None = None
    last_failure_time: float | None = None
    _lock: Any = field(default_factory=lambda: None, init=False, repr=False)
    
    def __post_init__(self) -> None:
        """Initialize thread lock for thread-safe operations."""
        import threading
        self._lock = threading.Lock()
    
    def record_success(self, latency_ms: float) -> None:
        """Record a successful request.
        
        Args:
            latency_ms: Request latency in milliseconds
        """
        with self._lock:
            self.success_count += 1
            self.total_latency_ms += latency_ms
            self.min_latency_ms = min(self.min_latency_ms, latency_ms)
            self.max_latency_ms = max(self.max_latency_ms, latency_ms)
            self.last_success_time = time.time()
    
    def record_failure(self) -> None:
        """Record a failed request."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
    
    def get_total_requests(self) -> int:
        """Get total number of requests.
        
        Returns:
            Total requests (success + failure)
        """
        with self._lock:
            return self.success_count + self.failure_count
    
    def get_success_rate(self) -> float:
        """Get success rate as a percentage (0.0-1.0).
        
        Returns:
            Success rate (0.0 if no requests yet)
        """
        with self._lock:
            total = self.success_count + self.failure_count
            if total == 0:
                return 0.0
            return self.success_count / total
    
    def get_error_rate(self) -> float:
        """Get error rate as a percentage (0.0-1.0).
        
        Returns:
            Error rate (0.0 if no requests yet)
        """
        with self._lock:
            total = self.success_count + self.failure_count
            if total == 0:
                return 0.0
            return self.failure_count / total
    
    def get_average_latency_ms(self) -> float:
        """Get average latency in milliseconds.
        
        Returns:
            Average latency (0.0 if no successful requests)
        """
        with self._lock:
            if self.success_count == 0:
                return 0.0
            return self.total_latency_ms / self.success_count
    
    def get_health_metrics(self) -> dict[str, Any]:
        """Get comprehensive health metrics.
        
        Returns:
            Dictionary containing all health metrics
            
        Example:
            >>> metrics = HealthMetrics()
            >>> metrics.record_success(latency_ms=100)
            >>> metrics.record_success(latency_ms=200)
            >>> metrics.record_failure()
            >>> health = metrics.get_health_metrics()
            >>> health['success_rate']
            0.6666...
            >>> health['average_latency_ms']
            150.0
        """
        with self._lock:
            total = self.success_count + self.failure_count
            
            # Calculate rates and averages inline to avoid nested lock acquisition
            success_rate = self.success_count / total if total > 0 else 0.0
            error_rate = self.failure_count / total if total > 0 else 0.0
            average_latency = self.total_latency_ms / self.success_count if self.success_count > 0 else 0.0
            
            return {
                'success_count': self.success_count,
                'failure_count': self.failure_count,
                'total_requests': total,
                'success_rate': success_rate,
                'error_rate': error_rate,
                'average_latency_ms': average_latency,
                'min_latency_ms': self.min_latency_ms if self.min_latency_ms != float('inf') else None,
                'max_latency_ms': self.max_latency_ms if self.max_latency_ms > 0 else None,
                'last_success_time': self.last_success_time,
                'last_failure_time': self.last_failure_time,
            }
    
    def reset(self) -> None:
        """Reset all metrics to initial state."""
        with self._lock:
            self.success_count = 0
            self.failure_count = 0
            self.total_latency_ms = 0.0
            self.min_latency_ms = float('inf')
            self.max_latency_ms = 0.0
            self.last_success_time = None
            self.last_failure_time = None
