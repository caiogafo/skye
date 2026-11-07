"""Custom exceptions for capability support.

This module defines exceptions specific to capability registration,
validation, and execution.
"""

from typing import Any

from skye.base.exceptions import CapabilityError, CapabilityExecutionError

__all__ = [
    "CapabilityCallParsingError",
    "CapabilityError",
    "CapabilityExecutionError",
    "CapabilityNotFoundError",
    "CapabilityValidationError",
]


class CapabilityNotFoundError(CapabilityError):
    """Raised when a requested capability is not registered.

    Args:
        message: Human-readable error message
        capability_name: Name of the capability that was not found
        **kwargs: Additional context to include in details
    """

    def __init__(self, message: str, capability_name: str, **kwargs: Any) -> None:
        """Initialize CapabilityNotFoundError with capability name."""
        details = {"capability_name": capability_name, **kwargs}
        super().__init__(message, details)


class CapabilityValidationError(CapabilityError):
    """Raised when capability schema validation fails.

    Args:
        message: Human-readable error message
        capability_name: Name of the capability that failed validation
        **kwargs: Additional context to include in details
    """

    def __init__(self, message: str, capability_name: str, **kwargs: Any) -> None:
        """Initialize CapabilityValidationError with capability name."""
        details = {"capability_name": capability_name, **kwargs}
        super().__init__(message, details)


class CapabilityCallParsingError(CapabilityError):
    """Raised when capability call parsing fails.

    Args:
        message: Human-readable error message
        provider: Name of the provider that generated the capability call
        **kwargs: Additional context to include in details
    """

    def __init__(self, message: str, provider: str, **kwargs: Any) -> None:
        """Initialize CapabilityCallParsingError with provider context."""
        details = {"provider": provider, **kwargs}
        super().__init__(message, details)
