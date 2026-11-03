"""Custom exceptions for Skye.

This module defines the exception hierarchy for the Skye GenAI platform.
All Skye-specific exceptions inherit from SkyeError.
"""

import logging
from typing import Any

# Set up module logger
logger = logging.getLogger(__name__)


class SkyeError(Exception):
    """Base exception for all Skye errors.

    All Skye-specific exceptions should inherit from this class.
    This allows users to catch all Skye errors with a single except clause.

    Args:
        message: Human-readable error message
        details: Optional dictionary containing additional error context

    Attributes:
        message: The error message
        details: Dictionary with additional error information
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize SkyeError with message and optional details.

        Args:
            message: Human-readable error message
            details: Optional dictionary containing additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

        # Log the exception when it's created
        logger.error(f"{self.__class__.__name__}: {message}", extra={"details": self.details})

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation of the error."""
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


class ProviderError(SkyeError):
    """Error from an LLM provider.

    Raised when an error occurs during communication with an LLM provider
    (e.g., OpenAI, Anthropic, AWS Bedrock).

    Args:
        message: Human-readable error message
        provider: Name of the provider that raised the error
        status_code: Optional HTTP status code from the provider
        **kwargs: Additional context to include in details
    """

    def __init__(
        self, message: str, provider: str, status_code: int | None = None, **kwargs: Any
    ) -> None:
        """Initialize ProviderError with provider context."""
        details = {"provider": provider, "status_code": status_code, **kwargs}
        super().__init__(message, details)


class ConfigurationError(SkyeError):
    """Error in configuration.

    Raised when there's an issue with configuration values, missing required
    configuration, or invalid configuration format.

    Args:
        message: Human-readable error message
        details: Optional dictionary containing additional error context
    """

    pass


class ValidationError(SkyeError, ValueError):
    """Error in data validation.

    Raised when data fails validation: a field of a model cannot be read as its type or breaks a
    constraint, or an interface compliance check fails. It is also a ``ValueError``, so code that
    catches ``ValueError`` keeps working.

    Args:
        message: Human-readable error message
        field: Name of the field that failed validation
        value: The invalid value that was provided
        **kwargs: Additional context to include in details
    """

    def __init__(self, message: str, field: str, value: Any, **kwargs: Any) -> None:
        """Initialize ValidationError with field information."""
        details = {"field": field, "value": value, **kwargs}
        super().__init__(message, details)


class CapabilityExecutionError(SkyeError):
    """Error during capability execution.

    Raised when a capability fails to execute properly.

    Args:
        message: Human-readable error message
        capability_name: Name of the capability that failed
        **kwargs: Additional context to include in details
    """

    def __init__(self, message: str, capability_name: str, **kwargs: Any) -> None:
        """Initialize CapabilityExecutionError with capability context."""
        details = {"capability": capability_name, **kwargs}
        super().__init__(message, details)


class MissingExtraError(SkyeError, ImportError):
    """An optional dependency is absent because its Extra is not installed.

    Wraps the underlying ``ImportError``/``ModuleNotFoundError`` (as
    ``__cause__`` when raised ``from``) and names the missing Extra. It also
    subclasses ``ImportError`` so pre-existing ``except ImportError`` call sites
    keep working.

    Args:
        extra: Name of the Extra that provides the missing module
        missing: Name of the module that could not be imported
        package: Optional pip package name (defaults to ``missing``)
    """

    def __init__(self, extra: str, missing: str, package: str | None = None) -> None:
        """Initialize MissingExtraError with the Extra and module names."""
        pkg = package or missing
        self.extra = extra
        self.missing = missing
        self.package = pkg
        message = (
            f"The '{missing}' package is required but not installed.\n"
            f"Install it with: pip install {pkg}\n"
            f"Or install the skye extra: pip install skyeai[{extra}]"
        )
        SkyeError.__init__(
            self, message, {"extra": extra, "missing": missing, "package": pkg}
        )
        self.name = missing
