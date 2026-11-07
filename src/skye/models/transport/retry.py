"""Retry logic for provider API calls.

This module provides retry decorators and utilities for handling transient
failures in provider API calls, including rate limiting, timeouts, and
temporary server errors.

The retry is written in the standard library (no third-party dependency).

Features:
- Exponential backoff with optional jitter
- Configurable max retries
- Provider-specific error detection
- Retry-after header support
- Structured logging of retry attempts
"""

import asyncio
import functools
import inspect
import logging
import random
import time
from typing import Any, Callable, TypeVar

from skye.base.exceptions import ProviderError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def _wait_seconds(attempt: int, multiplier: float, min_wait: float, max_wait: float, jitter: float) -> float:
    """Seconds to wait after the failed attempt number ``attempt`` (1-based), clamped to [min_wait, max_wait]."""
    delay: float = multiplier * (2 ** (attempt - 1))
    delay = max(min_wait, min(delay, max_wait))
    if jitter > 0:
        delay += random.uniform(0, jitter)
    return delay


def with_retry(
    max_retries: int = 3,
    min_wait: float = 4,
    max_wait: float = 10,
    multiplier: float = 1,
    jitter: float = 0,
) -> Callable[[F], F]:
    """Decorator for adding retry logic to provider methods.

    Implements exponential backoff (with optional jitter) for transient failures.
    Retries on ProviderError only; any other exception propagates at once. When
    every attempt fails, the last ProviderError is re-raised unchanged. Works on
    plain functions and on coroutine functions (the async wrapper sleeps with
    ``asyncio.sleep``).

    Args:
        max_retries: Maximum number of attempts (default: 3)
        min_wait: Minimum wait time in seconds (default: 4)
        max_wait: Maximum wait time in seconds (default: 10)
        multiplier: Exponential backoff multiplier (default: 1)
        jitter: Upper bound in seconds of a random delay added to each wait (default: 0)

    Returns:
        Decorated function with retry logic

    Example:
        >>> @with_retry(max_retries=3)
        ... def call_provider(self, request):
        ...     return self.client.chat.completions.create(**request)
    """

    def decorator(func: F) -> F:
        def exhausted(error: ProviderError) -> None:
            logger.error(
                f"Max retries ({max_retries}) exceeded for {func.__name__}",
                extra={"last_exception": str(error)},
            )

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                attempt = 1
                while True:
                    try:
                        return await func(*args, **kwargs)
                    except ProviderError as error:
                        if attempt >= max_retries:
                            exhausted(error)
                            raise
                        await asyncio.sleep(_wait_seconds(attempt, multiplier, min_wait, max_wait, jitter))
                        attempt += 1

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            while True:
                try:
                    return func(*args, **kwargs)
                except ProviderError as error:
                    if attempt >= max_retries:
                        exhausted(error)
                        raise
                    time.sleep(_wait_seconds(attempt, multiplier, min_wait, max_wait, jitter))
                    attempt += 1

        return wrapper  # type: ignore[return-value]

    return decorator
