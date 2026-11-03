"""The credential-source registry: the one extension point of ``auth`` (Requirement 11.5).

A credential source is a factory: ``factory(**config)`` returns an authenticator (an
``AuthenticationInterface``) or, for a secret manager, an object with ``get(name)``. User code
registers its own source under a name and resolves it by that name; adding a source edits only the
user's code and this registry, never another component. The sources that ship with ``auth`` are
registered here under fixed names and imported only when resolved, so listing the registry loads
nothing.
"""

from __future__ import annotations

import importlib
import threading
from collections.abc import Callable
from typing import Any

from skye.base.exceptions import ConfigurationError

CredentialSourceFactory = Callable[..., Any]

#: The sources that ship with ``auth``: name -> ``module:attribute`` of the factory.
BUILTIN_SOURCES: dict[str, str] = {
    "openai": "skye.auth.openai_compatible:openai_authenticator",
    "anthropic": "skye.auth.openai_compatible:anthropic_authenticator",
    "cohere": "skye.auth.openai_compatible:cohere_authenticator",
    "aws": "skye.auth.aws:aws_authenticator",
    "bedrock": "skye.auth.aws:bedrock_authenticator",
    "google": "skye.auth.google:resolve_google_auth",
    "azure": "skye.auth.azure:resolve_azure_auth",
    "client-credentials": "skye.auth.oauth2:ClientCredentialsAuth",
    "token-exchange": "skye.auth.oauth2:TokenExchangeAuth",
    "aws-secrets-manager": "skye.auth.secrets:AwsSecretsManager",
    "aws-ssm": "skye.auth.secrets:AwsParameterStore",
    "azure-key-vault": "skye.auth.secrets:AzureKeyVault",
    "google-secret-manager": "skye.auth.secrets:GoogleSecretManager",
}

_custom: dict[str, CredentialSourceFactory] = {}
_lock = threading.Lock()


def _check_name(name: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ConfigurationError(
            "A credential source needs a non-empty name", details={"name": name}
        )


def register_credential_source(
    name: str, factory: CredentialSourceFactory, *, replace: bool = False
) -> None:
    """Register a credential source under ``name``.

    Args:
        name: The name to resolve it by.
        factory: ``factory(**config)`` returns the authenticator (or secret source).
        replace: Allow replacing a source already registered under the name (one of the built-in
            names can only be replaced this way).

    Raises:
        ConfigurationError: The name is empty, or already taken and ``replace`` is false.
    """
    _check_name(name)
    if not callable(factory):
        raise ConfigurationError(
            "A credential source factory must be callable", details={"name": name}
        )
    with _lock:
        if (name in _custom or name in BUILTIN_SOURCES) and not replace:
            raise ConfigurationError(
                f"A credential source named {name!r} is already registered", details={"name": name}
            )
        _custom[name] = factory


def unregister_credential_source(name: str) -> None:
    """Remove a source registered with :func:`register_credential_source` (built-in ones stay)."""
    with _lock:
        _custom.pop(name, None)


def list_credential_sources() -> list[str]:
    """The names of every source: the built-in ones and those registered by user code."""
    with _lock:
        return sorted({*BUILTIN_SOURCES, *_custom})


def resolve_credential_source(name: str, **config: Any) -> Any:
    """Build the source registered under ``name`` with ``config``.

    Raises:
        ConfigurationError: No source has that name (the message lists the names).
    """
    with _lock:
        factory = _custom.get(name)
    if factory is None and name in BUILTIN_SOURCES:
        module, _, attribute = BUILTIN_SOURCES[name].partition(":")
        factory = getattr(importlib.import_module(module), attribute)
    if factory is None:
        raise ConfigurationError(
            f"No credential source named {name!r}; known: {', '.join(list_credential_sources())}",
            details={"name": name},
        )
    return factory(**config)


__all__ = [
    "BUILTIN_SOURCES",
    "register_credential_source",
    "unregister_credential_source",
    "list_credential_sources",
    "resolve_credential_source",
]
