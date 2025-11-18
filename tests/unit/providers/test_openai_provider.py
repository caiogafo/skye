"""Unit tests for OpenAI provider implementation.

Tests cover:
- Client initialization
- Request transformation
- Response transformation
- Streaming
- Structured outputs
- Function calling
- Error handling
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel

from nimbus.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.exceptions import ProviderError
from nimbus.messages import AssistantMessage, SystemMessage, UserMessage
from nimbus.providers.llm.openai_provider import OpenAIProvider


class TestOpenAIProviderInitialization:
    """Test OpenAI provider initialization."""
    
    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        provider = OpenAIProvider(api_key="sk-test")
        assert provider.api_key == "sk-test"
        assert provider.api_base is None
        assert provider.organization is None
    
    def test_init_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        provider = OpenAIProvider(
            api_key="sk-test",
            api_base="https://custom.api",
            organization="org-123"
        )
        assert provider.api_key == "sk-test"
        assert provider.api_base == "https://custom.api"
        assert provider.organization == "org-123"
    
    @patch("nimbus.providers.llm.openai_provider.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        provider = OpenAIProvider(api_key="sk-test")
        
        # Client should not be initialized yet
        mock_import.assert_not_called()
        
        # Access client to trigger initialization
        _ = provider.client
        
        # Now it should be initialized
        mock_import.assert_called_once_with("openai", install_extra="openai")
        mock_openai.OpenAI.assert_called_once_with(
            api_key="sk-test",
            base_url=None,
            organization=None
        )


class TestOpenAIRequestTransformation:
    """Test request transformation to OpenAI format."""
    
    def test_transform_basic_request(self) -> None:
        """Test transformation of basic completion request."""
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            temperature=0.7
        )
        
        result = provider._transform_request(request)
        
        assert result["model"] == "gpt-4"
        assert result["temperature"] == 0.7
        assert result["stream"] is False
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Hello"
    
    def test_transform_with_system_message(self) -> None:
        """Test transformation with system message."""
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[
                SystemMessage(content="You are helpful"),
                UserMessage(content="Hello")
            ],
            model="gpt-4"
        )
        
        result = provider._transform_request(request)
        
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "system"
        assert result["messages"][0]["content"] == "You are helpful"
        assert result["messages"][1]["role"] == "user"
    
    def test_transform_with_max_tokens(self) -> None:
        """Test transformation with max_tokens parameter."""
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            max_tokens=100
        )
        
        result = provider._transform_request(request)
        
        assert result["max_tokens"] == 100
    
    def test_transform_with_stop_sequences(self) -> None:
        """Test transformation with stop sequences."""
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            stop=["END", "STOP"]
        )
        
        result = provider._transform_request(request)
        
        assert result["stop"] == ["END", "STOP"]
    
    def test_transform_with_structured_output(self) -> None:
        """Test transformation with structured output schema."""
        class Person(BaseModel):
            name: str
            age: int
        
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Extract person info")],
            model="gpt-4",
            response_schema=Person
        )
        
        result = provider._transform_request(request)
        
        assert "response_format" in result
        assert result["response_format"]["type"] == "json_schema"
        assert result["response_format"]["json_schema"]["name"] == "Person"
        assert "schema" in result["response_format"]["json_schema"]
        assert result["response_format"]["json_schema"]["strict"] is True
    
    def test_transform_with_function_calling(self) -> None:
        """Test transformation with function calling."""
        provider = OpenAIProvider(api_key="sk-test")
        capabilities = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="gpt-4",
            capabilities=capabilities,
            capability_choice="auto"
        )
        
        result = provider._transform_request(request)
        
        assert result["tools"] == capabilities
        assert result["tool_choice"] == "auto"
    
    def test_transform_with_provider_metadata(self) -> None:
        """Test transformation with provider-specific metadata."""
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            metadata={
                "openai_seed": 42,
                "openai_user": "user123",
                "other_key": "ignored"
            }
        )
        
        result = provider._transform_request(request)
        
        assert result["seed"] == 42
        assert result["user"] == "user123"
        assert "other_key" not in result


class TestOpenAIResponseTransformation:
    """Test response transformation from OpenAI format."""
    
    def test_transform_basic_response(self) -> None:
        """Test transformation of basic OpenAI response."""
        provider = OpenAIProvider(api_key="sk-test")
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        mock_response.system_fingerprint = "fp_123"
        
        mock_choice = Mock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = Mock()
        mock_choice.message.content = "Hello! How can I help?"
        mock_choice.message.tool_calls = None
        # Configure hasattr to return False for 'parsed'
        mock_choice.message.parsed = None
        mock_response.choices = [mock_choice]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        assert isinstance(result, CompletionResponse)
        assert result.id == "chatcmpl-123"
        assert result.model == "gpt-4"
        assert result.provider == "openai"
        assert result.content == "Hello! How can I help?"
        assert result.role == "assistant"
        assert result.finish_reason == "stop"
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 20
        assert result.usage.total_tokens == 30
        assert result.metadata["system_fingerprint"] == "fp_123"
    
    def test_transform_response_with_tool_calls(self) -> None:
        """Test transformation of response with tool calls."""
        provider = OpenAIProvider(api_key="sk-test")
        
        # Mock OpenAI response with tool calls
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        mock_response.system_fingerprint = None
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"location": "NYC"}'
        
        mock_choice = Mock()
        mock_choice.finish_reason = "tool_calls"
        mock_choice.message = Mock()
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.message.parsed = None
        mock_response.choices = [mock_choice]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 15
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        assert result.content == ""
        assert result.finish_reason == "tool_calls"
        assert result.metadata["tool_calls"] is not None
        assert len(result.metadata["tool_calls"]) == 1
        assert result.metadata["tool_calls"][0]["id"] == "call_123"
        assert result.metadata["tool_calls"][0]["function"]["name"] == "get_weather"
    
    def test_transform_response_with_structured_output(self) -> None:
        """Test transformation of response with structured output."""
        class Person(BaseModel):
            name: str
            age: int
        
        provider = OpenAIProvider(api_key="sk-test")
        
        # Mock OpenAI response with parsed structured output
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        mock_response.system_fingerprint = None
        
        parsed_person = Person(name="Alice", age=30)
        
        mock_choice = Mock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = Mock()
        mock_choice.message.content = '{"name": "Alice", "age": 30}'
        mock_choice.message.parsed = parsed_person
        mock_choice.message.tool_calls = None
        mock_response.choices = [mock_choice]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 10
        mock_usage.total_tokens = 20
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        assert result.structured_output is not None
        assert result.structured_output == parsed_person
        assert result.structured_output.name == "Alice"
        assert result.structured_output.age == 30


class TestOpenAIStreamTransformation:
    """Test stream chunk transformation."""
    
    def test_transform_stream_chunk(self) -> None:
        """Test transformation of stream chunk."""
        provider = OpenAIProvider(api_key="sk-test")
        
        # Mock OpenAI stream chunk
        mock_chunk = Mock()
        mock_chunk.id = "chatcmpl-123"
        
        mock_choice = Mock()
        mock_choice.index = 0
        mock_choice.finish_reason = None
        mock_choice.delta = Mock()
        mock_choice.delta.content = "Hello"
        mock_chunk.choices = [mock_choice]
        
        result = provider._transform_stream_chunk(mock_chunk)
        
        assert isinstance(result, StreamChunk)
        assert result.id == "chatcmpl-123"
        assert result.delta == "Hello"
        assert result.finish_reason is None
        assert result.index == 0
    
    def test_transform_final_stream_chunk(self) -> None:
        """Test transformation of final stream chunk."""
        provider = OpenAIProvider(api_key="sk-test")
        
        # Mock final stream chunk
        mock_chunk = Mock()
        mock_chunk.id = "chatcmpl-123"
        
        mock_choice = Mock()
        mock_choice.index = 5
        mock_choice.finish_reason = "stop"
        mock_choice.delta = Mock()
        mock_choice.delta.content = None
        mock_chunk.choices = [mock_choice]
        
        result = provider._transform_stream_chunk(mock_chunk)
        
        assert result.delta == ""
        assert result.finish_reason == "stop"
        assert result.index == 5


class TestOpenAIProviderCalls:
    """Test actual provider API calls."""
    
    @patch("nimbus.providers.llm.openai_provider.LazyImporter.import_module")
    def test_complete_success(self, mock_import: Mock) -> None:
        """Test successful completion call."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        mock_response.system_fingerprint = None
        
        mock_choice = Mock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = Mock()
        mock_choice.message.content = "Test response"
        mock_choice.message.tool_calls = None
        mock_choice.message.parsed = None
        mock_response.choices = [mock_choice]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 15
        mock_response.usage = mock_usage
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Execute
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4"
        )
        
        result = provider.complete(request)
        
        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.content == "Test response"
        assert result.provider == "openai"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch("nimbus.providers.llm.openai_provider.LazyImporter.import_module")
    def test_complete_error_handling(self, mock_import: Mock) -> None:
        """Test error handling in complete."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client
        
        # Mock error
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Execute and verify error
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4"
        )
        
        with pytest.raises(ProviderError) as exc_info:
            provider.complete(request)
        
        assert "Provider call failed" in str(exc_info.value)
        assert exc_info.value.details["provider"] == "openai"
    
    @patch("nimbus.providers.llm.openai_provider.LazyImporter.import_module")
    def test_stream_success(self, mock_import: Mock) -> None:
        """Test successful streaming call."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client
        
        # Mock stream chunks
        mock_chunks = []
        for i, content in enumerate(["Hello", " ", "world"]):
            mock_chunk = Mock()
            mock_chunk.id = "chatcmpl-123"
            mock_choice = Mock()
            mock_choice.index = i
            mock_choice.finish_reason = None if i < 2 else "stop"
            mock_choice.delta = Mock()
            mock_choice.delta.content = content
            mock_chunk.choices = [mock_choice]
            mock_chunks.append(mock_chunk)
        
        mock_client.chat.completions.create.return_value = iter(mock_chunks)
        
        # Execute
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            stream=True
        )
        
        chunks = list(provider.stream(request))
        
        # Verify
        assert len(chunks) == 3
        assert chunks[0].delta == "Hello"
        assert chunks[1].delta == " "
        assert chunks[2].delta == "world"
        assert chunks[2].finish_reason == "stop"


class TestOpenAIAsyncSupport:
    """Test async completion support."""
    
    @pytest.mark.asyncio
    @patch("nimbus.providers.llm.openai_provider.LazyImporter.import_module")
    async def test_acomplete_success(self, mock_import: Mock) -> None:
        """Test successful async completion."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        # Mock async client
        mock_async_client = Mock()
        mock_openai.AsyncOpenAI.return_value = mock_async_client
        
        # Mock response
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        mock_response.system_fingerprint = None
        
        mock_choice = Mock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = Mock()
        mock_choice.message.content = "Async response"
        mock_choice.message.tool_calls = None
        mock_choice.message.parsed = None
        mock_response.choices = [mock_choice]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 15
        mock_response.usage = mock_usage
        
        # Make the create method async
        async def async_create(**kwargs: Any) -> Any:
            return mock_response
        
        mock_async_client.chat.completions.create = async_create
        
        # Execute
        provider = OpenAIProvider(api_key="sk-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4"
        )
        
        result = await provider.acomplete(request)
        
        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.content == "Async response"
        assert result.provider == "openai"


class TestOpenAIModelInfo:
    """Test model info retrieval."""
    
    def test_get_model_info(self) -> None:
        """Test getting model information."""
        provider = OpenAIProvider(api_key="sk-test")
        
        info = provider.get_model_info()
        
        assert info["provider"] == "openai"
        assert info["supports_streaming"] is True
        assert info["supports_function_calling"] is True
        assert info["supports_structured_output"] is True
        assert info["supports_multimodal"] is True
