"""Unit tests for Google multimodal embedding provider.

Tests cover:
- Client initialization
- Text encoding
- Image encoding
- Batch encoding with mixed content
- Vector dimensions
- Image input detection
- Error handling
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from nimbus.models.embeddings.google_multimodal_embeddings import (
    GoogleMultimodalEmbeddingProvider,
)


class TestGoogleMultimodalEmbeddingProviderInitialization:
    """Test Google multimodal embedding provider initialization."""
    
    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider.model == "multimodalembedding@001"
        assert provider.project_id == "my-project"
        assert provider.location == "us-central1"
    
    def test_init_with_additional_config(self) -> None:
        """Test initialization with additional configuration."""
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-west1",
            credentials_path="/path/to/creds.json"
        )
        assert provider.model == "multimodalembedding@001"
        assert provider.project_id == "my-project"
        assert provider.location == "us-west1"
        assert provider.config["credentials_path"] == "/path/to/creds.json"
    
    @patch("nimbus.models.embeddings.google_multimodal_embeddings.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_aiplatform = MagicMock()
        mock_model = MagicMock()
        mock_aiplatform.MultimodalEmbeddingModel.from_pretrained.return_value = mock_model
        mock_import.return_value = mock_aiplatform
        
        provider = GoogleMultimodalEmbeddingProvider(
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
        mock_aiplatform.MultimodalEmbeddingModel.from_pretrained.assert_called_once_with(
            "multimodalembedding@001"
        )


class TestGoogleMultimodalEmbeddingProviderImageDetection:
    """Test image input detection."""
    
    def test_is_image_input_jpg_file(self) -> None:
        """Test detection of JPG file."""
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider._is_image_input("image.jpg") is True
        assert provider._is_image_input("path/to/image.JPG") is True
    
    def test_is_image_input_png_file(self) -> None:
        """Test detection of PNG file."""
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider._is_image_input("image.png") is True
        assert provider._is_image_input("path/to/image.PNG") is True
    
    def test_is_image_input_image_url(self) -> None:
        """Test detection of image URL."""
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider._is_image_input("https://example.com/image.jpg") is True
        assert provider._is_image_input("http://example.com/image.png") is True
    
    def test_is_image_input_base64_data(self) -> None:
        """Test detection of base64 image data."""
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider._is_image_input("data:image/jpeg;base64,/9j/4AAQSkZJRg==") is True
    
    def test_is_image_input_text(self) -> None:
        """Test that plain text is not detected as image."""
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider._is_image_input("Hello, world!") is False
        assert provider._is_image_input("This is some text") is False


class TestGoogleMultimodalEmbeddingProviderTextEncoding:
    """Test text encoding functionality."""
    
    @patch("nimbus.models.embeddings.google_multimodal_embeddings.LazyImporter.import_module")
    def test_encode_text(self, mock_import: Mock) -> None:
        """Test text encoding."""
        # Setup mock
        mock_aiplatform = MagicMock()
        mock_model = MagicMock()
        mock_aiplatform.MultimodalEmbeddingModel.from_pretrained.return_value = mock_model
        mock_import.return_value = mock_aiplatform
        
        # Mock response
        mock_embedding = MagicMock()
        mock_embedding.text_embedding = [0.1, 0.2, 0.3]
        
        mock_model.get_embeddings.return_value = [mock_embedding]
        
        # Test
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        
        result = provider._encode_text("hello")
        
        # Verify
        assert result == [0.1, 0.2, 0.3]
        mock_model.get_embeddings.assert_called_once_with(texts=["hello"])


class TestGoogleMultimodalEmbeddingProviderBatchEncoding:
    """Test batch encoding functionality."""
    
    @patch("nimbus.models.embeddings.google_multimodal_embeddings.LazyImporter.import_module")
    def test_encode_batch_text_only(self, mock_import: Mock) -> None:
        """Test batch encoding with text only."""
        # Setup mock
        mock_aiplatform = MagicMock()
        mock_model = MagicMock()
        mock_aiplatform.MultimodalEmbeddingModel.from_pretrained.return_value = mock_model
        mock_import.return_value = mock_aiplatform
        
        # Mock responses
        mock_embedding_1 = MagicMock()
        mock_embedding_1.text_embedding = [0.1, 0.2, 0.3]
        mock_embedding_2 = MagicMock()
        mock_embedding_2.text_embedding = [0.4, 0.5, 0.6]
        
        mock_model.get_embeddings.side_effect = [
            [mock_embedding_1],
            [mock_embedding_2]
        ]
        
        # Test
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        
        result = provider.encode_batch(["text1", "text2"])
        
        # Verify
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
    
    @patch("nimbus.models.embeddings.google_multimodal_embeddings.ImageHandler.process_image")
    @patch("nimbus.models.embeddings.google_multimodal_embeddings.LazyImporter.import_module")
    def test_encode_batch_mixed_content(self, mock_import: Mock, mock_process_image: Mock) -> None:
        """Test batch encoding with mixed text and images."""
        # Setup mock
        mock_aiplatform = MagicMock()
        mock_model = MagicMock()
        mock_aiplatform.MultimodalEmbeddingModel.from_pretrained.return_value = mock_model
        mock_import.return_value = mock_aiplatform
        
        # Mock image processing
        mock_process_image.return_value = {
            "type": "image_url",
            "image_url": {"url": "https://example.com/image.jpg"}
        }
        
        # Mock responses
        mock_text_embedding = MagicMock()
        mock_text_embedding.text_embedding = [0.1, 0.2, 0.3]
        mock_image_embedding = MagicMock()
        mock_image_embedding.image_embedding = [0.4, 0.5, 0.6]
        
        mock_model.get_embeddings.side_effect = [
            [mock_text_embedding],
            [mock_image_embedding]
        ]
        
        # Test
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        
        result = provider.encode_batch(["hello", "image.jpg"])
        
        # Verify
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
    
    @patch("nimbus.models.embeddings.google_multimodal_embeddings.LazyImporter.import_module")
    def test_encode_single_text(self, mock_import: Mock) -> None:
        """Test encoding single text."""
        # Setup mock
        mock_aiplatform = MagicMock()
        mock_model = MagicMock()
        mock_aiplatform.MultimodalEmbeddingModel.from_pretrained.return_value = mock_model
        mock_import.return_value = mock_aiplatform
        
        # Mock response
        mock_embedding = MagicMock()
        mock_embedding.text_embedding = [0.1, 0.2, 0.3]
        
        mock_model.get_embeddings.return_value = [mock_embedding]
        
        # Test
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        
        result = provider.encode("hello")
        
        # Verify
        assert result == [0.1, 0.2, 0.3]


class TestGoogleMultimodalEmbeddingProviderVectorDimensions:
    """Test vector dimension retrieval."""
    
    def test_get_vector_dimension(self) -> None:
        """Test vector dimension for multimodalembedding@001."""
        provider = GoogleMultimodalEmbeddingProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider.get_vector_dimension() == 1408
