"""Unit tests for Bedrock embedding provider.

Tests cover:
- Client initialization
- Batch encoding
- Vector dimensions
- Optional boto3 import
- Error handling
"""

import json
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from nimbus.providers.embeddings.bedrock_embeddings import BedrockEmbeddingProvider


class TestBedrockEmbeddingProviderInitialization:
    """Test Bedrock embedding provider initialization."""
    
    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        provider = BedrockEmbeddingProvider(
            model="amazon.titan-embed-text-v1",
            region_name="us-east-1"
        )
        assert provider.model == "amazon.titan-embed-text-v1"
        assert provider.region_name == "us-east-1"
    
    def test_init_with_additional_config(self) -> None:
        """Test initialization with additional configuration."""
        provider = BedrockEmbeddingProvider(
            model="amazon.titan-embed-text-v2:0",
            region_name="us-west-2",
            profile_name="custom-profile"
        )
        assert provider.model == "amazon.titan-embed-text-v2:0"
        assert provider.region_name == "us-west-2"
        assert provider.config["profile_name"] == "custom-profile"
    
    @patch("nimbus.providers.embeddings.bedrock_embeddings.LazyImporter.is_available")
    @patch("nimbus.providers.embeddings.bedrock_embeddings.LazyImporter.import_module")
    def test_lazy_client_initialization_with_lazy_import(
        self, mock_import: Mock, mock_is_available: Mock
    ) -> None:
        """Test client initialization using lazy import."""
        mock_is_available.return_value = False
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_import.return_value = mock_boto3
        
        provider = BedrockEmbeddingProvider(
            model="amazon.titan-embed-text-v1",
            region_name="us-east-1"
        )
        
        # Client should not be initialized yet
        mock_import.assert_not_called()
        
        # Access client to trigger initialization
        _ = provider.client
        
        # Now it should be initialized
        mock_import.assert_called_once_with("boto3", install_extra="bedrock")
        mock_boto3.client.assert_called_once_with(
            "bedrock-runtime",
            region_name="us-east-1"
        )
    
    @patch("nimbus.providers.embeddings.bedrock_embeddings.LazyImporter.is_available")
    @patch("nimbus.providers.embeddings.bedrock_embeddings.LazyImporter.import_module")
    def test_lazy_client_initialization_with_preinstalled_boto3(
        self, mock_import: Mock, mock_is_available: Mock
    ) -> None:
        """Test client initialization using pre-installed boto3."""
        mock_is_available.return_value = True
        
        # When is_available returns True, import_module should not be called
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        
        # We need to mock the import statement inside the method
        with patch("builtins.__import__") as mock_builtin_import:
            mock_builtin_import.return_value = mock_boto3
            mock_boto3.client.return_value = mock_client
            
            provider = BedrockEmbeddingProvider(
                model="amazon.titan-embed-text-v1",
                region_name="us-east-1"
            )
            
            # Access client to trigger initialization
            _ = provider.client
            
            # is_available should have been called
            mock_is_available.assert_called_once_with("boto3")
            
            # import_module should NOT have been called since is_available returned True
            mock_import.assert_not_called()


class TestBedrockEmbeddingProviderBatchEncoding:
    """Test batch encoding functionality."""
    
    @patch("nimbus.providers.embeddings.bedrock_embeddings.LazyImporter.is_available")
    @patch("nimbus.providers.embeddings.bedrock_embeddings.LazyImporter.import_module")
    def test_encode_batch(self, mock_import: Mock, mock_is_available: Mock) -> None:
        """Test batch encoding."""
        mock_is_available.return_value = False
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_import.return_value = mock_boto3
        
        # Mock responses for each text
        responses = [
            {
                "body": BytesIO(json.dumps({"embedding": [0.1, 0.2, 0.3]}).encode())
            },
            {
                "body": BytesIO(json.dumps({"embedding": [0.4, 0.5, 0.6]}).encode())
            }
        ]
        mock_client.invoke_model.side_effect = responses
        
        # Test
        provider = BedrockEmbeddingProvider(
            model="amazon.titan-embed-text-v1",
            region_name="us-east-1"
        )
        
        result = provider.encode_batch(["text1", "text2"])
        
        # Verify
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        
        assert mock_client.invoke_model.call_count == 2
    
    @patch("nimbus.providers.embeddings.bedrock_embeddings.LazyImporter.is_available")
    @patch("nimbus.providers.embeddings.bedrock_embeddings.LazyImporter.import_module")
    def test_encode_single_text(self, mock_import: Mock, mock_is_available: Mock) -> None:
        """Test encoding single text."""
        mock_is_available.return_value = False
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_import.return_value = mock_boto3
        
        # Mock response
        mock_response = {
            "body": BytesIO(json.dumps({"embedding": [0.1, 0.2, 0.3]}).encode())
        }
        mock_client.invoke_model.return_value = mock_response
        
        # Test
        provider = BedrockEmbeddingProvider(
            model="amazon.titan-embed-text-v1",
            region_name="us-east-1"
        )
        
        result = provider.encode("hello")
        
        # Verify
        assert result == [0.1, 0.2, 0.3]
        
        mock_client.invoke_model.assert_called_once()


class TestBedrockEmbeddingProviderVectorDimensions:
    """Test vector dimension retrieval."""
    
    def test_get_vector_dimension_v1(self) -> None:
        """Test vector dimension for amazon.titan-embed-text-v1."""
        provider = BedrockEmbeddingProvider(
            model="amazon.titan-embed-text-v1",
            region_name="us-east-1"
        )
        assert provider.get_vector_dimension() == 1536
    
    def test_get_vector_dimension_v2(self) -> None:
        """Test vector dimension for amazon.titan-embed-text-v2:0."""
        provider = BedrockEmbeddingProvider(
            model="amazon.titan-embed-text-v2:0",
            region_name="us-east-1"
        )
        assert provider.get_vector_dimension() == 1024
    
    def test_get_vector_dimension_unknown_model(self) -> None:
        """Test vector dimension for unknown model."""
        provider = BedrockEmbeddingProvider(
            model="unknown-model",
            region_name="us-east-1"
        )
        with pytest.raises(ValueError, match="Unknown model"):
            provider.get_vector_dimension()
