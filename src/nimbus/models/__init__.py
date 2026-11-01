"""Model and embedding providers for Nimbus.

This module provides concrete implementations of ModelInterface and VectorEncoderInterface
for various LLM and embedding providers. Providers are loaded lazily and only require
their dependencies when instantiated.

Supported LLM Providers:
- OpenAI (GPT-4, GPT-3.5, o1, o3)
- Anthropic (Claude 3.x)
- AWS Bedrock (Claude, Titan, Llama, etc.)
- Azure OpenAI
- Google (Gemini, PaLM)

Supported Embedding Providers:
- OpenAI (text-embedding-3-small/large, ada-002)
- AWS Bedrock Titan Embeddings
- Cohere Embeddings
- Google Text Embeddings
- Google Multimodal Embeddings

Example:
    >>> from nimbus.models import ProviderRegistry
    >>>
    >>> # Get a model provider
    >>> provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")
    >>> response = provider.complete(request)
    >>>
    >>> # Get an embedding provider
    >>> embedder = ProviderRegistry.get_embedding_provider("openai", model="text-embedding-3-small")
    >>> vectors = embedder.encode_batch(["text1", "text2"])
"""

from nimbus.models.base import BaseEmbeddingProvider, BaseModelProvider
from nimbus.models.transport.cost import CostCalculator
from nimbus.models.embeddings.bedrock_embeddings import BedrockEmbeddingProvider
from nimbus.models.embeddings.cohere_embeddings import CohereEmbeddingProvider
from nimbus.models.embeddings.openai_embeddings import OpenAIEmbeddingProvider
from nimbus.models.embeddings.google_embeddings import GoogleEmbeddingProvider
from nimbus.models.embeddings.google_multimodal_embeddings import (
    GoogleMultimodalEmbeddingProvider,
)
from nimbus.models.lazy_import import LazyImporter
from nimbus.models.llm.anthropic import AnthropicProvider
from nimbus.models.llm.bedrock import BedrockProvider
from nimbus.models.llm.openai_compatible import AzureOpenAIProvider, OpenAIProvider
from nimbus.models.llm.google_provider import GoogleProvider
from nimbus.models.transport.multimodal import ImageHandler
from nimbus.models.registry import ProviderRegistry
from nimbus.models.transport.token_counter import TokenCounter

# Register model providers
ProviderRegistry.register_model_provider("openai", OpenAIProvider)
ProviderRegistry.register_model_provider("anthropic", AnthropicProvider)
ProviderRegistry.register_model_provider("bedrock", BedrockProvider)
ProviderRegistry.register_model_provider("azure", AzureOpenAIProvider)
ProviderRegistry.register_model_provider("google", GoogleProvider)

# Register embedding providers
ProviderRegistry.register_embedding_provider("openai", OpenAIEmbeddingProvider)
ProviderRegistry.register_embedding_provider("bedrock", BedrockEmbeddingProvider)
ProviderRegistry.register_embedding_provider("cohere", CohereEmbeddingProvider)
ProviderRegistry.register_embedding_provider("google", GoogleEmbeddingProvider)
ProviderRegistry.register_embedding_provider("google-multimodal", GoogleMultimodalEmbeddingProvider)

__all__ = [
    "BaseModelProvider",
    "BaseEmbeddingProvider",
    "LazyImporter",
    "ProviderRegistry",
    "ImageHandler",
    "TokenCounter",
    "CostCalculator",
    "OpenAIProvider",
    "AnthropicProvider",
    "BedrockProvider",
    "AzureOpenAIProvider",
    "GoogleProvider",
    "OpenAIEmbeddingProvider",
    "BedrockEmbeddingProvider",
    "CohereEmbeddingProvider",
    "GoogleEmbeddingProvider",
    "GoogleMultimodalEmbeddingProvider",
]
