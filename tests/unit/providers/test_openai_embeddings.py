"""Unit tests for OpenAI embedding provider.

Tests cover:
- Client initialization
- Batch encoding
- Async batch encoding
- Vector dimensions
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from nimbus.models.embeddings.openai_embeddings import OpenAIEmbeddingProvider


class TestOpenAIEmbeddingProviderInitialization:
    """Test OpenAI embedding provider initialization."""
    
    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-small",
            api_key="sk-test"
        )
        assert provider.model == "text-embedding-3-small"
        assert provider.api_key == "sk-test"
    
    def test_init_with_additional_config(self) -> None:
        """Test initialization with additional configuration."""
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-large",
            api_key="sk-test",
            organization="org-123"
        )
        assert provider.model == "text-embedding-3-large"
        assert provider.api_key == "sk-test"
        assert provider.config["organization"] == "org-123"
    
    @patch("nimbus.models.embeddings.openai_embeddings.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-small",
            api_key="sk-test"
        )
        
        # Client should not be initialized yet
        mock_import.assert_not_called()
        
        # Access client to trigger initialization
        _ = provider.client
        
        # Now it should be initialized
        mock_import.assert_called_once_with("openai", install_extra="openai")
        mock_openai.OpenAI.assert_called_once_with(api_key="sk-test")


class TestOpenAIEmbeddingProviderBatchEncoding:
    """Test batch encoding functionality."""
    
    @patch("nimbus.models.embeddings.openai_embeddings.LazyImporter.import_module")
    def test_encode_batch(self, mock_import: Mock) -> None:
        """Test batch encoding."""
        # Setup mock
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_import.return_value = mock_openai
        
        # Mock response
        mock_embedding_1 = MagicMock()
        mock_embedding_1.embedding = [0.1, 0.2, 0.3]
        mock_embedding_2 = MagicMock()
        mock_embedding_2.embedding = [0.4, 0.5, 0.6]
        
        mock_response = MagicMock()
        mock_response.data = [mock_embedding_1, mock_embedding_2]
        
        mock_client.embeddings.create.return_value = mock_response
        
        # Test
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-small",
            api_key="sk-test"
        )
        
        result = provider.encode_batch(["text1", "text2"])
        
        # Verify
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input=["text1", "text2"]
        )
    
    @patch("nimbus.models.embeddings.openai_embeddings.LazyImporter.import_module")
    def test_encode_single_text(self, mock_import: Mock) -> None:
        """Test encoding single text."""
        # Setup mock
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_import.return_value = mock_openai
        
        # Mock response
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1, 0.2, 0.3]
        
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]
        
        mock_client.embeddings.create.return_value = mock_response
        
        # Test
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-small",
            api_key="sk-test"
        )
        
        result = provider.encode("hello")
        
        # Verify
        assert result == [0.1, 0.2, 0.3]
        
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input=["hello"]
        )


class TestOpenAIEmbeddingProviderAsyncEncoding:
    """Test async encoding functionality."""
    
    @patch("nimbus.models.embeddings.openai_embeddings.LazyImporter.import_module")
    @pytest.mark.asyncio
    async def test_aencode_batch(self, mock_import: Mock) -> None:
        """Test async batch encoding."""
        # Setup mock
        mock_openai = MagicMock()
        mock_async_client = AsyncMock()
        mock_openai.AsyncOpenAI.return_value = mock_async_client
        mock_import.return_value = mock_openai
        
        # Mock response
        mock_embedding_1 = MagicMock()
        mock_embedding_1.embedding = [0.1, 0.2, 0.3]
        mock_embedding_2 = MagicMock()
        mock_embedding_2.embedding = [0.4, 0.5, 0.6]
        
        mock_response = MagicMock()
        mock_response.data = [mock_embedding_1, mock_embedding_2]
        
        mock_async_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # Test
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-small",
            api_key="sk-test"
        )
        
        result = await provider.aencode_batch(["text1", "text2"])
        
        # Verify
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        
        mock_async_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input=["text1", "text2"]
        )
    
    @patch("nimbus.models.embeddings.openai_embeddings.LazyImporter.import_module")
    @pytest.mark.asyncio
    async def test_aencode_single_text(self, mock_import: Mock) -> None:
        """Test async encoding single text."""
        # Setup mock
        mock_openai = MagicMock()
        mock_async_client = AsyncMock()
        mock_openai.AsyncOpenAI.return_value = mock_async_client
        mock_import.return_value = mock_openai
        
        # Mock response
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1, 0.2, 0.3]
        
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]
        
        mock_async_client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # Test
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-small",
            api_key="sk-test"
        )
        
        result = await provider.aencode("hello")
        
        # Verify
        assert result == [0.1, 0.2, 0.3]


class TestOpenAIEmbeddingProviderVectorDimensions:
    """Test vector dimension retrieval."""
    
    def test_get_vector_dimension_small(self) -> None:
        """Test vector dimension for text-embedding-3-small."""
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-small",
            api_key="sk-test"
        )
        assert provider.get_vector_dimension() == 1536
    
    def test_get_vector_dimension_large(self) -> None:
        """Test vector dimension for text-embedding-3-large."""
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-large",
            api_key="sk-test"
        )
        assert provider.get_vector_dimension() == 3072
    
    def test_get_vector_dimension_ada(self) -> None:
        """Test vector dimension for text-embedding-ada-002."""
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-ada-002",
            api_key="sk-test"
        )
        assert provider.get_vector_dimension() == 1536
    
    def test_get_vector_dimension_unknown_model(self) -> None:
        """Test vector dimension for unknown model."""
        provider = OpenAIEmbeddingProvider(
            model="unknown-model",
            api_key="sk-test"
        )
        with pytest.raises(ValueError, match="Unknown model"):
            provider.get_vector_dimension()
