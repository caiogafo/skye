"""OpenAI embedding provider implementation.

This module provides the OpenAIEmbeddingProvider class for generating embeddings
using OpenAI's embedding models.

Example:
    >>> from nimbus.models.embeddings import OpenAIEmbeddingProvider
    >>>
    >>> embedder = OpenAIEmbeddingProvider(
    ...     model="text-embedding-3-small",
    ...     api_key="sk-..."
    ... )
    >>> vector = embedder.encode("Hello, world!")
    >>> vectors = embedder.encode_batch(["text1", "text2"])
"""

from typing import Any

from nimbus.models.base import BaseEmbeddingProvider
from nimbus.models.lazy_import import LazyImporter


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider implementation.
    
    Supports OpenAI's embedding models:
    - text-embedding-3-small (1536 dimensions)
    - text-embedding-3-large (3072 dimensions)
    - text-embedding-ada-002 (1536 dimensions)
    
    Example:
        >>> embedder = OpenAIEmbeddingProvider(
        ...     model="text-embedding-3-small",
        ...     api_key="sk-..."
        ... )
        >>> vector = embedder.encode("Hello")
        >>> vectors = embedder.encode_batch(["text1", "text2"])
    """
    
    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(self, model: str, api_key: str, **config: Any) -> None:
        """Initialize OpenAI embedding provider.
        
        Args:
            model: Model identifier (e.g., 'text-embedding-3-small')
            api_key: OpenAI API key
            **config: Additional configuration parameters
        """
        super().__init__(model=model, api_key=api_key, **config)
        self.api_key = api_key
    
    def _initialize_client(self) -> Any:
        """Initialize OpenAI client.
        
        Returns:
            OpenAI client instance
        """
        openai = LazyImporter.import_module("openai", install_extra="openai")
        return openai.OpenAI(api_key=self.api_key)
    
    def _encode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors using OpenAI API.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    async def _aencode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors asynchronously.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        # Import AsyncOpenAI for async support
        openai = LazyImporter.import_module("openai", install_extra="openai")
        async_client = openai.AsyncOpenAI(api_key=self.api_key)
        
        response = await async_client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def get_vector_dimension(self) -> int:
        """Return the dimension of vectors produced by this model.
        
        Returns:
            The vector dimension size
        """
        if self.model not in self.MODEL_DIMENSIONS:
            raise ValueError(f"Unknown model: {self.model}")
        return self.MODEL_DIMENSIONS[self.model]
