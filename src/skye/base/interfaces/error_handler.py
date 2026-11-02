"""Error handler interface for provider-specific error handling.

This module defines the abstract interface for handling and transforming
provider-specific errors into Skye exceptions.
"""

from abc import ABC, abstractmethod
from typing import Any

from skye.base.exceptions import SkyeError


class ErrorHandlerInterface(ABC):
    """Abstract interface for error handling.

    This interface defines the contract for handling provider-specific errors
    and transforming them into appropriate Skye exceptions.

    Example:
        >>> class MyErrorHandler(ErrorHandlerInterface):
        ...     def handle_error(self, error, provider):
        ...         if "rate limit" in str(error).lower():
        ...             return ProviderError("Rate limited", provider=provider)
        ...         return ProviderError(str(error), provider=provider)
        ...
        ...     def is_retryable(self, error):
        ...         return "rate limit" in str(error).lower()
    """

    @abstractmethod
    def handle_error(self, error: Exception, provider: str, **context: Any) -> SkyeError:
        """Handle a provider-specific error and convert to Skye exception.

        Args:
            error: The original provider-specific exception.
            provider: The provider name (e.g., 'openai', 'bedrock').
            **context: Additional context about the error.

        Returns:
            A Skye exception with appropriate error details.

        Example:
            >>> try:
            ...     # Provider call
            ...     pass
            ... except Exception as e:
            ...     skye_error = handler.handle_error(e, "openai")
            ...     raise skye_error
        """
        pass

    @abstractmethod
    def is_retryable(self, error: Exception) -> bool:
        """Determine if an error is retryable.

        Args:
            error: The exception to check.

        Returns:
            True if the error should trigger a retry, False otherwise.

        Example:
            >>> if handler.is_retryable(error):
            ...     # Retry the request
            ...     pass
        """
        pass

    @abstractmethod
    def get_retry_after(self, error: Exception) -> float | None:
        """Extract retry-after duration from error if available.

        Args:
            error: The exception to extract retry-after from.

        Returns:
            Number of seconds to wait before retrying, or None if not specified.

        Example:
            >>> retry_after = handler.get_retry_after(error)
            >>> if retry_after:
            ...     time.sleep(retry_after)
        """
        pass

    @abstractmethod
    def classify_error(self, error: Exception) -> str:
        """Classify the error type for metrics and routing decisions.

        Args:
            error: The exception to classify.

        Returns:
            Error classification string (e.g., 'rate_limit', 'timeout',
            'authentication', 'server_error', 'client_error').

        Example:
            >>> error_type = handler.classify_error(error)
            >>> if error_type == "rate_limit":
            ...     # Handle rate limiting
            ...     pass
        """
        pass
