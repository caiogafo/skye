"""Embedding provider implementations for Nimbus.

This module provides concrete implementations of VectorEncoderInterface for various
embedding providers.

Example:
    >>> from nimbus.providers.embeddings import OpenAIEmbeddingProvider
    >>>
    >>> embedder = OpenAIEmbeddingProvider(model="text-embedding-3-small", api_key="sk-...")
    >>> vector = embedder.encode("Hello, world!")
    >>> vectors = embedder.encode_batch(["text1", "text2", "text3"])
"""

from nimbus.providers.embeddings.bedrock_embeddings import BedrockEmbeddingProvider
from nimbus.providers.embeddings.cohere_embeddings import CohereEmbeddingProvider
from nimbus.providers.embeddings.openai_embeddings import OpenAIEmbeddingProvider
from nimbus.providers.embeddings.vertex_embeddings import VertexEmbeddingProvider
from nimbus.providers.embeddings.vertex_multimodal_embeddings import (
    VertexMultimodalEmbeddingProvider,
)

__all__ = [
    "OpenAIEmbeddingProvider",
    "BedrockEmbeddingProvider",
    "CohereEmbeddingProvider",
    "VertexEmbeddingProvider",
    "VertexMultimodalEmbeddingProvider",
]
