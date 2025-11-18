"""Model and embedding providers for Nimbus.

This module provides concrete implementations of ModelInterface and VectorEncoderInterface
for various LLM and embedding providers. Providers are loaded lazily and only require
their dependencies when instantiated.

Supported LLM Providers:
- OpenAI (GPT-4, GPT-3.5, o1, o3)
- Anthropic (Claude 3.x)
- AWS Bedrock (Claude, Titan, Llama, etc.)
- Azure OpenAI
- Google Vertex AI (Gemini, PaLM)

Supported Embedding Providers:
- OpenAI (text-embedding-3-small/large, ada-002)
- AWS Bedrock Titan Embeddings
- Cohere Embeddings
- Vertex AI Text Embeddings
- Vertex AI Multimodal Embeddings

Example:
    >>> from nimbus.providers import ProviderRegistry
    >>>
    >>> # Get a model provider
    >>> provider = ProviderRegistry.get_model_provider("openai", api_key="sk-...")
    >>> response = provider.complete(request)
    >>>
    >>> # Get an embedding provider
    >>> embedder = ProviderRegistry.get_embedding_provider("openai", model="text-embedding-3-small")
    >>> vectors = embedder.encode_batch(["text1", "text2"])
"""

from nimbus.providers.base import BaseEmbeddingProvider, BaseModelProvider
from nimbus.providers.cost_calculator import CostCalculator
from nimbus.providers.embeddings.bedrock_embeddings import BedrockEmbeddingProvider
from nimbus.providers.embeddings.cohere_embeddings import CohereEmbeddingProvider
from nimbus.providers.embeddings.openai_embeddings import OpenAIEmbeddingProvider
from nimbus.providers.embeddings.vertex_embeddings import VertexEmbeddingProvider
from nimbus.providers.embeddings.vertex_multimodal_embeddings import (
    VertexMultimodalEmbeddingProvider,
)
from nimbus.providers.lazy_import import LazyImporter
from nimbus.providers.llm.anthropic_provider import AnthropicProvider
from nimbus.providers.llm.azure_provider import AzureOpenAIProvider
from nimbus.providers.llm.bedrock_provider import BedrockProvider
from nimbus.providers.llm.openai_provider import OpenAIProvider
from nimbus.providers.llm.vertex_provider import VertexAIProvider
from nimbus.providers.multimodal import ImageHandler
from nimbus.providers.registry import ProviderRegistry
from nimbus.providers.token_counter import TokenCounter

# Register model providers
ProviderRegistry.register_model_provider("openai", OpenAIProvider)
ProviderRegistry.register_model_provider("anthropic", AnthropicProvider)
ProviderRegistry.register_model_provider("bedrock", BedrockProvider)
ProviderRegistry.register_model_provider("azure", AzureOpenAIProvider)
ProviderRegistry.register_model_provider("vertex", VertexAIProvider)

# Register embedding providers
ProviderRegistry.register_embedding_provider("openai", OpenAIEmbeddingProvider)
ProviderRegistry.register_embedding_provider("bedrock", BedrockEmbeddingProvider)
ProviderRegistry.register_embedding_provider("cohere", CohereEmbeddingProvider)
ProviderRegistry.register_embedding_provider("vertex", VertexEmbeddingProvider)
ProviderRegistry.register_embedding_provider("vertex-multimodal", VertexMultimodalEmbeddingProvider)

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
    "VertexAIProvider",
    "OpenAIEmbeddingProvider",
    "BedrockEmbeddingProvider",
    "CohereEmbeddingProvider",
    "VertexEmbeddingProvider",
    "VertexMultimodalEmbeddingProvider",
]
