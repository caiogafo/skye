"""Unit tests for Google embedding provider.

Tests cover:
- Client initialization
- Batch encoding
- Vector dimensions
- Error handling
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from nimbus.models.embeddings.google_embeddings import GoogleEmbeddingProvider


class TestGoogleEmbeddingProviderInitialization:
    """Test Google embedding provider initialization."""
    
    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        provider = GoogleEmbeddingProvider(
            model="text-embedding-004",
            project_id="my-project",
            location="us-central1"
        )
        assert provider.model == "text-embedding-004"
        assert provider.project_id == "my-project"
        assert provider.location == "us-central1"
    
    def test_init_with_additional_config(self) -> None:
        """Test initialization with additional configuration."""
        provider = GoogleEmbeddingProvider(
            model="text-multilingual-embedding-002",
            project_id="my-project",
            location="us-west1",
            credentials_path="/path/to/creds.json"
        )
        assert provider.model == "text-multilingual-embedding-002"
        assert provider.project_id == "my-project"
        assert provider.location == "us-west1"
        assert provider.config["credentials_path"] == "/path/to/creds.json"
    
    @patch("nimbus.models.embeddings.google_embeddings.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_aiplatform = MagicMock()
        mock_model = MagicMock()
        mock_aiplatform.TextEmbeddingModel.from_pretrained.return_value = mock_model
        mock_import.return_value = mock_aiplatform
        
        provider = GoogleEmbeddingProvider(
            model="text-embedding-004",
            project_id="my-project",
            location="us-central1"
        )
        
        # Client should not be initialized yet
        mock_import.assert_not_called()
        
        # Access client to trigger initialization
        _ = provider.client
        
        # Now it should be initialized
        mock_import.assert_called_once_with(
            "google.cloud.aiplatform",
            package_name="google-cloud-aiplatform",
            install_extra="google"
        )
        mock_aiplatform.init.assert_called_once_with(
            project="my-project",
            location="us-central1"
        )
        mock_aiplatform.TextEmbeddingModel.from_pretrained.assert_called_once_with(
            "text-embedding-004"
        )


class TestGoogleEmbeddingProviderBatchEncoding:
    """Test batch encoding functionality."""
    
    @patch("nimbus.models.embeddings.google_embeddings.LazyImporter.import_module")
    def test_encode_batch(self, mock_import: Mock) -> None:
        """Test batch encoding."""
        # Setup mock
        mock_aiplatform = MagicMock()
        mock_model = MagicMock()
        mock_aiplatform.TextEmbeddingModel.from_pretrained.return_value = mock_model
        mock_import.return_value = mock_aiplatform
        
        # Mock embeddings
        mock_embedding_1 = MagicMock()
        mock_embedding_1.values = [0.1, 0.2, 0.3]
        mock_embedding_2 = MagicMock()
        mock_embedding_2.values = [0.4, 0.5, 0.6]
        
        mock_model.get_embeddings.return_value = [mock_embedding_1, mock_embedding_2]
        
        # Test
        provider = GoogleEmbeddingProvider(
            model="text-embedding-004",
            project_id="my-project",
            location="us-central1"
        )
        
        result = provider.encode_batch(["text1", "text2"])
        
        # Verify
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        
        mock_model.get_embeddings.assert_called_once_with(["text1", "text2"])
    
    @patch("nimbus.models.embeddings.google_embeddings.LazyImporter.import_module")
    def test_encode_single_text(self, mock_import: Mock) -> None:
        """Test encoding single text."""
        # Setup mock
        mock_aiplatform = MagicMock()
        mock_model = MagicMock()
        mock_aiplatform.TextEmbeddingModel.from_pretrained.return_value = mock_model
        mock_import.return_value = mock_aiplatform
        
        # Mock embedding
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3]
        
        mock_model.get_embeddings.return_value = [mock_embedding]
        
        # Test
        provider = GoogleEmbeddingProvider(
            model="text-embedding-004",
            project_id="my-project",
            location="us-central1"
        )
        
        result = provider.encode("hello")
        
        # Verify
        assert result == [0.1, 0.2, 0.3]
        
        mock_model.get_embeddings.assert_called_once_with(["hello"])


class TestGoogleEmbeddingProviderVectorDimensions:
    """Test vector dimension retrieval."""
    
    def test_get_vector_dimension_text_embedding_004(self) -> None:
        """Test vector dimension for text-embedding-004."""
        provider = GoogleEmbeddingProvider(
            model="text-embedding-004",
            project_id="my-project",
            location="us-central1"
        )
        assert provider.get_vector_dimension() == 768
    
    def test_get_vector_dimension_multilingual(self) -> None:
        """Test vector dimension for text-multilingual-embedding-002."""
        provider = GoogleEmbeddingProvider(
            model="text-multilingual-embedding-002",
            project_id="my-project",
            location="us-central1"
        )
        assert provider.get_vector_dimension() == 768
    
    def test_get_vector_dimension_unknown_model(self) -> None:
        """Test vector dimension for unknown model."""
        provider = GoogleEmbeddingProvider(
            model="unknown-model",
            project_id="my-project",
            location="us-central1"
        )
        with pytest.raises(ValueError, match="Unknown model"):
            provider.get_vector_dimension()
