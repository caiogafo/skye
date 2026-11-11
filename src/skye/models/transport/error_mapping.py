"""Provider errors to the ``ProviderError`` subclass the failure calls for (decision D104).

An error that is not already a ``ProviderError`` (one from a vendor SDK, a socket, a custom
adapter) is read for its HTTP status, its class name and its message, and becomes the same
subclass the standard-library HTTP layer raises for that response: ``RateLimitError`` (429),
``ServerError`` (5xx), ``ProviderTimeoutError`` (a timeout or a dropped connection),
``AuthenticationError`` (401, 403), ``BadRequestError`` (other 4xx, ``ContentPolicyError`` when
the body names a content policy). A known status code is decided by the rule of
``skye.base.http``, so there is one mapping; the class name and the message decide only when no
status is known. Every result keeps ``status_code``, ``provider``, ``retry_after`` and, in
``details``, an ``error_type`` classification.
"""

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from skye.base.exceptions import (
    AuthenticationError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
    ServerError,
)
from skye.base.http import _is_timeout, _status_class

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

#: The subclass for a classification when no HTTP status is known.
_CLASS_OF_KIND: dict[str, type[ProviderError]] = {
    "rate_limit": RateLimitError,
    "timeout": ProviderTimeoutError,
    "connection_error": ProviderTimeoutError,
    "authentication_error": AuthenticationError,
    "permission_error": AuthenticationError,
    "service_unavailable": ServerError,
}


def error_class(status_code: int | None, kind: str, message: str = "") -> type[ProviderError]:
    """The ``ProviderError`` subclass for an HTTP status (the rule of ``skye.base.http``).

    Without a status, the classification (``rate_limit``, ``timeout``, ...) decides.
    """
    if isinstance(status_code, int) and status_code >= 400:
        return _status_class(status_code, message)
    return _CLASS_OF_KIND.get(kind, ProviderError)


def _classify(error_type: str, message: str) -> str:
    """The classification the OpenAI, Anthropic and Azure clients share (class name and message)."""
    name, text = error_type.lower(), message.lower()
    if "ratelimit" in name or "rate_limit" in name or "rate_limit" in text:
        return "rate_limit"
    if "timeout" in name or "timeout" in text:
        return "timeout"
    if "connection" in name or "connection" in text:
        return "connection_error"
    if "auth" in name or "unauthorized" in text:
        return "authentication_error"
    if "api" in name:
        return "api_error"
    return "unknown_error"


def _build(
    label: str,
    error: Exception,
    provider: str,
    kind: str,
    status_code: int | None = None,
    retry_after: float | None = None,
    **extra: Any,
) -> ProviderError:
    message = str(error)
    cls = error_class(status_code, kind, message)
    if cls is ProviderError and _is_timeout(error):
        cls = ProviderTimeoutError
    return cls(
        f"{label}: {message}",
        provider=provider,
        status_code=status_code,
        retry_after=retry_after,
        error_type=kind,
        original_error_type=type(error).__name__,
        **extra,
    )


class ErrorHandler:
    """Turn provider errors into the ``ProviderError`` subclass of D104."""

    @staticmethod
    def handle_openai_error(error: Exception, provider: str = "openai") -> ProviderError:
        """Handle an OpenAI error.

        Args:
            error: The error to handle
            provider: Provider name for context

        Returns:
            The ``ProviderError`` subclass for the failure
        """
        kind = _classify(type(error).__name__, str(error))
        return _build(
            "OpenAI API error",
            error,
            provider,
            kind,
            getattr(error, "status_code", None),
            getattr(error, "retry_after", None),
        )

    @staticmethod
    def handle_anthropic_error(error: Exception, provider: str = "anthropic") -> ProviderError:
        """Handle an Anthropic error.

        Args:
            error: The error to handle
            provider: Provider name for context

        Returns:
            The ``ProviderError`` subclass for the failure
        """
        kind = _classify(type(error).__name__, str(error))
        return _build(
            "Anthropic API error",
            error,
            provider,
            kind,
            getattr(error, "status_code", None),
            getattr(error, "retry_after", None),
        )

    @staticmethod
    def handle_bedrock_error(error: Exception, provider: str = "bedrock") -> ProviderError:
        """Handle an AWS Bedrock error (a botocore ``ClientError`` shape included).

        Args:
            error: The error to handle
            provider: Provider name for context

        Returns:
            The ``ProviderError`` subclass for the failure
        """
        error_code = None
        status_code = None
        response = getattr(error, "response", None)
        if isinstance(response, dict):
            error_code = response.get("Error", {}).get("Code")
            status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")

        code = error_code.lower() if error_code else ""
        name, text = type(error).__name__.lower(), str(error).lower()
        if "throttling" in code:
            kind = "rate_limit"
        elif "ratelimit" in name or "rate_limit" in name or "rate_limit" in text:
            kind = "rate_limit"
        elif "timeout" in name or "timeout" in text:
            kind = "timeout"
        elif "connection" in name or "connection" in text:
            kind = "connection_error"
        elif "accessdenied" in code or "access_denied" in code:
            kind = "authentication_error"
        elif "serviceunavailable" in code or "service_unavailable" in code:
            kind = "service_unavailable"
        else:
            kind = "unknown_error"
        return _build(
            "Bedrock API error", error, provider, kind, status_code, error_code=error_code
        )

    @staticmethod
    def handle_azure_error(error: Exception, provider: str = "azure") -> ProviderError:
        """Handle an Azure OpenAI error.

        Args:
            error: The error to handle
            provider: Provider name for context

        Returns:
            The ``ProviderError`` subclass for the failure
        """
        kind = _classify(type(error).__name__, str(error))
        return _build(
            "Azure OpenAI API error",
            error,
            provider,
            kind,
            getattr(error, "status_code", None),
            getattr(error, "retry_after", None),
        )

    @staticmethod
    def handle_google_error(error: Exception, provider: str = "google") -> ProviderError:
        """Handle a Google error.

        Args:
            error: The error to handle
            provider: Provider name for context

        Returns:
            The ``ProviderError`` subclass for the failure
        """
        code = getattr(error, "code", None)
        status_code = code if isinstance(code, int) else None
        name, text = type(error).__name__.lower(), str(error).lower()
        if "resourceexhausted" in name or "rate_limit" in text:
            kind = "rate_limit"
        elif "deadlineexceeded" in name or "timeout" in text:
            kind = "timeout"
        elif "unavailable" in name or "unavailable" in text:
            kind = "service_unavailable"
        elif "unauthenticated" in name or "auth" in text:
            kind = "authentication_error"
        elif "permissiondenied" in name:
            kind = "permission_error"
        else:
            kind = "unknown_error"
        return _build("Google API error", error, provider, kind, status_code)

    @staticmethod
    def wrap_provider_error(
        error: Exception,
        provider: str,
    ) -> ProviderError:
        """Wrap a provider error in the ``ProviderError`` subclass it calls for.

        Routes to the provider-specific handler by provider name; a ``ProviderError`` is returned
        as it is.

        Args:
            error: The error to wrap
            provider: Provider name (openai, anthropic, bedrock, azure, google, or another)

        Returns:
            The ``ProviderError`` subclass for the failure
        """
        if isinstance(error, ProviderError):
            return error

        handlers: dict[str, Callable[[Exception, str], ProviderError]] = {
            "openai": ErrorHandler.handle_openai_error,
            "anthropic": ErrorHandler.handle_anthropic_error,
            "bedrock": ErrorHandler.handle_bedrock_error,
            "azure": ErrorHandler.handle_azure_error,
            "google": ErrorHandler.handle_google_error,
        }
        handler = handlers.get(provider)
        if handler is not None:
            return handler(error, provider)
        kind = "timeout" if _is_timeout(error) else "unknown_error"
        return _build("Provider error", error, provider, kind, getattr(error, "status_code", None))


__all__ = ["ErrorHandler", "error_class"]
