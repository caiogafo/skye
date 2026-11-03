"""API-key and bearer strategies for OpenAI-compatible providers, Anthropic and Cohere.

Each provider's key comes from its own standard variable, never from a prefixed one
(Requirement 11.6). A missing key raises ``ConfigurationError`` naming the variable, never a value;
``repr`` shows the class name only; ``apply`` returns a new dict and leaves the input alone.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from skye.base.exceptions import ConfigurationError

#: The provider-standard variable that holds each provider's key.
STANDARD_ENV_VARS: Mapping[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "cohere": "COHERE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "together": "TOGETHER_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "xai": "XAI_API_KEY",
}


def _key(api_key: str | None, env_var: str) -> str:
    key = api_key or os.environ.get(env_var)
    if not key:
        raise ConfigurationError(
            f"No API key: pass api_key or set {env_var}", details={"variable": env_var}
        )
    return key


class ApiKeyAuth:
    """The key in a header of its own (``x-api-key`` for Anthropic).

    Args:
        env_var: The provider-standard variable to read when no key is passed.
        api_key: The key; the variable is not read when it is given.
        header: The header that carries the key.
    """

    def __init__(
        self, env_var: str, api_key: str | None = None, *, header: str = "x-api-key"
    ) -> None:
        self._key = _key(api_key, env_var)
        self._header = header

    def apply(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> dict[str, str]:
        """The headers with the key added."""
        return {**headers, self._header: self._key}

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class BearerAuth:
    """``Authorization: Bearer <key>``, the scheme of OpenAI and of the providers that copy it.

    Args:
        env_var: The provider-standard variable to read when no key is passed.
        api_key: The key; the variable is not read when it is given.
    """

    def __init__(self, env_var: str, api_key: str | None = None) -> None:
        self._key = _key(api_key, env_var)

    def apply(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> dict[str, str]:
        """The headers with the bearer key added."""
        return {**headers, "Authorization": f"Bearer {self._key}"}

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


def openai_authenticator(
    api_key: str | None = None, *, env_var: str = "OPENAI_API_KEY"
) -> BearerAuth:
    """Bearer authentication for OpenAI and OpenAI-compatible servers (variable can be changed)."""
    return BearerAuth(env_var, api_key)


def anthropic_authenticator(api_key: str | None = None) -> ApiKeyAuth:
    """The ``x-api-key`` header of Anthropic, from ``ANTHROPIC_API_KEY``."""
    return ApiKeyAuth("ANTHROPIC_API_KEY", api_key, header="x-api-key")


def cohere_authenticator(api_key: str | None = None) -> BearerAuth:
    """Bearer authentication for Cohere, from ``COHERE_API_KEY``."""
    return BearerAuth("COHERE_API_KEY", api_key)


def api_key_authenticator(provider: str, api_key: str | None = None) -> ApiKeyAuth | BearerAuth:
    """The strategy of a provider by name: Anthropic uses ``x-api-key``, the others a bearer key.

    Raises:
        ConfigurationError: For a provider with no standard variable (pass ``env_var`` to
            ``BearerAuth`` yourself).
    """
    if provider not in STANDARD_ENV_VARS:
        raise ConfigurationError(
            f"No standard API-key variable is known for provider {provider!r}",
            details={"provider": provider},
        )
    if provider == "anthropic":
        return anthropic_authenticator(api_key)
    return BearerAuth(STANDARD_ENV_VARS[provider], api_key)


__all__ = [
    "STANDARD_ENV_VARS",
    "ApiKeyAuth",
    "BearerAuth",
    "openai_authenticator",
    "anthropic_authenticator",
    "cohere_authenticator",
    "api_key_authenticator",
]
