"""Cohere embedding provider implementation.

This module provides the CohereEmbeddingProvider class for generating embeddings
using Cohere's embedding models.

Example:
    >>> from nimbus.providers.embeddings import CohereEmbeddingProvider
    >>>
    >>> embedder = CohereEmbeddingProvider(
    ...     model="embed-english-v3.0",
    ...     api_key="..."
    ... )
    >>> vector = embedder.encode("Hello, world!")
    >>> vectors = embedder.encode_batch(["text1", "text2"])
"""

from typing import Any

from nimbus.providers.base import BaseEmbeddingProvider
from nimbus.providers.lazy_import import LazyImporter


class CohereEmbeddingProvider(BaseEmbeddingProvider):
    """Cohere embedding provider implementation.
    
    Supports Cohere's embedding models:
    - embed-english-v3.0 (1024 dimensions)
    - embed-english-light-v3.0 (384 dimensions)
    - embed-multilingual-v3.0 (1024 dimensions)
    
    Example:
        >>> embedder = CohereEmbeddingProvider(
        ...     model="embed-english-v3.0",
        ...     api_key="..."
        ... )
        >>> vector = embedder.encode("Hello")
        >>> vectors = embedder.encode_batch(["text1", "text2"])
    """
    
    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "embed-english-v3.0": 1024,
        "embed-english-light-v3.0": 384,
        "embed-multilingual-v3.0": 1024,
    }
    
    def __init__(self, model: str, api_key: str, **config: Any) -> None:
        """Initialize Cohere embedding provider.
        
        Args:
            model: Model identifier (e.g., 'embed-english-v3.0')
            api_key: Cohere API key
            **config: Additional configuration parameters
        """
        super().__init__(model=model, api_key=api_key, **config)
        self.api_key = api_key
    
    def _initialize_client(self) -> Any:
        """Initialize Cohere client.
        
        Returns:
            Cohere client instance
        """
        cohere = LazyImporter.import_module("cohere", install_extra="cohere")
        return cohere.ClientV2(api_key=self.api_key)
    
    def _encode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors using Cohere API.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        response = self.client.embed(
            model=self.model,
            texts=texts,
            input_type="search_document"
        )
        return [embedding for embedding in response.embeddings]
    
    def get_vector_dimension(self) -> int:
        """Return the dimension of vectors produced by this model.
        
        Returns:
            The vector dimension size
        """
        if self.model not in self.MODEL_DIMENSIONS:
            raise ValueError(f"Unknown model: {self.model}")
        return self.MODEL_DIMENSIONS[self.model]
