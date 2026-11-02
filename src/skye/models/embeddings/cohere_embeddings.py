"""Cohere embedding provider implementation.

This module provides the CohereEmbeddingProvider class for generating embeddings
using Cohere's embedding models.

Example:
    >>> from skye.models.embeddings import CohereEmbeddingProvider
    >>>
    >>> embedder = CohereEmbeddingProvider(
    ...     model="embed-english-v3.0",
    ...     api_key="..."
    ... )
    >>> vector = embedder.encode("Hello, world!")
    >>> vectors = embedder.encode_batch(["text1", "text2"])
"""

from typing import Any

from skye.models.base import BaseEmbeddingProvider
from skye.models.transport import rest

COHERE_EMBED_URL = "https://api.cohere.com/v2/embed"


class CohereEmbeddingProvider(BaseEmbeddingProvider):
    """Cohere embedding provider implementation (stdlib REST, no vendor SDK).
    
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
        """No vendor SDK is used: requests go through ``skye.models.transport.rest``.

        Returns:
            None (kept so ``self.client`` remains valid for the base class)
        """
        return None
    
    def _encode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors using the Cohere v2 REST API.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        response = rest.post_json(
            COHERE_EMBED_URL,
            {
                "model": self.model,
                "texts": texts,
                "input_type": "search_document",
                "embedding_types": ["float"],
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=float(self.config.get("timeout", 60.0)),
            provider="cohere",
        )
        return [list(vector) for vector in response.embeddings.float]
    
    def get_vector_dimension(self) -> int:
        """Return the dimension of vectors produced by this model.
        
        Returns:
            The vector dimension size
        """
        if self.model not in self.MODEL_DIMENSIONS:
            raise ValueError(f"Unknown model: {self.model}")
        return self.MODEL_DIMENSIONS[self.model]
