"""Unit tests for Google provider implementation.

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

from nimbus.base.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.base.exceptions import ProviderError
from nimbus.base.messages import AssistantMessage, SystemMessage, UserMessage
from nimbus.models.llm.google_provider import GoogleProvider


class TestGoogleProviderInitialization:
    """Test Google provider initialization."""

    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        assert provider.project_id == "my-project"
        assert provider.location == "us-central1"
        assert provider.credentials is None

    def test_init_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        mock_creds = Mock()
        provider = GoogleProvider(
            project_id="my-project",
            location="europe-west1",
            credentials=mock_creds
        )
        assert provider.project_id == "my-project"
        assert provider.location == "europe-west1"
        assert provider.credentials is mock_creds

    @patch("nimbus.models.llm.google_provider.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_vertexai = MagicMock()
        mock_import.return_value = mock_vertexai

        provider = GoogleProvider(
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
        mock_vertexai.init.assert_called_once_with(
            project="my-project",
            location="us-central1",
            credentials=None
        )


class TestGoogleAIRequestTransformation:
    """Test request transformation to Google format."""

    def test_transform_basic_request(self) -> None:
        """Test transformation of basic completion request."""
        provider = GoogleProvider(
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
        provider = GoogleProvider(
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
        provider = GoogleProvider(
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
        provider = GoogleProvider(
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
        provider = GoogleProvider(
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
        provider = GoogleProvider(
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
        """Test transformation with function calling (legacy test - now handled by TestGoogleAIToolCalling)."""
        # This test is now superseded by the more comprehensive TestGoogleAIToolCalling tests
        # Keeping it for backwards compatibility but updating to use proper CapabilityInterface
        from nimbus.tools import LocalFunctionCapability

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        capability = LocalFunctionCapability(get_weather)

        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="gemini-1.5-pro",
            capabilities=[capability]
        )

        result = provider._transform_request(request)

        assert "tools" in result
        assert len(result["tools"]) == 1
        assert "function_declarations" in result["tools"][0]
        assert len(result["tools"][0]["function_declarations"]) == 1
        assert result["tools"][0]["function_declarations"][0]["name"] == "get_weather"

    def test_transform_with_provider_metadata(self) -> None:
        """Test transformation with provider-specific metadata."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gemini-1.5-pro",
            metadata={
                "google_candidate_count": 1,
                "google_presence_penalty": 0.5,
                "other_key": "ignored"
            }
        )

        result = provider._transform_request(request)

        assert result["candidate_count"] == 1
        assert result["presence_penalty"] == 0.5
        assert "other_key" not in result


class TestGoogleAIResponseTransformation:
    """Test response transformation from Google format."""

    def test_transform_basic_response(self) -> None:
        """Test transformation of basic Google response."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Google response
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
        assert result.provider == "google"
        assert result.content == "Hello! How can I help?"
        assert result.role == "assistant"
        assert result.finish_reason == "stop"
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 20
        assert result.usage.total_tokens == 30

    def test_transform_response_with_function_call(self) -> None:
        """Test transformation of response with function call (legacy test - now handled by TestGoogleAIToolCalling)."""
        # This test is now superseded by the more comprehensive TestGoogleAIToolCalling tests
        # Updating to match new metadata format
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Google response with function call
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
        # New format stores tool calls in metadata["candidates"]
        assert "candidates" in result.metadata
        assert len(result.metadata["candidates"]) == 1
        # Also check that capability_calls list is populated
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        assert result.capability_calls[0].name == "get_weather"
        assert result.capability_calls[0].arguments == {"location": "NYC"}

    def test_transform_response_without_usage(self) -> None:
        """Test transformation of response without usage metadata."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Google response without usage
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


class TestGoogleAIStreamTransformation:
    """Test stream chunk transformation."""

    def test_transform_stream_chunk(self) -> None:
        """Test transformation of stream chunk."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Google stream chunk
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
        provider = GoogleProvider(
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


class TestGoogleProviderCalls:
    """Test actual provider API calls."""

    @patch("nimbus.models.llm.google_provider.LazyImporter.import_module")
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
        provider = GoogleProvider(
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
        assert result.provider == "google"
        mock_model.generate_content.assert_called_once()

    @patch("nimbus.models.llm.google_provider.LazyImporter.import_module")
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
        provider = GoogleProvider(
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
        assert exc_info.value.details["provider"] == "google"

    @patch("nimbus.models.llm.google_provider.LazyImporter.import_module")
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
        provider = GoogleProvider(
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


class TestGoogleAIAsyncSupport:
    """Test async completion support."""

    @pytest.mark.asyncio
    @patch("nimbus.models.llm.google_provider.LazyImporter.import_module")
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
        provider = GoogleProvider(
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
        assert result.provider == "google"


class TestGoogleAIModelInfo:
    """Test model info retrieval."""

    def test_get_model_info(self) -> None:
        """Test getting model information."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        info = provider.get_model_info()

        assert info["provider"] == "google"
        assert info["supports_streaming"] is True
        assert info["supports_function_calling"] is True
        assert info["supports_structured_output"] is False
        assert info["supports_multimodal"] is True


class TestGoogleAIToolCalling:
    """Test tool calling integration with capabilities."""

    def test_transform_capabilities_with_capability_interface(self) -> None:
        """Test _transform_capabilities() with CapabilityInterface objects."""
        from nimbus.tools import LocalFunctionCapability

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        capability = LocalFunctionCapability(get_weather)

        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Test internal transformation method
        result = provider._transform_capabilities([capability])

        # Verify Google format
        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["description"] == "Get weather for a location."
        assert "parameters" in result[0]
        assert result[0]["parameters"]["type"] == "object"
    
    def test_transform_capabilities_with_dict_format(self) -> None:
        """Test _transform_capabilities() with dict format."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        
        # Already in Google format
        capabilities = [
            {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
        
        result = provider._transform_capabilities(capabilities)
        
        # Should pass through unchanged
        assert result == capabilities
    
    def test_transform_capabilities_converts_openai_format(self) -> None:
        """Test _transform_capabilities() converts OpenAI format to Google format."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        
        # OpenAI format
        capabilities = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}
                }
            }
        ]
        
        result = provider._transform_capabilities(capabilities)
        
        # Should convert to Google format
        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["description"] == "Get weather"
        assert result[0]["parameters"]["type"] == "object"
        assert "location" in result[0]["parameters"]["properties"]

    def test_transform_request_with_capabilities(self) -> None:
        """Test transformation of request with capabilities."""
        from nimbus.tools import LocalFunctionCapability

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        capability = LocalFunctionCapability(get_weather)

        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather in NYC?")],
            model="gemini-1.5-pro",
            capabilities=[capability]
        )

        result = provider._transform_request(request)

        # Verify tools are present
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert "function_declarations" in result["tools"][0]

        # Verify function declaration format
        func_decl = result["tools"][0]["function_declarations"][0]
        assert func_decl["name"] == "get_weather"
        assert func_decl["description"] == "Get weather for a location."
        assert "parameters" in func_decl

    def test_transform_request_with_tool_choice_auto(self) -> None:
        """Test transformation with capability_choice='auto'."""
        from nimbus.tools import LocalFunctionCapability

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        capability = LocalFunctionCapability(get_weather)

        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="gemini-1.5-pro",
            capabilities=[capability],
            capability_choice="auto"
        )

        result = provider._transform_request(request)

        # Verify tool_config is present
        assert "tool_config" in result
        assert result["tool_config"]["function_calling_config"]["mode"] == "AUTO"

    def test_transform_request_with_tool_choice_required(self) -> None:
        """Test transformation with capability_choice='required'."""
        from nimbus.tools import LocalFunctionCapability

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        capability = LocalFunctionCapability(get_weather)

        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="gemini-1.5-pro",
            capabilities=[capability],
            capability_choice="required"
        )

        result = provider._transform_request(request)

        # Verify tool_config is present
        assert "tool_config" in result
        assert result["tool_config"]["function_calling_config"]["mode"] == "ANY"

    def test_transform_request_with_specific_tool_choice(self) -> None:
        """Test transformation with specific tool name in capability_choice."""
        from nimbus.tools import LocalFunctionCapability

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        def get_time(timezone: str) -> str:
            """Get current time."""
            return f"Time in {timezone}"

        capability1 = LocalFunctionCapability(get_weather)
        capability2 = LocalFunctionCapability(get_time)

        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="gemini-1.5-pro",
            capabilities=[capability1, capability2],
            capability_choice="get_weather"
        )

        result = provider._transform_request(request)

        # Verify tool_config with specific function
        assert "tool_config" in result
        assert result["tool_config"]["function_calling_config"]["mode"] == "ANY"
        assert result["tool_config"]["function_calling_config"]["allowed_function_names"] == ["get_weather"]

    def test_transform_response_with_tool_calls(self) -> None:
        """Test transformation of response with tool calls."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Google response with function call
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

        # Verify capability_calls are present
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        assert result.capability_calls[0].name == "get_weather"
        assert result.capability_calls[0].arguments == {"location": "NYC"}
        assert result.capability_calls[0].id.startswith("google_call_")

        # Verify metadata contains raw tool calls
        assert "candidates" in result.metadata
        assert len(result.metadata["candidates"]) == 1

    def test_transform_response_with_multiple_tool_calls(self) -> None:
        """Test transformation of response with multiple tool calls."""
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Google response with multiple function calls
        mock_response = Mock()
        mock_response.name = "response-123"
        mock_response.model = "gemini-1.5-pro"

        mock_func_call1 = Mock()
        mock_func_call1.name = "get_weather"
        mock_func_call1.args = {"location": "NYC"}

        mock_func_call2 = Mock()
        mock_func_call2.name = "get_time"
        mock_func_call2.args = {"timezone": "EST"}

        mock_part1 = Mock()
        mock_part1.function_call = mock_func_call1
        mock_part1.text = None

        mock_part2 = Mock()
        mock_part2.function_call = mock_func_call2
        mock_part2.text = None

        mock_content = Mock()
        mock_content.parts = [mock_part1, mock_part2]

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

        # Verify multiple capability_calls are present
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 2
        assert result.capability_calls[0].name == "get_weather"
        assert result.capability_calls[0].arguments == {"location": "NYC"}
        assert result.capability_calls[1].name == "get_time"
        assert result.capability_calls[1].arguments == {"timezone": "EST"}

    @patch("nimbus.models.llm.google_provider.LazyImporter.import_module")
    def test_complete_with_tool_calling(self, mock_import: Mock) -> None:
        """Test complete with tool calling end-to-end."""
        from nimbus.tools import LocalFunctionCapability

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        capability = LocalFunctionCapability(get_weather)

        # Setup mocks
        mock_vertexai = MagicMock()
        mock_import.return_value = mock_vertexai

        mock_generative_models = Mock()
        mock_vertexai.generative_models = mock_generative_models

        mock_model = Mock()
        mock_generative_models.GenerativeModel.return_value = mock_model

        # Mock response with function call
        mock_response = Mock()
        mock_response.name = "response-123"
        mock_response.model = "gemini-1.5-pro"

        mock_func_call = Mock()
        mock_func_call.name = "get_weather"
        mock_func_call.args = {"location": "San Francisco"}

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
        mock_usage.prompt_token_count = 15
        mock_usage.candidates_token_count = 5
        mock_usage.total_token_count = 20
        mock_response.usage_metadata = mock_usage

        mock_model.generate_content.return_value = mock_response

        # Execute
        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather in San Francisco?")],
            model="gemini-1.5-pro",
            capabilities=[capability]
        )

        result = provider.complete(request)

        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        assert result.capability_calls[0].name == "get_weather"
        assert result.capability_calls[0].arguments == {"location": "San Francisco"}

        # Verify the call was made with tools
        call_kwargs = mock_model.generate_content.call_args[1]
        assert "tools" in call_kwargs
        assert len(call_kwargs["tools"]) == 1
        assert "function_declarations" in call_kwargs["tools"][0]

    def test_tool_call_parsing_with_handler(self) -> None:
        """Test that tool calls can be parsed by CapabilityCallHandler."""
        from nimbus.tools import CapabilityRegistry, LocalFunctionCapability
        from nimbus.tools.capability_call_handler import CapabilityCallHandler

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        # Register capability
        capability = LocalFunctionCapability(get_weather)
        registry = CapabilityRegistry.get_instance()
        registry.register(capability)

        provider = GoogleProvider(
            project_id="my-project",
            location="us-central1"
        )

        # Mock Google response with function call
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

        # Transform response
        result = provider._transform_response(mock_response)

        # Parse tool calls using handler with provider instance
        handler = CapabilityCallHandler(registry)
        capability_calls = handler.parse_capability_calls(result, provider)

        # Verify parsing
        assert len(capability_calls) == 1
        assert capability_calls[0].name == "get_weather"
        assert capability_calls[0].arguments == {"location": "NYC"}

        # Clean up
        registry.unregister("get_weather")
