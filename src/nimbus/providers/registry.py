"""Provider registry for model and embedding providers.

This module provides a central registry for discovering and instantiating
model and embedding providers. Providers can be registered by name and
retrieved with configuration.

Example:
    >>> from nimbus.providers.registry import ProviderRegistry
    >>> from nimbus.providers.openai_provider import OpenAIProvider
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

from typing import Any, Type

from nimbus.exceptions import ConfigurationError
from nimbus.interfaces.model import ModelInterface
from nimbus.interfaces.vector_encoder import VectorEncoderInterface


class ProviderRegistry:
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
            >>> from nimbus.providers.openai_provider import OpenAIProvider
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
            >>> from nimbus.providers.embeddings.openai_embeddings import OpenAIEmbeddingProvider
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
            raise ConfigurationError(
                f"Model provider '{name}' not found. "
                f"Available providers: {available}. "
                f"Install with: pip install nimbus[{name}]"
            )

        provider_class = cls._model_providers[name]
        try:
            return provider_class(**config)
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
                f"Embedding provider '{name}' not found. "
                f"Available providers: {available}. "
                f"Install with: pip install nimbus[{name}]"
            )

        provider_class = cls._embedding_providers[name]
        try:
            return provider_class(**config)
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
            ['openai', 'anthropic', 'bedrock', 'azure', 'vertex']
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
            ['openai', 'bedrock', 'cohere', 'vertex']
        """
        return list(cls._embedding_providers.keys())
