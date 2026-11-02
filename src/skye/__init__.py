"""Skye - Modular GenAI library with optional extras.

Skye provides a foundational layer for building AI agents and intelligent applications
with a Clean Architecture approach. The base package includes only interfaces and models,
while all implementations are available as optional extras. The top level re-exports only
the four base modules (messages, completion, exceptions, config); import everything else
from its Component path (skye.models, skye.router, skye.tools, ...).

Installation:
    pip install skyeai                    # Base only
    pip install skyeai[bedrock]           # + Bedrock provider
    pip install skyeai[agents,memory]     # + Multiple extras
    pip install skyeai[all]               # Everything

Example:
    >>> import skye
    >>> from skye.base.messages import UserMessage
    >>>
    >>> client = skye.provider("bedrock", region="us-east-1")
    >>> response = client.complete(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
    ... )
    >>> print(response.text)
"""

__version__ = "0.1.0"

from typing import TYPE_CHECKING, Any

from skye.base import completion, config, exceptions, messages

if TYPE_CHECKING:
    from skye.base.interfaces.model import ModelInterface
    from skye.base.interfaces.vector_encoder import VectorEncoderInterface

__all__ = ["__version__", "messages", "completion", "exceptions", "config", "provider"]


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

    return _provider(name, **config)
