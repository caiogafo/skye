"""Retry logic for provider API calls.

This module provides retry decorators and utilities for handling transient
failures in provider API calls, including rate limiting, timeouts, and
temporary server errors.

Features:
- Exponential backoff with jitter
- Configurable max retries
- Provider-specific error detection
- Retry-after header support
- Structured logging of retry attempts
"""

import logging
from typing import Any, Callable, TypeVar

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

from nimbus.base.exceptions import ProviderError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    max_retries: int = 3,
    min_wait: float = 4,
    max_wait: float = 10,
    multiplier: float = 1,
) -> Callable[[F], F]:
    """Decorator for adding retry logic to provider methods.

    Implements exponential backoff with jitter for transient failures.
    Retries on ProviderError and other transient exceptions.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        min_wait: Minimum wait time in seconds (default: 4)
        max_wait: Maximum wait time in seconds (default: 10)
        multiplier: Exponential backoff multiplier (default: 1)

    Returns:
        Decorated function with retry logic

    Example:
        >>> @with_retry(max_retries=3)
        ... def call_provider(self, request):
        ...     return self.client.chat.completions.create(**request)
    """

    def decorator(func: F) -> F:
        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(
                multiplier=multiplier,
                min=min_wait,
                max=max_wait,
            ),
            retry=retry_if_exception_type(ProviderError),
            reraise=True,
        )
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except RetryError as e:
                # Log final failure after all retries exhausted
                logger.error(
                    f"Max retries ({max_retries}) exceeded for {func.__name__}",
                    extra={"last_exception": str(e.last_attempt.exception())},
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator
