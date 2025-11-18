"""Provider-specific error handling and wrapping.

This module provides utilities for catching provider-specific errors and
wrapping them in ProviderError with appropriate context information.

Features:
- Provider-specific error detection
- Retry-after header extraction
- Status code preservation
- Error type classification
- Structured error context
"""

import logging
from typing import Any, Callable, TypeVar

from nimbus.exceptions import ProviderError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class ErrorHandler:
    """Handle provider-specific errors and wrap them in ProviderError."""

    @staticmethod
    def handle_openai_error(error: Exception, provider: str = "openai") -> ProviderError:
        """Handle OpenAI-specific errors.

        Args:
            error: The OpenAI error to handle
            provider: Provider name for context

        Returns:
            ProviderError with appropriate context
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Extract retry_after if available
        retry_after = None
        status_code = None

        if hasattr(error, "retry_after"):
            retry_after = error.retry_after

        if hasattr(error, "status_code"):
            status_code = error.status_code

        # Classify error type - check both error type name and message
        error_type_lower = error_type.lower()
        error_message_lower = error_message.lower()
        
        if "ratelimit" in error_type_lower or "rate_limit" in error_type_lower or "rate_limit" in error_message_lower:
            error_classification = "rate_limit"
        elif "timeout" in error_type_lower or "timeout" in error_message_lower:
            error_classification = "timeout"
        elif "connection" in error_type_lower or "connection" in error_message_lower:
            error_classification = "connection_error"
        elif "auth" in error_type_lower or "unauthorized" in error_message_lower:
            error_classification = "authentication_error"
        elif "api" in error_type_lower:
            error_classification = "api_error"
        else:
            error_classification = "unknown_error"

        return ProviderError(
            f"OpenAI API error: {error_message}",
            provider=provider,
            status_code=status_code,
            error_type=error_classification,
            retry_after=retry_after,
            original_error_type=error_type,
        )

    @staticmethod
    def handle_anthropic_error(error: Exception, provider: str = "anthropic") -> ProviderError:
        """Handle Anthropic-specific errors.

        Args:
            error: The Anthropic error to handle
            provider: Provider name for context

        Returns:
            ProviderError with appropriate context
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Extract status code if available
        status_code = None
        if hasattr(error, "status_code"):
            status_code = error.status_code

        # Classify error type - check both error type name and message
        error_type_lower = error_type.lower()
        error_message_lower = error_message.lower()
        
        if "ratelimit" in error_type_lower or "rate_limit" in error_type_lower or "rate_limit" in error_message_lower:
            error_classification = "rate_limit"
        elif "timeout" in error_type_lower or "timeout" in error_message_lower:
            error_classification = "timeout"
        elif "connection" in error_type_lower or "connection" in error_message_lower:
            error_classification = "connection_error"
        elif "auth" in error_type_lower or "unauthorized" in error_message_lower:
            error_classification = "authentication_error"
        elif "api" in error_type_lower:
            error_classification = "api_error"
        else:
            error_classification = "unknown_error"

        return ProviderError(
            f"Anthropic API error: {error_message}",
            provider=provider,
            status_code=status_code,
            error_type=error_classification,
            original_error_type=error_type,
        )

    @staticmethod
    def handle_bedrock_error(error: Exception, provider: str = "bedrock") -> ProviderError:
        """Handle AWS Bedrock-specific errors.

        Args:
            error: The Bedrock error to handle
            provider: Provider name for context

        Returns:
            ProviderError with appropriate context
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Extract error code if available (boto3 ClientError)
        error_code = None
        status_code = None
        if hasattr(error, "response"):
            response = error.response
            if isinstance(response, dict):
                error_code = response.get("Error", {}).get("Code")
                status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")

        # Classify error type
        error_code_lower = error_code.lower() if error_code else ""
        error_type_lower = error_type.lower()
        error_message_lower = error_message.lower()
        
        if "throttling" in error_code_lower:
            error_classification = "rate_limit"
        elif "ratelimit" in error_type_lower or "rate_limit" in error_type_lower or "rate_limit" in error_message_lower:
            error_classification = "rate_limit"
        elif "timeout" in error_type_lower or "timeout" in error_message_lower:
            error_classification = "timeout"
        elif "connection" in error_type_lower or "connection" in error_message_lower:
            error_classification = "connection_error"
        elif "accessdenied" in error_code_lower or "access_denied" in error_code_lower:
            error_classification = "authentication_error"
        elif "serviceunavailable" in error_code_lower or "service_unavailable" in error_code_lower:
            error_classification = "service_unavailable"
        else:
            error_classification = "unknown_error"

        return ProviderError(
            f"Bedrock API error: {error_message}",
            provider=provider,
            status_code=status_code,
            error_type=error_classification,
            error_code=error_code,
            original_error_type=error_type,
        )

    @staticmethod
    def handle_azure_error(error: Exception, provider: str = "azure") -> ProviderError:
        """Handle Azure OpenAI-specific errors.

        Args:
            error: The Azure error to handle
            provider: Provider name for context

        Returns:
            ProviderError with appropriate context
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Extract status code if available
        status_code = None
        if hasattr(error, "status_code"):
            status_code = error.status_code

        # Classify error type - check both error type name and message
        error_type_lower = error_type.lower()
        error_message_lower = error_message.lower()
        
        if "ratelimit" in error_type_lower or "rate_limit" in error_type_lower or "rate_limit" in error_message_lower:
            error_classification = "rate_limit"
        elif "timeout" in error_type_lower or "timeout" in error_message_lower:
            error_classification = "timeout"
        elif "connection" in error_type_lower or "connection" in error_message_lower:
            error_classification = "connection_error"
        elif "auth" in error_type_lower or "unauthorized" in error_message_lower:
            error_classification = "authentication_error"
        elif "api" in error_type_lower:
            error_classification = "api_error"
        else:
            error_classification = "unknown_error"

        return ProviderError(
            f"Azure OpenAI API error: {error_message}",
            provider=provider,
            status_code=status_code,
            error_type=error_classification,
            original_error_type=error_type,
        )

    @staticmethod
    def handle_vertex_error(error: Exception, provider: str = "vertex") -> ProviderError:
        """Handle Google Vertex AI-specific errors.

        Args:
            error: The Vertex error to handle
            provider: Provider name for context

        Returns:
            ProviderError with appropriate context
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Extract status code if available
        status_code = None
        if hasattr(error, "code"):
            status_code = error.code

        # Classify error type - check both error type name and message
        error_type_lower = error_type.lower()
        error_message_lower = error_message.lower()
        
        if "resourceexhausted" in error_type_lower or "rate_limit" in error_message_lower:
            error_classification = "rate_limit"
        elif "deadlineexceeded" in error_type_lower or "timeout" in error_message_lower:
            error_classification = "timeout"
        elif "unavailable" in error_type_lower or "unavailable" in error_message_lower:
            error_classification = "service_unavailable"
        elif "unauthenticated" in error_type_lower or "auth" in error_message_lower:
            error_classification = "authentication_error"
        elif "permissiondenied" in error_type_lower:
            error_classification = "permission_error"
        else:
            error_classification = "unknown_error"

        return ProviderError(
            f"Vertex AI API error: {error_message}",
            provider=provider,
            status_code=status_code,
            error_type=error_classification,
            original_error_type=error_type,
        )

    @staticmethod
    def wrap_provider_error(
        error: Exception,
        provider: str,
    ) -> ProviderError:
        """Wrap a provider error with appropriate context.

        Routes to provider-specific error handlers based on provider name.

        Args:
            error: The error to wrap
            provider: Provider name (openai, anthropic, bedrock, azure, vertex)

        Returns:
            ProviderError with appropriate context
        """
        # If already a ProviderError, return as-is
        if isinstance(error, ProviderError):
            return error

        # Route to provider-specific handler
        if provider == "openai":
            return ErrorHandler.handle_openai_error(error, provider)
        elif provider == "anthropic":
            return ErrorHandler.handle_anthropic_error(error, provider)
        elif provider == "bedrock":
            return ErrorHandler.handle_bedrock_error(error, provider)
        elif provider == "azure":
            return ErrorHandler.handle_azure_error(error, provider)
        elif provider == "vertex":
            return ErrorHandler.handle_vertex_error(error, provider)
        else:
            # Generic error handling for unknown providers
            return ProviderError(
                f"Provider error: {str(error)}",
                provider=provider,
                error_type="unknown_error",
                original_error_type=type(error).__name__,
            )
