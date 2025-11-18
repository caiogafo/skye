"""Unit tests for Vertex AI provider implementation.

Tests cover:
- Client initialization
- Request transformation
- Response transformation
- Streaming
- Safety settings
- Grounding features
- Error handling
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from nimbus.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.exceptions import ProviderError
from nimbus.messages import AssistantMessage, SystemMessage, UserMessage
from nimbus.providers.llm.vertex_provider import VertexAIProvider


class TestVertexAIProviderInitialization:
    """Test Vertex AI provider initialization."""

    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider.project_id == "my-project"
        assert provider.location == "us-central1"
        assert provider.credentials is None

    def test_init_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        mock_creds = Mock()
        provider = VertexAIProvider(
            project_id="my-project",
            location="europe-west1",
            credentials=mock_creds
        )
        assert provider.project_id == "my-project"
        assert provider.location == "europe-west1"
        assert provider.credentials is mock_creds

    @patch("nimbus.providers.llm.vertex_provider.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_vertexai = MagicMock()
        mock_import.return_value = mock_vertexai

        provider = VertexAIProvider(
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
            install_extra="vertex"
        )
        mock_vertexai.init.assert_called_once_with(
            project="my-project",
            location="us-central1",
            credentials=None
        )


class TestVertexAIRequestTransformation:
    """Test request transformation to Vertex AI format."""

    def test_transform_basic_request(self) -> None:
        """Test transformation of basic completion request."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro",
            temperature=0.7
        )

        result = provider._transform_request(request)

        assert result["model"] == "gemini-1.5-pro"
        assert result["generation_config"]["temperature"] == 0.7
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["parts"][0]["text"] == "Hello"

    def test_transform_with_system_message(self) -> None:
        """Test transformation with system message."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[
                SystemMessage(content="You are helpful"),
                UserMessage(content="Hello")
            ],
            model="gemini-1.5-pro"
        )

        result = provider._transform_request(request)

        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "system"
        assert result["messages"][0]["parts"][0]["text"] == "You are helpful"
        assert result["messages"][1]["role"] == "user"

    def test_transform_with_max_tokens(self) -> None:
        """Test transformation with max_tokens parameter."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro",
            max_tokens=100
        )

        result = provider._transform_request(request)

        assert result["generation_config"]["max_output_tokens"] == 100

    def test_transform_with_stop_sequences(self) -> None:
        """Test transformation with stop sequences."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro",
            stop=["END", "STOP"]
        )

        result = provider._transform_request(request)

        assert result["generation_config"]["stop_sequences"] == ["END", "STOP"]

    def test_transform_with_safety_settings(self) -> None:
        """Test transformation with safety settings."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro",
            metadata={"safety_settings": safety_settings}
        )

        result = provider._transform_request(request)

        assert result["safety_settings"] == safety_settings

    def test_transform_with_grounding(self) -> None:
        """Test transformation with grounding features."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        grounding_config = {
            "source": "GOOGLE_SEARCH"
        }
        request = CompletionRequest(
            messages=[UserMessage(content="What is the weather?")],
            model="gemini-1.5-pro",
            metadata={"grounding": grounding_config}
        )

        result = provider._transform_request(request)

        assert result["grounding"] == grounding_config

    def test_transform_with_function_calling(self) -> None:
        """Test transformation with function calling."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        capabilities = [
            {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="gemini-1.5-pro",
            capabilities=capabilities
        )

        result = provider._transform_request(request)

        assert "tools" in result
        assert result["tools"][0]["function_declarations"] == capabilities

    def test_transform_with_provider_metadata(self) -> None:
        """Test transformation with provider-specific metadata."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro",
            metadata={
                "vertex_candidate_count": 1,
                "vertex_presence_penalty": 0.5,
                "other_key": "ignored"
            }
        )

        result = provider._transform_request(request)

        assert result["candidate_count"] == 1
        assert result["presence_penalty"] == 0.5
        assert "other_key" not in result


class TestVertexAIResponseTransformation:
    """Test response transformation from Vertex AI format."""

    def test_transform_basic_response(self) -> None:
        """Test transformation of basic Vertex AI response."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Vertex AI response
        mock_response = Mock()
        mock_response.name = "response-123"
        mock_response.model = "gemini-1.5-pro"

        mock_part = Mock()
        mock_part.text = "Hello! How can I help?"

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content
        mock_candidate.finish_reason = "STOP"

        mock_response.candidates = [mock_candidate]

        mock_usage = Mock()
        mock_usage.prompt_token_count = 10
        mock_usage.candidates_token_count = 20
        mock_usage.total_token_count = 30
        mock_response.usage_metadata = mock_usage

        result = provider._transform_response(mock_response)

        assert isinstance(result, CompletionResponse)
        assert result.id == "response-123"
        assert result.model == "gemini-1.5-pro"
        assert result.provider == "vertex"
        assert result.content == "Hello! How can I help?"
        assert result.role == "assistant"
        assert result.finish_reason == "stop"
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 20
        assert result.usage.total_tokens == 30

    def test_transform_response_with_function_call(self) -> None:
        """Test transformation of response with function call."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Vertex AI response with function call
        mock_response = Mock()
        mock_response.name = "response-123"
        mock_response.model = "gemini-1.5-pro"

        mock_func_call = Mock()
        mock_func_call.name = "get_weather"
        mock_func_call.args = {"location": "NYC"}

        mock_part = Mock()
        mock_part.function_call = mock_func_call
        mock_part.text = None

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content
        mock_candidate.finish_reason = "STOP"

        mock_response.candidates = [mock_candidate]

        mock_usage = Mock()
        mock_usage.prompt_token_count = 10
        mock_usage.candidates_token_count = 5
        mock_usage.total_token_count = 15
        mock_response.usage_metadata = mock_usage

        result = provider._transform_response(mock_response)

        assert result.content == ""
        assert result.metadata["tool_calls"] is not None
        assert len(result.metadata["tool_calls"]) == 1
        assert result.metadata["tool_calls"][0]["function"]["name"] == "get_weather"
        assert result.metadata["tool_calls"][0]["function"]["arguments"] == {"location": "NYC"}

    def test_transform_response_without_usage(self) -> None:
        """Test transformation of response without usage metadata."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Vertex AI response without usage
        mock_response = Mock()
        mock_response.name = "response-123"
        mock_response.model = "gemini-1.5-pro"

        mock_part = Mock()
        mock_part.text = "Response"

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content
        mock_candidate.finish_reason = "STOP"

        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = None

        result = provider._transform_response(mock_response)

        assert result.usage.prompt_tokens == 0
        assert result.usage.completion_tokens == 0
        assert result.usage.total_tokens == 0


class TestVertexAIStreamTransformation:
    """Test stream chunk transformation."""

    def test_transform_stream_chunk(self) -> None:
        """Test transformation of stream chunk."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Vertex AI stream chunk
        mock_chunk = Mock()

        mock_part = Mock()
        mock_part.text = "Hello"

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content
        mock_candidate.finish_reason = "STOP"

        mock_chunk.candidates = [mock_candidate]

        result = provider._transform_stream_chunk(mock_chunk)

        assert isinstance(result, StreamChunk)
        assert result.delta == "Hello"
        assert result.finish_reason == "stop"

    def test_transform_final_stream_chunk(self) -> None:
        """Test transformation of final stream chunk."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock final stream chunk
        mock_chunk = Mock()

        mock_part = Mock()
        mock_part.text = ""

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content
        mock_candidate.finish_reason = "STOP"

        mock_chunk.candidates = [mock_candidate]

        result = provider._transform_stream_chunk(mock_chunk)

        assert result.delta == ""
        assert result.finish_reason == "stop"


class TestVertexAIProviderCalls:
    """Test actual provider API calls."""

    @patch("nimbus.providers.llm.vertex_provider.LazyImporter.import_module")
    def test_complete_success(self, mock_import: Mock) -> None:
        """Test successful completion call."""
        # Setup mocks
        mock_vertexai = MagicMock()
        mock_import.return_value = mock_vertexai

        mock_generative_models = Mock()
        mock_vertexai.generative_models = mock_generative_models

        mock_model = Mock()
        mock_generative_models.GenerativeModel.return_value = mock_model

        # Mock response
        mock_response = Mock()
        mock_response.name = "response-123"
        mock_response.model = "gemini-1.5-pro"

        mock_part = Mock()
        mock_part.text = "Test response"

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content
        mock_candidate.finish_reason = "STOP"

        mock_response.candidates = [mock_candidate]

        mock_usage = Mock()
        mock_usage.prompt_token_count = 10
        mock_usage.candidates_token_count = 5
        mock_usage.total_token_count = 15
        mock_response.usage_metadata = mock_usage

        mock_model.generate_content.return_value = mock_response

        # Execute
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro"
        )

        result = provider.complete(request)

        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.content == "Test response"
        assert result.provider == "vertex"
        mock_model.generate_content.assert_called_once()

    @patch("nimbus.providers.llm.vertex_provider.LazyImporter.import_module")
    def test_complete_error_handling(self, mock_import: Mock) -> None:
        """Test error handling in complete."""
        # Setup mocks
        mock_vertexai = MagicMock()
        mock_import.return_value = mock_vertexai

        mock_generative_models = Mock()
        mock_vertexai.generative_models = mock_generative_models

        mock_model = Mock()
        mock_generative_models.GenerativeModel.return_value = mock_model

        # Mock error
        mock_model.generate_content.side_effect = Exception("API Error")

        # Execute and verify error
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro"
        )

        with pytest.raises(ProviderError) as exc_info:
            provider.complete(request)

        assert "Provider call failed" in str(exc_info.value)
        assert exc_info.value.details["provider"] == "vertex"

    @patch("nimbus.providers.llm.vertex_provider.LazyImporter.import_module")
    def test_stream_success(self, mock_import: Mock) -> None:
        """Test successful streaming call."""
        # Setup mocks
        mock_vertexai = MagicMock()
        mock_import.return_value = mock_vertexai

        mock_generative_models = Mock()
        mock_vertexai.generative_models = mock_generative_models

        mock_model = Mock()
        mock_generative_models.GenerativeModel.return_value = mock_model

        # Mock stream chunks
        mock_chunks = []
        for content in ["Hello", " ", "world"]:
            mock_chunk = Mock()

            mock_part = Mock()
            mock_part.text = content

            mock_content = Mock()
            mock_content.parts = [mock_part]

            mock_candidate = Mock()
            mock_candidate.content = mock_content
            mock_candidate.finish_reason = None if content != "world" else "STOP"

            mock_chunk.candidates = [mock_candidate]
            mock_chunks.append(mock_chunk)

        mock_model.generate_content.return_value = iter(mock_chunks)

        # Execute
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro",
            stream=True
        )

        chunks = list(provider.stream(request))

        # Verify
        assert len(chunks) == 3
        assert chunks[0].delta == "Hello"
        assert chunks[1].delta == " "
        assert chunks[2].delta == "world"
        assert chunks[2].finish_reason == "stop"


class TestVertexAIAsyncSupport:
    """Test async completion support."""

    @pytest.mark.asyncio
    @patch("nimbus.providers.llm.vertex_provider.LazyImporter.import_module")
    async def test_acomplete_success(self, mock_import: Mock) -> None:
        """Test successful async completion."""
        # Setup mocks
        mock_vertexai = MagicMock()
        mock_import.return_value = mock_vertexai

        mock_generative_models = Mock()
        mock_vertexai.generative_models = mock_generative_models

        mock_model = Mock()
        mock_generative_models.GenerativeModel.return_value = mock_model

        # Mock response
        mock_response = Mock()
        mock_response.name = "response-123"
        mock_response.model = "gemini-1.5-pro"

        mock_part = Mock()
        mock_part.text = "Async response"

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content
        mock_candidate.finish_reason = "STOP"

        mock_response.candidates = [mock_candidate]

        mock_usage = Mock()
        mock_usage.prompt_token_count = 10
        mock_usage.candidates_token_count = 5
        mock_usage.total_token_count = 15
        mock_response.usage_metadata = mock_usage

        mock_model.generate_content.return_value = mock_response

        # Execute
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro"
        )

        result = await provider.acomplete(request)

        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.content == "Async response"
        assert result.model == "gemini-1.5-pro"
        assert result.provider == "vertex"


class TestVertexAIModelInfo:
    """Test model info retrieval."""

    def test_get_model_info(self) -> None:
        """Test getting model information."""
        provider = VertexAIProvider(
            project_id="my-project",
            location="us-central1"
        )

        info = provider.get_model_info()

        assert info["provider"] == "vertex"
        assert info["supports_streaming"] is True
        assert info["supports_function_calling"] is True
        assert info["supports_structured_output"] is False
        assert info["supports_multimodal"] is True
