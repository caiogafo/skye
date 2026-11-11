"""Provider registry for model and embedding providers.

This module provides a central registry for discovering and instantiating
model and embedding providers. Providers can be registered by name and
retrieved with configuration.

Example:
    >>> from skye.models.registry import ProviderRegistry
    >>> from skye.models.llm.openai import OpenAIProvider
    >>>
    >>> # Register a provider
    >>> ProviderRegistry.register_model_provider("openai", OpenAIProvider)
    >>>
    >>> # Get a provider instance
    >>> provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")
    >>>
    >>> # List available providers
    >>> providers = ProviderRegistry.list_model_providers()
"""

import inspect
from typing import Any, Literal, Type, overload

from skye.base.exceptions import ConfigurationError
from skye.base.interfaces.model import ModelInterface
from skye.base.interfaces.registry import ProviderRegistryInterface, set_provider_registry
from skye.base.interfaces.vector_encoder import VectorEncoderInterface


class ProviderRegistry(ProviderRegistryInterface):
    """Registry for model and embedding providers.

    This class provides a central registry for discovering and instantiating
    model and embedding providers. Providers are registered by name and can
    be retrieved with configuration parameters.

    The registry maintains separate collections for model providers (LLMs)
    and embedding providers (vector encoders).

    Example:
        >>> # Register providers
        >>> ProviderRegistry.register_model_provider("openai", OpenAIProvider)
        >>> ProviderRegistry.register_embedding_provider("openai", OpenAIEmbeddingProvider)
        >>>
        >>> # Get provider instances
        >>> model = ProviderRegistry.get_model_provider("openai", api_key="sk-...")
        >>> embedder = ProviderRegistry.get_embedding_provider("openai", model="text-embedding-3-small")
        >>>
        >>> # List available providers
        >>> print(ProviderRegistry.list_model_providers())
        ['openai', 'anthropic', 'bedrock']
    """

    _model_providers: dict[str, Type[ModelInterface]] = {}
    _embedding_providers: dict[str, Type[VectorEncoderInterface]] = {}

    @classmethod
    def register_model_provider(
        cls, name: str, provider_class: Type[ModelInterface]
    ) -> None:
        """Register a model provider.

        Args:
            name: The name to register the provider under (e.g., "openai", "bedrock").
            provider_class: The provider class that implements ModelInterface.

        Example:
            >>> from skye.models.llm.openai import OpenAIProvider
            >>> ProviderRegistry.register_model_provider("openai", OpenAIProvider)
        """
        cls._model_providers[name] = provider_class

    @classmethod
    def register_embedding_provider(
        cls, name: str, provider_class: Type[VectorEncoderInterface]
    ) -> None:
        """Register an embedding provider.

        Args:
            name: The name to register the provider under (e.g., "openai", "cohere").
            provider_class: The provider class that implements VectorEncoderInterface.

        Example:
            >>> from skye.models.embeddings.openai_embeddings import OpenAIEmbeddingProvider
            >>> ProviderRegistry.register_embedding_provider("openai", OpenAIEmbeddingProvider)
        """
        cls._embedding_providers[name] = provider_class

    @classmethod
    def get_model_provider(cls, name: str, **config: Any) -> ModelInterface:
        """Instantiate a model provider by name.

        Args:
            name: The name of the provider to instantiate.
            **config: Configuration parameters to pass to the provider constructor.

        Returns:
            An instance of the requested model provider.

        Raises:
            ConfigurationError: If the provider is not found or not installed.

        Example:
            >>> provider = ProviderRegistry.get_model_provider(
            ...     "openai",
            ...     api_key="sk-...",
            ...     api_base="https://api.openai.com/v1"
            ... )
            >>> response = provider.complete(request)
        """
        if name not in cls._model_providers:
            available = ", ".join(cls._model_providers.keys()) or "none"
            hint = (
                f" '{name}' is an embedding provider: pass provider_type=\"embedding\"."
                if name in cls._embedding_providers
                else ""
            )
            raise ConfigurationError(
                f"Model provider '{name}' not found. Available model providers: {available}.{hint}"
            )

        provider_class = cls._model_providers[name]
        try:
            return provider_class(**config)
        except ConfigurationError:
            raise  # it already says what is missing (a key, a region) and names the variable
        except Exception as e:
            raise ConfigurationError(
                f"Failed to instantiate provider '{name}': {str(e)}"
            ) from e

    @classmethod
    def get_embedding_provider(
        cls, name: str, **config: Any
    ) -> VectorEncoderInterface:
        """Instantiate an embedding provider by name.

        Args:
            name: The name of the provider to instantiate.
            **config: Configuration parameters to pass to the provider constructor.

        Returns:
            An instance of the requested embedding provider.

        Raises:
            ConfigurationError: If the provider is not found or not installed.

        Example:
            >>> embedder = ProviderRegistry.get_embedding_provider(
            ...     "openai",
            ...     model="text-embedding-3-small",
            ...     api_key="sk-..."
            ... )
            >>> vectors = embedder.encode_batch(["text1", "text2"])
        """
        if name not in cls._embedding_providers:
            available = ", ".join(cls._embedding_providers.keys()) or "none"
            raise ConfigurationError(
                f"Embedding provider '{name}' not found. Available embedding providers: {available}."
            )

        provider_class = cls._embedding_providers[name]
        try:
            return provider_class(**config)
        except ConfigurationError:
            raise  # it already says what is missing (a key, a region) and names the variable
        except Exception as e:
            raise ConfigurationError(
                f"Failed to instantiate embedding provider '{name}': {str(e)}"
            ) from e

    @classmethod
    def list_model_providers(cls) -> list[str]:
        """List all registered model providers.

        Returns:
            List of registered model provider names.

        Example:
            >>> providers = ProviderRegistry.list_model_providers()
            >>> print(providers)
            ['openai', 'anthropic', 'bedrock', 'azure', 'google']
        """
        return list(cls._model_providers.keys())

    @classmethod
    def list_embedding_providers(cls) -> list[str]:
        """List all registered embedding providers.

        Returns:
            List of registered embedding provider names.

        Example:
            >>> providers = ProviderRegistry.list_embedding_providers()
            >>> print(providers)
            ['openai', 'bedrock', 'cohere', 'google']
        """
        return list(cls._embedding_providers.keys())


set_provider_registry(ProviderRegistry)


@overload
def provider(name: str, *, provider_type: Literal["embedding"], **config: Any) -> VectorEncoderInterface: ...


@overload
def provider(name: str, *, provider_type: Literal["model"] = ..., **config: Any) -> ModelInterface: ...


def provider(name: str, **config: Any) -> ModelInterface | VectorEncoderInterface:
    """Create a provider client (boto3-style API).

    This is the main entry point for the simplified boto3-style API.
    Returns a provider instance that supports direct method calls.

    Args:
        name: Provider name (e.g., "openai", "bedrock", "anthropic", "cohere").
        **config: Provider-specific configuration. Use provider_type="embedding"
            to get an embedding provider instead of a model provider; a name that has only an
            embedding provider (``cohere``) gives it without ``provider_type``. ``region`` is an
            alias of the AWS ``region_name`` and of the Google ``location``; ``location`` stays
            ``location`` for Google. ``max_retries`` (0 turns retries off) goes to the client.

    Returns:
        ModelInterface or VectorEncoderInterface instance that supports boto3-style calls.

    Example:
        >>> from skye.base.messages import UserMessage
        >>>
        >>> # OpenAI LLM
        >>> client = provider("openai", api_key="sk-...")
        >>> response = client.complete(
        ...     messages=[UserMessage(content="Hello")],
        ...     model="gpt-4"
        ... )
        >>>
        >>> # OpenAI Embeddings
        >>> embedder = provider(
        ...     "openai",
        ...     api_key="sk-...",
        ...     model="text-embedding-3-small",
        ...     provider_type="embedding"
        ... )
        >>> vectors = embedder.encode_batch(["text1", "text2"])
        >>>
        >>> # Bedrock LLM
        >>> client = provider("bedrock", region="us-east-1")
        >>> response = client.complete(
        ...     messages=[UserMessage(content="Hello")],
        ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
        ... )
        >>>
        >>> # Bedrock Embeddings
        >>> embedder = provider(
        ...     "bedrock",
        ...     region="us-east-1",
        ...     model="amazon.titan-embed-text-v1",
        ...     provider_type="embedding"
        ... )
        >>> vectors = embedder.encode_batch(["text1", "text2"])
        >>>
        >>> # Google Embeddings
        >>> embedder = provider(
        ...     "google",
        ...     project_id="my-project",
        ...     location="us-central1",
        ...     model="textembedding-gecko@003",
        ...     provider_type="embedding"
        ... )
        >>> vectors = embedder.encode_batch(["text1", "text2"])
    """
    provider_type = config.pop("provider_type", None)
    if provider_type is None:
        # A name registered only for embeddings (``cohere``) gives its embedding client.
        only_embedding = (
            name in ProviderRegistry._embedding_providers and name not in ProviderRegistry._model_providers
        )
        provider_type = "embedding" if only_embedding else "model"

    registered = (
        ProviderRegistry._embedding_providers if provider_type == "embedding" else ProviderRegistry._model_providers
    )
    target = registered.get(name)
    if target is not None:
        _normalize_location(target, config)

    if provider_type == "embedding":
        return ProviderRegistry.get_embedding_provider(name, **config)
    return ProviderRegistry.get_model_provider(name, **config)


def _parameters(cls: type) -> set[str]:
    try:
        return set(inspect.signature(cls).parameters)
    except (TypeError, ValueError):
        return set()


def _normalize_location(cls: type, config: dict[str, Any]) -> None:
    """Let ``region`` and ``location`` name the parameter the class takes.

    An AWS client takes ``region_name`` (``region`` and ``location`` are aliases of it); a Google
    client takes ``location`` (``region`` is an alias of it), which is never renamed.
    """
    accepted = _parameters(cls)
    if "location" in accepted:
        if "region" in config and "location" not in config:
            config["location"] = config.pop("region")
        if "region_name" in config and "location" not in config:
            config["location"] = config.pop("region_name")
    elif "region_name" in accepted:
        for alias in ("region", "location"):
            if alias in config and "region_name" not in config:
                config["region_name"] = config.pop(alias)
