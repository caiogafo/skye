"""AWS Bedrock embedding provider implementation.

This module provides the BedrockEmbeddingProvider class for generating embeddings
using AWS Bedrock's embedding models.

Example:
    >>> from nimbus.models.embeddings import BedrockEmbeddingProvider
    >>>
    >>> embedder = BedrockEmbeddingProvider(
    ...     model="amazon.titan-embed-text-v1",
    ...     region_name="us-east-1"
    ... )
    >>> vector = embedder.encode("Hello, world!")
    >>> vectors = embedder.encode_batch(["text1", "text2"])
"""

from typing import Any

from nimbus.models.base import BaseEmbeddingProvider
from nimbus.models.lazy_import import LazyImporter


class BedrockEmbeddingProvider(BaseEmbeddingProvider):
    """AWS Bedrock embedding provider implementation.
    
    Supports AWS Bedrock's embedding models:
    - amazon.titan-embed-text-v1 (1536 dimensions)
    - amazon.titan-embed-text-v2:0 (1024 dimensions)
    
    Note: boto3 is optional and may be pre-installed in AWS Lambda environments.
    
    Example:
        >>> embedder = BedrockEmbeddingProvider(
        ...     model="amazon.titan-embed-text-v1",
        ...     region_name="us-east-1"
        ... )
        >>> vector = embedder.encode("Hello")
        >>> vectors = embedder.encode_batch(["text1", "text2"])
    """


    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "amazon.titan-embed-text-v1": 1536,
        "amazon.titan-embed-text-v2:0": 1024,
    }
    
    def __init__(self, model: str, region_name: str, **config: Any) -> None:
        """Initialize Bedrock embedding provider.
        
        Args:
            model: Model identifier (e.g., 'amazon.titan-embed-text-v1')
            region_name: AWS region name
            **config: Additional configuration parameters (e.g., profile_name)
        """
        super().__init__(model=model, region_name=region_name, **config)
        self.region_name = region_name
    
    def _initialize_client(self) -> Any:
        """Initialize Bedrock client.
        
        Attempts to use pre-installed boto3 (e.g., in Lambda), falls back to
        lazy import if not available.
        
        Returns:
            Bedrock runtime client instance
        """
        # Try to use pre-installed boto3 first (e.g., in Lambda)
        if LazyImporter.is_available("boto3"):
            import boto3
            return boto3.client("bedrock-runtime", region_name=self.region_name)
        
        # Fall back to lazy import
        boto3 = LazyImporter.import_module("boto3", install_extra="bedrock")
        return boto3.client("bedrock-runtime", region_name=self.region_name)
    
    def _encode_batch_impl(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts to vectors using Bedrock API.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of vector representations
        """
        embeddings = []
        
        for text in texts:
            # Bedrock Titan embeddings API expects individual requests
            response = self.client.invoke_model(
                modelId=self.model,
                body=f'{{"inputText": "{text}"}}'
            )
            
            # Parse response
            import json
            response_body = json.loads(response["body"].read())
            embeddings.append(response_body["embedding"])
        
        return embeddings
    
    def get_vector_dimension(self) -> int:
        """Return the dimension of vectors produced by this model.
        
        Returns:
            The vector dimension size
        """
        if self.model not in self.MODEL_DIMENSIONS:
            raise ValueError(f"Unknown model: {self.model}")
        return self.MODEL_DIMENSIONS[self.model]
