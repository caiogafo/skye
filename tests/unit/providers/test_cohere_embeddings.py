"""Unit tests for Cohere embedding provider.

Tests cover:
- Client initialization
- Batch encoding
- Vector dimensions
- Error handling
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from nimbus.providers.embeddings.cohere_embeddings import CohereEmbeddingProvider


class TestCohereEmbeddingProviderInitialization:
    """Test Cohere embedding provider initialization."""
    
    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        provider = CohereEmbeddingProvider(
            model="embed-english-v3.0",
            api_key="cohere-key"
        )
        assert provider.model == "embed-english-v3.0"
        assert provider.api_key == "cohere-key"
    
    def test_init_with_additional_config(self) -> None:
        """Test initialization with additional configuration."""
        provider = CohereEmbeddingProvider(
            model="embed-multilingual-v3.0",
            api_key="cohere-key",
            timeout=30
        )
        assert provider.model == "embed-multilingual-v3.0"
        assert provider.api_key == "cohere-key"
        assert provider.config["timeout"] == 30
    
    @patch("nimbus.providers.embeddings.cohere_embeddings.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_cohere = MagicMock()
        mock_import.return_value = mock_cohere
        
        provider = CohereEmbeddingProvider(
            model="embed-english-v3.0",
            api_key="cohere-key"
        )
        
        # Client should not be initialized yet
        mock_import.assert_not_called()
        
        # Access client to trigger initialization
        _ = provider.client
        
        # Now it should be initialized
        mock_import.assert_called_once_with("cohere", install_extra="cohere")
        mock_cohere.ClientV2.assert_called_once_with(api_key="cohere-key")


class TestCohereEmbeddingProviderBatchEncoding:
    """Test batch encoding functionality."""
    
    @patch("nimbus.providers.embeddings.cohere_embeddings.LazyImporter.import_module")
    def test_encode_batch(self, mock_import: Mock) -> None:
        """Test batch encoding."""
        # Setup mock
        mock_cohere = MagicMock()
        mock_client = MagicMock()
        mock_cohere.ClientV2.return_value = mock_client
        mock_import.return_value = mock_cohere
        
        # Mock response
        mock_response = MagicMock()
        mock_response.embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        
        mock_client.embed.return_value = mock_response
        
        # Test
        provider = CohereEmbeddingProvider(
            model="embed-english-v3.0",
            api_key="cohere-key"
        )
        
        result = provider.encode_batch(["text1", "text2"])
        
        # Verify
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        
        mock_client.embed.assert_called_once_with(
            model="embed-english-v3.0",
            texts=["text1", "text2"],
            input_type="search_document"
        )
    
    @patch("nimbus.providers.embeddings.cohere_embeddings.LazyImporter.import_module")
    def test_encode_single_text(self, mock_import: Mock) -> None:
        """Test encoding single text."""
        # Setup mock
        mock_cohere = MagicMock()
        mock_client = MagicMock()
        mock_cohere.ClientV2.return_value = mock_client
        mock_import.return_value = mock_cohere
        
        # Mock response
        mock_response = MagicMock()
        mock_response.embeddings = [[0.1, 0.2, 0.3]]
        
        mock_client.embed.return_value = mock_response
        
        # Test
        provider = CohereEmbeddingProvider(
            model="embed-english-v3.0",
            api_key="cohere-key"
        )
        
        result = provider.encode("hello")
        
        # Verify
        assert result == [0.1, 0.2, 0.3]
        
        mock_client.embed.assert_called_once_with(
            model="embed-english-v3.0",
            texts=["hello"],
            input_type="search_document"
        )


class TestCohereEmbeddingProviderVectorDimensions:
    """Test vector dimension retrieval."""
    
    def test_get_vector_dimension_english_v3(self) -> None:
        """Test vector dimension for embed-english-v3.0."""
        provider = CohereEmbeddingProvider(
            model="embed-english-v3.0",
            api_key="cohere-key"
        )
        assert provider.get_vector_dimension() == 1024
    
    def test_get_vector_dimension_english_light_v3(self) -> None:
        """Test vector dimension for embed-english-light-v3.0."""
        provider = CohereEmbeddingProvider(
            model="embed-english-light-v3.0",
            api_key="cohere-key"
        )
        assert provider.get_vector_dimension() == 384
    
    def test_get_vector_dimension_multilingual_v3(self) -> None:
        """Test vector dimension for embed-multilingual-v3.0."""
        provider = CohereEmbeddingProvider(
            model="embed-multilingual-v3.0",
            api_key="cohere-key"
        )
        assert provider.get_vector_dimension() == 1024
    
    def test_get_vector_dimension_unknown_model(self) -> None:
        """Test vector dimension for unknown model."""
        provider = CohereEmbeddingProvider(
            model="unknown-model",
            api_key="cohere-key"
        )
        with pytest.raises(ValueError, match="Unknown model"):
            provider.get_vector_dimension()
