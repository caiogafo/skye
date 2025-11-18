"""Custom exceptions for Nimbus.

This module defines the exception hierarchy for the Nimbus GenAI platform.
All Nimbus-specific exceptions inherit from NimbusError.
"""

import logging
from typing import Any, Optional

# Set up module logger
logger = logging.getLogger(__name__)


class NimbusError(Exception):
    """Base exception for all Nimbus errors.
    
    All Nimbus-specific exceptions should inherit from this class.
    This allows users to catch all Nimbus errors with a single except clause.
    
    Args:
        message: Human-readable error message
        details: Optional dictionary containing additional error context
    
    Attributes:
        message: The error message
        details: Dictionary with additional error information
    """
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """Initialize NimbusError with message and optional details.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary containing additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
        
        # Log the exception when it's created
        logger.error(
            f"{self.__class__.__name__}: {message}",
            extra={"details": self.details}
        )
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message
    
    def __repr__(self) -> str:
        """Return detailed representation of the error."""
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


class ProviderError(NimbusError):
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
        self,
        message: str,
        provider: str,
        status_code: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        """Initialize ProviderError with provider context."""
        details = {
            "provider": provider,
            "status_code": status_code,
            **kwargs
        }
        super().__init__(message, details)


class ConfigurationError(NimbusError):
    """Error in configuration.
    
    Raised when there's an issue with configuration values, missing required
    configuration, or invalid configuration format.
    
    Args:
        message: Human-readable error message
        details: Optional dictionary containing additional error context
    """
    
    pass


class ValidationError(NimbusError):
    """Error in data validation.
    
    Raised when data fails validation, typically when Pydantic model
    validation fails or when interface compliance checks fail.
    
    Args:
        message: Human-readable error message
        field: Name of the field that failed validation
        value: The invalid value that was provided
        **kwargs: Additional context to include in details
    """
    
    def __init__(
        self,
        message: str,
        field: str,
        value: Any,
        **kwargs: Any
    ) -> None:
        """Initialize ValidationError with field information."""
        details = {
            "field": field,
            "value": value,
            **kwargs
        }
        super().__init__(message, details)


class CapabilityExecutionError(NimbusError):
    """Error during capability execution.
    
    Raised when a capability (tool/function) fails to execute properly.
    
    Args:
        message: Human-readable error message
        capability_name: Name of the capability that failed
        **kwargs: Additional context to include in details
    """
    
    def __init__(
        self,
        message: str,
        capability_name: str,
        **kwargs: Any
    ) -> None:
        """Initialize CapabilityExecutionError with capability context."""
        details = {
            "capability": capability_name,
            **kwargs
        }
        super().__init__(message, details)
