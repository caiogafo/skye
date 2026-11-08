"""Skye - Modular GenAI library with optional extras.

Skye provides a foundational layer for building AI agents and intelligent applications
with a Clean Architecture approach. The base package includes only interfaces and models,
while all implementations are available as optional extras. The top level re-exports only
the commonest names (messages, completion, errors) and ``provider``; the modules ``skye.messages``, ``skye.completion``, ``skye.exceptions``, ``skye.config``, ``skye.data`` and ``skye.interfaces`` are the public paths of ``base``; import everything else
from its Component path (skye.models, skye.router, skye.tools, ...).

Installation:
    pip install skyeai                    # every provider (built-in REST adapters)
    pip install skyeai[tokens]            # + exact token counts
    pip install skyeai[memory]            # + Redis store
    pip install skyeai[all]               # every optional library

Example:
    >>> import skye
    >>> from skye import UserMessage
    >>>
    >>> client = skye.provider("bedrock", region="us-east-1")
    >>> response = client.complete(  # doctest: +SKIP
    ...     messages=[UserMessage(content="Hello")],
    ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
    ... )
    >>> print(response.content)  # doctest: +SKIP
"""

__version__ = "0.1.1"

from typing import TYPE_CHECKING, Any, Literal, overload


if TYPE_CHECKING:
    from skye.base.completion import CompleteRequest, CompleteResponse, StreamChunk, TokenUsage
    from skye.base.exceptions import (
        ConfigurationError,
        MissingExtraError,
        ProviderError,
        SkyeError,
        ValidationError,
    )
    from skye.base.messages import AssistantMessage, CapabilityMessage, SystemMessage, UserMessage
    from skye.flows import Flow
    from skye.utils.skye_files import load
    from skye.base.interfaces.model import ModelInterface
    from skye.base.interfaces.vector_encoder import VectorEncoderInterface

# The commonest names, importable as ``from skye import UserMessage``; each is loaded on first use, so ``import skye`` stays light.
_LAZY = {
    "UserMessage": "skye.base.messages",
    "SystemMessage": "skye.base.messages",
    "AssistantMessage": "skye.base.messages",
    "CapabilityMessage": "skye.base.messages",
    "CompleteRequest": "skye.base.completion",
    "CompleteResponse": "skye.base.completion",
    "StreamChunk": "skye.base.completion",
    "TokenUsage": "skye.base.completion",
    "SkyeError": "skye.base.exceptions",
    "ProviderError": "skye.base.exceptions",
    "ConfigurationError": "skye.base.exceptions",
    "ValidationError": "skye.base.exceptions",
    "MissingExtraError": "skye.base.exceptions",
    "load": "skye.utils.skye_files",
    "Flow": "skye.flows",
}

__all__ = ["__version__", "messages", "completion", "exceptions", "config", "provider", *_LAZY]


def __getattr__(name: str) -> Any:
    """Load a commonly used name (``UserMessage``, ``SkyeError``, ...) on first access."""
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module 'skye' has no attribute {name!r}")
    import importlib

    value = getattr(importlib.import_module(module), name)
    globals()[name] = value
    return value


@overload
def provider(name: str, *, provider_type: Literal["embedding"], **config: Any) -> "VectorEncoderInterface": ...


@overload
def provider(name: str, *, provider_type: Literal["model"] = ..., **config: Any) -> "ModelInterface": ...


def provider(name: str, **config: Any) -> "ModelInterface | VectorEncoderInterface":
    """Create the client of a model provider with one call, in the style of ``boto3.client``.

    ``name`` is the provider (``"openai"``, ``"anthropic"``, ``"bedrock"``, ``"azure"``, ``"google"``, ``"cohere"``); the rest is its
    configuration. Pass ``provider_type="embedding"`` to get an embedding client instead of a language model client. The registry is
    imported only when this function is called, so ``import skye`` stays light.

    Example:
        >>> import skye
        >>> client = skye.provider("openai", api_key="sk-...")
        >>> embedder = skye.provider("openai", model="text-embedding-3-small", provider_type="embedding")
    """
    from skye.models.registry import provider as _provider

    client: ModelInterface | VectorEncoderInterface = _provider(name, **config)
    return client


# The public module paths of ``base`` (``skye.messages`` and the others); imported last so that they are attributes of ``skye``.
from skye import completion, config, exceptions, messages  # noqa: E402
