"""Unit tests for Azure OpenAI provider implementation.

Tests cover:
- Client initialization
- Azure-specific configuration
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

from nimbus.base.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.base.exceptions import ProviderError
from nimbus.base.messages import AssistantMessage, SystemMessage, UserMessage
from nimbus.models.llm.openai_compatible import AzureOpenAIProvider


class TestAzureOpenAIProviderInitialization:
    """Test Azure OpenAI provider initialization."""
    
    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        assert provider.azure_endpoint == "https://myresource.openai.azure.com/"
        assert provider.api_key == "test-key"
        assert provider.api_version == "2024-02-15-preview"
        assert provider.deployment_name == "gpt-4"
    
    def test_init_with_additional_kwargs(self) -> None:
        """Test initialization with additional kwargs."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4",
            custom_param="value"
        )
        assert provider.config["custom_param"] == "value"
    
    @patch("nimbus.models.llm.openai_compatible.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Client should not be initialized yet
        mock_import.assert_not_called()
        
        # Access client to trigger initialization
        _ = provider.client
        
        # Now it should be initialized
        mock_import.assert_called_once_with("openai", install_extra="openai")
        mock_openai.AzureOpenAI.assert_called_once_with(
            api_key="test-key",
            api_version="2024-02-15-preview",
            azure_endpoint="https://myresource.openai.azure.com/"
        )


class TestAzureOpenAIRequestTransformation:
    """Test request transformation to Azure OpenAI format."""
    
    def test_transform_basic_request(self) -> None:
        """Test transformation of basic completion request."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            temperature=0.7
        )
        
        result = provider._transform_request(request)
        
        # Azure uses deployment_name instead of model
        assert result["model"] == "gpt-4"
        assert result["temperature"] == 0.7
        assert result["stream"] is False
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Hello"
    
    def test_transform_with_system_message(self) -> None:
        """Test transformation with system message."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
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
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            max_tokens=100
        )
        
        result = provider._transform_request(request)
        
        assert result["max_tokens"] == 100
    
    def test_transform_with_stop_sequences(self) -> None:
        """Test transformation with stop sequences."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
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
        
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
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
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
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
    
    def test_transform_with_azure_metadata(self) -> None:
        """Test transformation with Azure-specific metadata."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            metadata={
                "azure_seed": 42,
                "azure_user": "user123",
                "other_key": "ignored"
            }
        )
        
        result = provider._transform_request(request)
        
        assert result["seed"] == 42
        assert result["user"] == "user123"
        assert "other_key" not in result


class TestAzureOpenAIResponseTransformation:
    """Test response transformation from Azure OpenAI format."""
    
    def test_transform_basic_response(self) -> None:
        """Test transformation of basic Azure OpenAI response."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Mock Azure OpenAI response
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
        mock_choice = Mock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = Mock()
        mock_choice.message.content = "Hello! How can I help?"
        mock_choice.message.tool_calls = None
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
        assert result.provider == "azure"
        assert result.content == "Hello! How can I help?"
        assert result.role == "assistant"
        assert result.finish_reason == "stop"
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 20
        assert result.usage.total_tokens == 30
    
    def test_transform_response_with_tool_calls(self) -> None:
        """Test transformation of response with tool calls."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Mock Azure OpenAI response with tool calls
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
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
        
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Mock Azure OpenAI response with parsed structured output
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
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


class TestAzureOpenAIStreamTransformation:
    """Test stream chunk transformation."""
    
    def test_transform_stream_chunk(self) -> None:
        """Test transformation of stream chunk."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Mock Azure OpenAI stream chunk
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
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
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


class TestAzureOpenAIProviderCalls:
    """Test actual provider API calls."""
    
    @patch("nimbus.models.llm.openai_compatible.LazyImporter.import_module")
    def test_complete_success(self, mock_import: Mock) -> None:
        """Test successful completion call."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        mock_client = Mock()
        mock_openai.AzureOpenAI.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
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
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4"
        )
        
        result = provider.complete(request)
        
        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.content == "Test response"
        assert result.provider == "azure"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch("nimbus.models.llm.openai_compatible.LazyImporter.import_module")
    def test_complete_error_handling(self, mock_import: Mock) -> None:
        """Test error handling in complete."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        mock_client = Mock()
        mock_openai.AzureOpenAI.return_value = mock_client
        
        # Mock error
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Execute and verify error
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4"
        )
        
        with pytest.raises(ProviderError) as exc_info:
            provider.complete(request)
        
        assert "Provider call failed" in str(exc_info.value)
        assert exc_info.value.details["provider"] == "azure"
    
    @patch("nimbus.models.llm.openai_compatible.LazyImporter.import_module")
    def test_stream_success(self, mock_import: Mock) -> None:
        """Test successful streaming call."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        mock_client = Mock()
        mock_openai.AzureOpenAI.return_value = mock_client
        
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
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
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


class TestAzureOpenAIAsyncSupport:
    """Test async completion support."""
    
    @pytest.mark.asyncio
    @patch("nimbus.models.llm.openai_compatible.LazyImporter.import_module")
    async def test_acomplete_success(self, mock_import: Mock) -> None:
        """Test successful async completion."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        # Mock async client
        mock_async_client = Mock()
        mock_openai.AsyncAzureOpenAI.return_value = mock_async_client
        
        # Mock response
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
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
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4"
        )
        
        result = await provider.acomplete(request)
        
        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.content == "Async response"
        assert result.provider == "azure"


class TestAzureOpenAIToolCalling:
    """Test tool calling integration with capabilities."""
    
    def test_transform_request_with_capabilities(self) -> None:
        """Test transformation of request with capabilities to Azure format."""
        # Mock capability
        mock_capability = Mock()
        mock_schema = Mock()
        mock_schema.name = "get_weather"
        mock_schema.description = "Get weather for a location"
        mock_schema.parameters = {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
        mock_capability.get_schema.return_value = mock_schema
        
        provider = AzureOpenAIProvider(
            model="gpt-4",
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather in NYC?")],
            model="gpt-4",
            capabilities=[mock_capability],
            capability_choice="auto"
        )
        
        result = provider._transform_request(request)
        
        # Verify tools are converted to Azure/OpenAI format
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["type"] == "function"
        assert result["tools"][0]["function"]["name"] == "get_weather"
        assert result["tools"][0]["function"]["description"] == "Get weather for a location"
        assert result["tool_choice"] == "auto"
    
    def test_transform_request_with_specific_capability_choice(self) -> None:
        """Test transformation with specific capability name in capability_choice."""
        # Mock capability
        mock_capability = Mock()
        mock_schema = Mock()
        mock_schema.name = "get_weather"
        mock_schema.description = "Get weather"
        mock_schema.parameters = {"type": "object", "properties": {}}
        mock_capability.get_schema.return_value = mock_schema
        
        provider = AzureOpenAIProvider(
            model="gpt-4",
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="gpt-4",
            capabilities=[mock_capability],
            capability_choice="get_weather"
        )
        
        result = provider._transform_request(request)
        
        # Verify tool_choice is formatted correctly for specific tool
        assert "tool_choice" in result
        assert result["tool_choice"]["type"] == "function"
        assert result["tool_choice"]["function"]["name"] == "get_weather"
    
    def test_transform_request_with_required_tool_choice(self) -> None:
        """Test transformation with 'required' tool_choice."""
        # Mock capability
        mock_capability = Mock()
        mock_schema = Mock()
        mock_schema.name = "calculator"
        mock_schema.description = "Calculate"
        mock_schema.parameters = {"type": "object", "properties": {}}
        mock_capability.get_schema.return_value = mock_schema
        
        provider = AzureOpenAIProvider(
            model="gpt-4",
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="Calculate 2+2")],
            model="gpt-4",
            capabilities=[mock_capability],
            capability_choice="required"
        )
        
        result = provider._transform_request(request)
        
        # Verify tool_choice is passed through as-is for 'required'
        assert result["tool_choice"] == "required"
    
    def test_transform_response_with_tool_calls_creates_tool_call_objects(self) -> None:
        """Test that tool calls in response are converted to CapabilityCall objects."""
        provider = AzureOpenAIProvider(
            model="gpt-4",
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Mock Azure OpenAI response with tool calls
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_abc123"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"location": "San Francisco", "unit": "celsius"}'
        
        mock_choice = Mock()
        mock_choice.finish_reason = "tool_calls"
        mock_choice.message = Mock()
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.message.parsed = None
        mock_response.choices = [mock_choice]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 70
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        # Verify capability_calls are present in response
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        
        # Verify CapabilityCall object structure
        capability_call = result.capability_calls[0]
        assert capability_call.id == "call_abc123"
        assert capability_call.name == "get_weather"
        assert capability_call.arguments == {"location": "San Francisco", "unit": "celsius"}
        
        # Verify metadata also contains raw tool calls
        assert result.metadata["tool_calls"] is not None
        assert len(result.metadata["tool_calls"]) == 1
        assert result.metadata["tool_calls"][0]["id"] == "call_abc123"
    
    def test_transform_response_with_parallel_tool_calls(self) -> None:
        """Test handling of parallel tool calls in response."""
        provider = AzureOpenAIProvider(
            model="gpt-4",
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Mock Azure OpenAI response with multiple parallel tool calls
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
        mock_tool_call_1 = Mock()
        mock_tool_call_1.id = "call_1"
        mock_tool_call_1.type = "function"
        mock_tool_call_1.function = Mock()
        mock_tool_call_1.function.name = "get_weather"
        mock_tool_call_1.function.arguments = '{"location": "NYC"}'
        
        mock_tool_call_2 = Mock()
        mock_tool_call_2.id = "call_2"
        mock_tool_call_2.type = "function"
        mock_tool_call_2.function = Mock()
        mock_tool_call_2.function.name = "get_time"
        mock_tool_call_2.function.arguments = '{"timezone": "EST"}'
        
        mock_choice = Mock()
        mock_choice.finish_reason = "tool_calls"
        mock_choice.message = Mock()
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call_1, mock_tool_call_2]
        mock_choice.message.parsed = None
        mock_response.choices = [mock_choice]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 60
        mock_usage.completion_tokens = 30
        mock_usage.total_tokens = 90
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        # Verify both capability calls are present
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 2
        
        # Verify first capability call
        assert result.capability_calls[0].id == "call_1"
        assert result.capability_calls[0].name == "get_weather"
        assert result.capability_calls[0].arguments == {"location": "NYC"}
        
        # Verify second capability call
        assert result.capability_calls[1].id == "call_2"
        assert result.capability_calls[1].name == "get_time"
        assert result.capability_calls[1].arguments == {"timezone": "EST"}
    
    def test_transform_response_with_invalid_json_arguments(self) -> None:
        """Test handling of tool calls with invalid JSON arguments."""
        provider = AzureOpenAIProvider(
            model="gpt-4",
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Mock Azure OpenAI response with invalid JSON in arguments
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = 'invalid json {'
        
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
        
        # Verify capability call is still created with empty arguments
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        assert result.capability_calls[0].arguments == {}
    
    def test_transform_request_with_multiple_capabilities(self) -> None:
        """Test transformation with multiple capabilities."""
        provider = AzureOpenAIProvider(
            model="gpt-4",
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        # Mock multiple capabilities
        mock_capability_1 = Mock()
        mock_schema_1 = Mock()
        mock_schema_1.name = "get_weather"
        mock_schema_1.description = "Get weather"
        mock_schema_1.parameters = {"type": "object", "properties": {"location": {"type": "string"}}}
        mock_capability_1.get_schema.return_value = mock_schema_1
        
        mock_capability_2 = Mock()
        mock_schema_2 = Mock()
        mock_schema_2.name = "get_time"
        mock_schema_2.description = "Get time"
        mock_schema_2.parameters = {"type": "object", "properties": {"timezone": {"type": "string"}}}
        mock_capability_2.get_schema.return_value = mock_schema_2
        
        # Create request with multiple capabilities
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            capabilities=[mock_capability_1, mock_capability_2]
        )
        
        result = provider._transform_request(request)
        
        # Verify both tools are present
        assert "tools" in result
        assert len(result["tools"]) == 2
        assert result["tools"][0]["function"]["name"] == "get_weather"
        assert result["tools"][1]["function"]["name"] == "get_time"
    
    @patch("nimbus.models.llm.openai_compatible.LazyImporter.import_module")
    def test_complete_with_tool_calls(self, mock_import: Mock) -> None:
        """Test end-to-end completion with tool calls."""
        # Setup mocks
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        
        mock_client = Mock()
        mock_openai.AzureOpenAI.return_value = mock_client
        
        # Mock capability
        mock_capability = Mock()
        mock_schema = Mock()
        mock_schema.name = "get_weather"
        mock_schema.description = "Get weather"
        mock_schema.parameters = {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
        mock_capability.get_schema.return_value = mock_schema
        
        # Mock response with tool call
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"location": "Boston"}'
        
        mock_choice = Mock()
        mock_choice.finish_reason = "tool_calls"
        mock_choice.message = Mock()
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.message.parsed = None
        mock_response.choices = [mock_choice]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 40
        mock_usage.completion_tokens = 15
        mock_usage.total_tokens = 55
        mock_response.usage = mock_usage
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Execute
        provider = AzureOpenAIProvider(
            model="gpt-4",
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather in Boston?")],
            model="gpt-4",
            capabilities=[mock_capability],
            capability_choice="auto"
        )
        
        result = provider.complete(request)
        
        # Verify
        assert result.finish_reason == "tool_calls"
        assert result.has_capability_calls()
        assert len(result.capability_calls) == 1
        assert result.capability_calls[0].name == "get_weather"
        
        # Verify the API was called with tools
        call_args = mock_client.chat.completions.create.call_args
        assert "tools" in call_args[1]
        assert call_args[1]["tool_choice"] == "auto"


class TestAzureOpenAIModelInfo:
    """Test model info retrieval."""
    
    def test_get_model_info(self) -> None:
        """Test getting model information."""
        provider = AzureOpenAIProvider(
            azure_endpoint="https://myresource.openai.azure.com/",
            api_key="test-key",
            api_version="2024-02-15-preview",
            deployment_name="gpt-4"
        )
        
        info = provider.get_model_info()
        
        assert info["provider"] == "azure"
        assert info["supports_streaming"] is True
        assert info["supports_function_calling"] is True
        assert info["supports_structured_output"] is True
        assert info["supports_multimodal"] is True
