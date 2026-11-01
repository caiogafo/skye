"""Google Vertex AI multimodal embedding provider implementation.

This module provides the VertexMultimodalEmbeddingProvider class for generating
embeddings from text and images using Google Vertex AI's multimodal embedding model.

Example:
    >>> from nimbus.models.embeddings import VertexMultimodalEmbeddingProvider
    >>>
    >>> embedder = VertexMultimodalEmbeddingProvider(
    ...     project_id="my-project",
    ...     location="us-central1"
    ... )
    >>> # Text embedding
    >>> vector = embedder.encode("Hello, world!")
    >>> # Image embedding
    >>> vector = embedder.encode("path/to/image.jpg")
    >>> # Batch with mixed content
    >>> vectors = embedder.encode_batch(["text1", "path/to/image.jpg"])
"""

from typing import Any, Union

from nimbus.models.base import BaseEmbeddingProvider
from nimbus.models.lazy_import import LazyImporter
from nimbus.models.transport.multimodal import ImageHandler


class VertexMultimodalEmbeddingProvider(BaseEmbeddingProvider):
    """Google Vertex AI multimodal embedding provider implementation.
    
    Supports Vertex AI's multimodal embedding model:
    - multimodalembedding@001 (1408 dimensions)
    
    This provider can encode both text and images into the same vector space,
    enabling cross-modal retrieval and similarity search.
    
    Example:
        >>> embedder = VertexMultimodalEmbeddingProvider(
        ...     project_id="my-project",
        ...     location="us-central1"
        ... )
        >>> # Text embedding
        >>> text_vector = embedder.encode("Hello")
        >>> # Image embedding
        >>> image_vector = embedder.encode("path/to/image.jpg")
        >>> # Batch encoding
        >>> vectors = embedder.encode_batch(["text1", "image.jpg"])
    """
    
    # Model dimensions
    VECTOR_DIMENSION = 1408
    MODEL_NAME = "multimodalembedding@001"
    
    def __init__(
        self,
        project_id: str,
        location: str,
        **config: Any
    ) -> None:
        """Initialize Vertex AI multimodal embedding provider.
        
        Args:
            project_id: Google Cloud project ID
            location: Region location (e.g., 'us-central1')
            **config: Additional configuration parameters
        """
        super().__init__(
            model=self.MODEL_NAME,
            project_id=project_id,
            location=location,
            **config
        )
        self.project_id = project_id
        self.location = location
    
    def _initialize_client(self) -> Any:
        """Initialize Vertex AI client.
        
        Returns:
            Vertex AI MultimodalEmbeddingModel instance
        """
        aiplatform = LazyImporter.import_module(
            "google.cloud.aiplatform",
            package_name="google-cloud-aiplatform",
            install_extra="vertex"
        )
        
        aiplatform.init(project=self.project_id, location=self.location)
        return aiplatform.MultimodalEmbeddingModel.from_pretrained(self.MODEL_NAME)
    
    def _encode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts/images to vectors.
        
        Each item in texts can be:
        - Plain text string
        - File path to an image
        - URL to an image
        - Base64-encoded image data
        
        Args:
            texts: List of texts or image paths to encode
            
        Returns:
            List of vector representations
        """
        embeddings = []
        
        for item in texts:
            # Try to detect if it's an image
            if self._is_image_input(item):
                # Process as image
                embedding = self._encode_image(item)
            else:
                # Process as text
                embedding = self._encode_text(item)
            
            embeddings.append(embedding)
        
        return embeddings
    
    def _is_image_input(self, item: str) -> bool:
        """Detect if input is an image.
        
        Args:
            item: Input string to check
            
        Returns:
            True if input appears to be an image, False otherwise
        """
        # Check for image file extensions
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        item_lower = item.lower()
        
        # Check file extension
        for ext in image_extensions:
            if item_lower.endswith(ext):
                return True
        
        # Check for URLs
        if item.startswith("http://") or item.startswith("https://"):
            # Could be image URL, check common patterns
            if any(ext in item_lower for ext in image_extensions):
                return True
        
        # Check for base64 image data
        if item.startswith("data:image/"):
            return True
        
        return False
    
    def _encode_text(self, text: str) -> list[float]:
        """Encode text to vector.
        
        Args:
            text: Text to encode
            
        Returns:
            Vector representation
        """
        response = self.client.get_embeddings(texts=[text])
        return response[0].text_embedding
    
    def _encode_image(self, image_input: Union[str]) -> list[float]:
        """Encode image to vector.
        
        Args:
            image_input: Image path, URL, or base64 data
            
        Returns:
            Vector representation
        """
        # Process image using ImageHandler
        processed_image = ImageHandler.process_image(image_input)
        
        # Extract image data for Vertex API
        if processed_image["type"] == "image_url":
            url = processed_image["image_url"]["url"]
            
            # If it's a data URL, we need to convert it
            if url.startswith("data:"):
                # Extract base64 data
                parts = url.split(",", 1)
                base64_data = parts[1]
                
                # Use Vertex API with base64 image
                from google.cloud.aiplatform.gapic.types import content
                
                image_data = content.Blob(
                    mime_type="image/jpeg",
                    data=base64_data.encode()
                )
                response = self.client.get_embeddings(images=[image_data])
            else:
                # Use URL directly
                response = self.client.get_embeddings(image_urls=[url])
        else:
            response = self.client.get_embeddings(image_urls=[image_input])
        
        return response[0].image_embedding
    
    def get_vector_dimension(self) -> int:
        """Return the dimension of vectors produced by this model.
        
        Returns:
            The vector dimension size (1408 for multimodalembedding@001)
        """
        return self.VECTOR_DIMENSION
