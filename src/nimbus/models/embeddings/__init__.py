"""Embedding provider implementations for Nimbus.

This module provides concrete implementations of VectorEncoderInterface for various
embedding providers.

Example:
    >>> from nimbus.models.embeddings import OpenAIEmbeddingProvider
    >>>
    >>> embedder = OpenAIEmbeddingProvider(model="text-embedding-3-small", api_key="sk-...")
    >>> vector = embedder.encode("Hello, world!")
    >>> vectors = embedder.encode_batch(["text1", "text2", "text3"])
"""

from nimbus.models.embeddings.bedrock_embeddings import BedrockEmbeddingProvider
from nimbus.models.embeddings.cohere_embeddings import CohereEmbeddingProvider
from nimbus.models.embeddings.openai_embeddings import OpenAIEmbeddingProvider
from nimbus.models.embeddings.google_embeddings import GoogleEmbeddingProvider
from nimbus.models.embeddings.google_multimodal_embeddings import (
    GoogleMultimodalEmbeddingProvider,
)

__all__ = [
    "OpenAIEmbeddingProvider",
    "BedrockEmbeddingProvider",
    "CohereEmbeddingProvider",
    "GoogleEmbeddingProvider",
    "GoogleMultimodalEmbeddingProvider",
]
