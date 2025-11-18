"""Google Vertex AI embedding provider implementation.

This module provides the VertexEmbeddingProvider class for generating embeddings
using Google Vertex AI's embedding models.

Example:
    >>> from nimbus.providers.embeddings import VertexEmbeddingProvider
    >>>
    >>> embedder = VertexEmbeddingProvider(
    ...     model="text-embedding-004",
    ...     project_id="my-project",
    ...     location="us-central1"
    ... )
    >>> vector = embedder.encode("Hello, world!")
    >>> vectors = embedder.encode_batch(["text1", "text2"])
"""

from typing import Any

from nimbus.providers.base import BaseEmbeddingProvider
from nimbus.providers.lazy_import import LazyImporter


class VertexEmbeddingProvider(BaseEmbeddingProvider):
    """Google Vertex AI embedding provider implementation.
    
    Supports Vertex AI's embedding models:
    - text-embedding-004 (768 dimensions)
    - text-multilingual-embedding-002 (768 dimensions)
    
    Example:
        >>> embedder = VertexEmbeddingProvider(
        ...     model="text-embedding-004",
        ...     project_id="my-project",
        ...     location="us-central1"
        ... )
        >>> vector = embedder.encode("Hello")
        >>> vectors = embedder.encode_batch(["text1", "text2"])
    """
    
    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "text-embedding-004": 768,
        "text-multilingual-embedding-002": 768,
    }
    
    def __init__(
        self,
        model: str,
        project_id: str,
        location: str,
        **config: Any
    ) -> None:
        """Initialize Vertex AI embedding provider.
        
        Args:
            model: Model identifier (e.g., 'text-embedding-004')
            project_id: Google Cloud project ID
            location: Region location (e.g., 'us-central1')
            **config: Additional configuration parameters
        """
        super().__init__(model=model, project_id=project_id, location=location, **config)
        self.project_id = project_id
        self.location = location
    
    def _initialize_client(self) -> Any:
        """Initialize Vertex AI client.
        
        Returns:
            Vertex AI TextEmbeddingModel instance
        """
        aiplatform = LazyImporter.import_module(
            "google.cloud.aiplatform",
            package_name="google-cloud-aiplatform",
            install_extra="vertex"
        )
        
        aiplatform.init(project=self.project_id, location=self.location)
        return aiplatform.TextEmbeddingModel.from_pretrained(self.model)
    
    def _encode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors using Vertex AI API.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        embeddings = self.client.get_embeddings(texts)
        return [embedding.values for embedding in embeddings]
    
    def get_vector_dimension(self) -> int:
        """Return the dimension of vectors produced by this model.
        
        Returns:
            The vector dimension size
        """
        if self.model not in self.MODEL_DIMENSIONS:
            raise ValueError(f"Unknown model: {self.model}")
        return self.MODEL_DIMENSIONS[self.model]
