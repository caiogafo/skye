"""Unit tests for Anthropic provider implementation.

Tests cover:
- Client initialization
- Request transformation with system message separation
- Response transformation
- Tool use format
- Streaming
- Error handling
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from nimbus.base.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.base.exceptions import ProviderError
from nimbus.base.messages import AssistantMessage, SystemMessage, UserMessage
from nimbus.models.llm.anthropic import AnthropicProvider


class TestAnthropicProviderInitialization:
    """Test Anthropic provider initialization."""
    
    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        assert provider.api_key == "sk-ant-test"
    
    @patch("nimbus.models.llm.anthropic.LazyImporter.import_module")
    def test_lazy_client_initialization(self, mock_import: Mock) -> None:
        """Test that client is lazily initialized."""
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Client should not be initialized yet
        mock_import.assert_not_called()
        
        # Access client to trigger initialization
        _ = provider.client
        
        # Now it should be initialized
        mock_import.assert_called_once_with("anthropic", install_extra="anthropic")
        mock_anthropic.Anthropic.assert_called_once_with(api_key="sk-ant-test")


class TestAnthropicRequestTransformation:
    """Test request transformation to Anthropic format."""
    
    def test_transform_basic_request(self) -> None:
        """Test transformation of basic completion request."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="claude-3-opus-20240229",
            temperature=0.7
        )
        
        result = provider._transform_request(request)
        
        assert result["model"] == "claude-3-opus-20240229"
        assert result["temperature"] == 0.7
        assert result["stream"] is False
        assert result["max_tokens"] == 4096  # Default
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Hello"
        assert "system" not in result
    
    def test_transform_with_system_message_separation(self) -> None:
        """Test transformation with system message separated."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[
                SystemMessage(content="You are a helpful assistant"),
                UserMessage(content="Hello")
            ],
            model="claude-3-opus-20240229"
        )
        
        result = provider._transform_request(request)
        
        # System message should be separate
        assert result["system"] == "You are a helpful assistant"
        # Only user message in messages array
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Hello"
    
    def test_transform_with_max_tokens(self) -> None:
        """Test transformation with max_tokens parameter."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="claude-3-opus-20240229",
            max_tokens=1000
        )
        
        result = provider._transform_request(request)
        
        assert result["max_tokens"] == 1000
    
    def test_transform_with_stop_sequences(self) -> None:
        """Test transformation with stop sequences."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="claude-3-opus-20240229",
            stop=["END", "STOP"]
        )
        
        result = provider._transform_request(request)
        
        assert result["stop_sequences"] == ["END", "STOP"]
    
    def test_transform_with_tool_use(self) -> None:
        """Test transformation with tool use (Anthropic's function calling)."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        capabilities = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        }
                    }
                }
            }
        ]
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="claude-3-opus-20240229",
            capabilities=capabilities,
            capability_choice="auto"
        )
        
        result = provider._transform_request(request)
        
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "get_weather"
        assert result["tools"][0]["description"] == "Get weather information"
        assert result["tools"][0]["input_schema"]["type"] == "object"
        assert result["tool_choice"] == {"type": "auto"}
    
    def test_transform_with_tool_choice_required(self) -> None:
        """Test transformation with required tool choice."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
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
            model="claude-3-opus-20240229",
            capabilities=capabilities,
            capability_choice="required"
        )
        
        result = provider._transform_request(request)
        
        assert result["tool_choice"] == {"type": "any"}
    
    def test_transform_with_provider_metadata(self) -> None:
        """Test transformation with provider-specific metadata."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="claude-3-opus-20240229",
            metadata={
                "anthropic_metadata": {"user_id": "user123"},
                "other_key": "ignored"
            }
        )
        
        result = provider._transform_request(request)
        
        assert result["metadata"] == {"user_id": "user123"}
        assert "other_key" not in result


class TestAnthropicResponseTransformation:
    """Test response transformation from Anthropic format."""
    
    def test_transform_basic_response(self) -> None:
        """Test transformation of basic Anthropic response."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock Anthropic response
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.stop_sequence = None
        
        # Mock content blocks
        mock_content = Mock()
        mock_content.type = "text"
        mock_content.text = "Hello! How can I help you today?"
        mock_response.content = [mock_content]
        
        # Mock usage
        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        assert isinstance(result, CompletionResponse)
        assert result.id == "msg_123"
        assert result.model == "claude-3-opus-20240229"
        assert result.provider == "anthropic"
        assert result.content == "Hello! How can I help you today?"
        assert result.role == "assistant"
        assert result.finish_reason == "end_turn"
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 20
        assert result.usage.total_tokens == 30
        assert result.metadata["stop_sequence"] is None
        assert result.metadata["tool_calls"] is None
    
    def test_transform_response_with_tool_use(self) -> None:
        """Test transformation of response with tool use."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock Anthropic response with tool use
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "tool_use"
        mock_response.stop_sequence = None
        
        # Mock tool use content block
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.id = "toolu_123"
        mock_tool_use.name = "get_weather"
        mock_tool_use.input = {"location": "NYC"}
        mock_response.content = [mock_tool_use]
        
        # Mock usage
        mock_usage = Mock()
        mock_usage.input_tokens = 15
        mock_usage.output_tokens = 10
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        assert result.content == ""
        assert result.finish_reason == "tool_use"
        assert result.metadata["tool_calls"] is not None
        assert len(result.metadata["tool_calls"]) == 1
        assert result.metadata["tool_calls"][0]["id"] == "toolu_123"
        assert result.metadata["tool_calls"][0]["type"] == "function"
        assert result.metadata["tool_calls"][0]["function"]["name"] == "get_weather"
        assert result.metadata["tool_calls"][0]["function"]["arguments"] == {"location": "NYC"}
    
    def test_transform_response_with_mixed_content(self) -> None:
        """Test transformation of response with text and tool use."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock Anthropic response with mixed content
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "tool_use"
        mock_response.stop_sequence = None
        
        # Mock text content
        mock_text = Mock()
        mock_text.type = "text"
        mock_text.text = "Let me check the weather for you."
        
        # Mock tool use content
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.id = "toolu_123"
        mock_tool_use.name = "get_weather"
        mock_tool_use.input = {"location": "NYC"}
        
        mock_response.content = [mock_text, mock_tool_use]
        
        # Mock usage
        mock_usage = Mock()
        mock_usage.input_tokens = 15
        mock_usage.output_tokens = 25
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        assert result.content == "Let me check the weather for you."
        assert result.metadata["tool_calls"] is not None
        assert len(result.metadata["tool_calls"]) == 1


class TestAnthropicStreamTransformation:
    """Test stream chunk transformation."""
    
    def test_transform_content_block_delta(self) -> None:
        """Test transformation of content block delta event."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock Anthropic stream event
        mock_chunk = Mock()
        mock_chunk.type = "content_block_delta"
        mock_chunk.message_id = "msg_123"
        mock_chunk.index = 0
        mock_chunk.delta = Mock()
        mock_chunk.delta.text = "Hello"
        
        result = provider._transform_stream_chunk(mock_chunk)
        
        assert isinstance(result, StreamChunk)
        assert result.id == "msg_123"
        assert result.delta == "Hello"
        assert result.finish_reason is None
        assert result.index == 0
    
    def test_transform_message_delta_with_stop(self) -> None:
        """Test transformation of message delta with stop reason."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock final stream event
        mock_chunk = Mock()
        mock_chunk.type = "message_delta"
        mock_chunk.message_id = "msg_123"
        mock_chunk.index = 0
        mock_chunk.delta = Mock()
        mock_chunk.delta.stop_reason = "end_turn"
        
        result = provider._transform_stream_chunk(mock_chunk)
        
        assert result.delta == ""
        assert result.finish_reason == "end_turn"
    
    def test_transform_other_event_types(self) -> None:
        """Test transformation of other event types."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock other event type (e.g., message_start)
        mock_chunk = Mock()
        mock_chunk.type = "message_start"
        mock_chunk.message_id = "msg_123"
        mock_chunk.index = 0
        
        result = provider._transform_stream_chunk(mock_chunk)
        
        assert result.delta == ""
        assert result.finish_reason is None


class TestAnthropicProviderCalls:
    """Test actual provider API calls."""
    
    @patch("nimbus.models.llm.anthropic.LazyImporter.import_module")
    def test_complete_success(self, mock_import: Mock) -> None:
        """Test successful completion call."""
        # Setup mocks
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.stop_sequence = None
        
        mock_content = Mock()
        mock_content.type = "text"
        mock_content.text = "Test response"
        mock_response.content = [mock_content]
        
        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 5
        mock_response.usage = mock_usage
        
        mock_client.messages.create.return_value = mock_response
        
        # Execute
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="claude-3-opus-20240229"
        )
        
        result = provider.complete(request)
        
        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.content == "Test response"
        assert result.provider == "anthropic"
        mock_client.messages.create.assert_called_once()
    
    @patch("nimbus.models.llm.anthropic.LazyImporter.import_module")
    def test_complete_error_handling(self, mock_import: Mock) -> None:
        """Test error handling in complete."""
        # Setup mocks
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client
        
        # Mock error
        mock_client.messages.create.side_effect = Exception("API Error")
        
        # Execute and verify error
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="claude-3-opus-20240229"
        )
        
        with pytest.raises(ProviderError) as exc_info:
            provider.complete(request)
        
        assert "Provider call failed" in str(exc_info.value)
        assert exc_info.value.details["provider"] == "anthropic"
    
    @patch("nimbus.models.llm.anthropic.LazyImporter.import_module")
    def test_stream_success(self, mock_import: Mock) -> None:
        """Test successful streaming call."""
        # Setup mocks
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client
        
        # Mock stream events
        mock_events = []
        for i, text in enumerate(["Hello", " ", "world"]):
            mock_event = Mock()
            mock_event.type = "content_block_delta"
            mock_event.message_id = "msg_123"
            mock_event.index = i
            mock_event.delta = Mock()
            mock_event.delta.text = text
            mock_events.append(mock_event)
        
        # Add final event
        mock_final = Mock()
        mock_final.type = "message_delta"
        mock_final.message_id = "msg_123"
        mock_final.index = 3
        mock_final.delta = Mock()
        mock_final.delta.stop_reason = "end_turn"
        mock_events.append(mock_final)
        
        # Mock stream context manager
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=iter(mock_events))
        mock_stream.__exit__ = Mock(return_value=False)
        mock_client.messages.stream.return_value = mock_stream
        
        # Execute
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="claude-3-opus-20240229",
            stream=True
        )
        
        chunks = list(provider.stream(request))
        
        # Verify
        assert len(chunks) == 4
        assert chunks[0].delta == "Hello"
        assert chunks[1].delta == " "
        assert chunks[2].delta == "world"
        assert chunks[3].finish_reason == "end_turn"


class TestAnthropicAsyncSupport:
    """Test async completion support."""
    
    @pytest.mark.asyncio
    @patch("nimbus.models.llm.anthropic.LazyImporter.import_module")
    async def test_acomplete_success(self, mock_import: Mock) -> None:
        """Test successful async completion."""
        # Setup mocks
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        
        # Mock async client
        mock_async_client = Mock()
        mock_anthropic.AsyncAnthropic.return_value = mock_async_client
        
        # Mock response
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.stop_sequence = None
        
        mock_content = Mock()
        mock_content.type = "text"
        mock_content.text = "Async response"
        mock_response.content = [mock_content]
        
        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 5
        mock_response.usage = mock_usage
        
        # Make the create method async
        async def async_create(**kwargs: Any) -> Any:
            return mock_response
        
        mock_async_client.messages.create = async_create
        
        # Execute
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="claude-3-opus-20240229"
        )
        
        result = await provider.acomplete(request)
        
        # Verify
        assert isinstance(result, CompletionResponse)
        assert result.content == "Async response"
        assert result.provider == "anthropic"


class TestAnthropicModelInfo:
    """Test model info retrieval."""
    
    def test_get_model_info(self) -> None:
        """Test getting model information."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        info = provider.get_model_info()
        
        assert info["provider"] == "anthropic"
        assert info["supports_streaming"] is True
        assert info["supports_function_calling"] is True
        assert info["supports_structured_output"] is False
        assert info["supports_multimodal"] is True
        assert info["supports_thinking"] is True


class TestAnthropicToolCalling:
    """Test tool calling integration with capabilities."""
    
    def test_transform_request_with_capabilities(self) -> None:
        """Test transformation of request with capabilities to Anthropic format."""
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
        
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather in NYC?")],
            model="claude-3-opus-20240229",
            capabilities=[mock_capability],
            capability_choice="auto"
        )
        
        result = provider._transform_request(request)
        
        # Verify tools are converted to Anthropic format
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "get_weather"
        assert result["tools"][0]["description"] == "Get weather for a location"
        assert result["tools"][0]["input_schema"]["type"] == "object"
        assert result["tools"][0]["input_schema"]["properties"]["location"]["type"] == "string"
        assert result["tool_choice"] == {"type": "auto"}
    
    def test_transform_request_with_specific_tool_choice(self) -> None:
        """Test transformation with specific tool name in tool_choice."""
        # Mock capability
        mock_capability = Mock()
        mock_schema = Mock()
        mock_schema.name = "get_weather"
        mock_schema.description = "Get weather"
        mock_schema.parameters = {"type": "object", "properties": {}}
        mock_capability.get_schema.return_value = mock_schema
        
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="claude-3-opus-20240229",
            capabilities=[mock_capability],
            capability_choice="get_weather"
        )
        
        result = provider._transform_request(request)
        
        # Verify tool_choice is formatted correctly for specific tool
        assert "tool_choice" in result
        assert result["tool_choice"]["type"] == "tool"
        assert result["tool_choice"]["name"] == "get_weather"
    
    def test_transform_request_with_required_tool_choice(self) -> None:
        """Test transformation with 'required' tool_choice."""
        # Mock capability
        mock_capability = Mock()
        mock_schema = Mock()
        mock_schema.name = "calculator"
        mock_schema.description = "Calculate"
        mock_schema.parameters = {"type": "object", "properties": {}}
        mock_capability.get_schema.return_value = mock_schema
        
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="Calculate 2+2")],
            model="claude-3-opus-20240229",
            capabilities=[mock_capability],
            capability_choice="required"
        )
        
        result = provider._transform_request(request)
        
        # Verify tool_choice is converted to Anthropic's "any" type
        assert result["tool_choice"] == {"type": "any"}
    
    def test_transform_response_with_capability_calls_creates_capability_call_objects(self) -> None:
        """Test that capability calls in response are converted to CapabilityCall objects."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock Anthropic response with tool use
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "tool_use"
        mock_response.stop_sequence = None
        
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.id = "toolu_abc123"
        mock_tool_use.name = "get_weather"
        mock_tool_use.input = {"location": "San Francisco", "unit": "celsius"}
        
        mock_response.content = [mock_tool_use]
        
        mock_usage = Mock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 20
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        # Verify capability_calls are present in response
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        
        # Verify CapabilityCall object structure
        capability_call = result.capability_calls[0]
        assert capability_call.id == "toolu_abc123"
        assert capability_call.name == "get_weather"
        assert capability_call.arguments == {"location": "San Francisco", "unit": "celsius"}
        
        # Verify metadata also contains tool calls
        assert result.metadata["tool_calls"] is not None
        assert len(result.metadata["tool_calls"]) == 1
        assert result.metadata["tool_calls"][0]["id"] == "toolu_abc123"
    
    def test_transform_response_with_parallel_capability_calls(self) -> None:
        """Test handling of parallel capability calls in response."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock Anthropic response with multiple tool uses
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "tool_use"
        mock_response.stop_sequence = None
        
        mock_tool_use_1 = Mock()
        mock_tool_use_1.type = "tool_use"
        mock_tool_use_1.id = "toolu_1"
        mock_tool_use_1.name = "get_weather"
        mock_tool_use_1.input = {"location": "NYC"}
        
        mock_tool_use_2 = Mock()
        mock_tool_use_2.type = "tool_use"
        mock_tool_use_2.id = "toolu_2"
        mock_tool_use_2.name = "get_time"
        mock_tool_use_2.input = {"timezone": "EST"}
        
        mock_response.content = [mock_tool_use_1, mock_tool_use_2]
        
        mock_usage = Mock()
        mock_usage.input_tokens = 60
        mock_usage.output_tokens = 30
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        # Verify both capability calls are present
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 2
        
        # Verify first capability call
        assert result.capability_calls[0].id == "toolu_1"
        assert result.capability_calls[0].name == "get_weather"
        assert result.capability_calls[0].arguments == {"location": "NYC"}
        
        # Verify second capability call
        assert result.capability_calls[1].id == "toolu_2"
        assert result.capability_calls[1].name == "get_time"
        assert result.capability_calls[1].arguments == {"timezone": "EST"}
    
    def test_transform_response_with_text_and_tool_use(self) -> None:
        """Test handling of response with both text and tool use."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
        # Mock Anthropic response with text and tool use
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "tool_use"
        mock_response.stop_sequence = None
        
        mock_text = Mock()
        mock_text.type = "text"
        mock_text.text = "Let me check the weather for you."
        
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.id = "toolu_123"
        mock_tool_use.name = "get_weather"
        mock_tool_use.input = {"location": "Boston"}
        
        mock_response.content = [mock_text, mock_tool_use]
        
        mock_usage = Mock()
        mock_usage.input_tokens = 40
        mock_usage.output_tokens = 25
        mock_response.usage = mock_usage
        
        result = provider._transform_response(mock_response)
        
        # Verify both text content and capability calls are present
        assert result.content == "Let me check the weather for you."
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        assert result.capability_calls[0].name == "get_weather"
    
    def test_transform_request_with_multiple_capabilities(self) -> None:
        """Test transformation with multiple capabilities."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        
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
            model="claude-3-opus-20240229",
            capabilities=[mock_capability_1, mock_capability_2]
        )
        
        result = provider._transform_request(request)
        
        # Verify both tools are present
        assert "tools" in result
        assert len(result["tools"]) == 2
        assert result["tools"][0]["name"] == "get_weather"
        assert result["tools"][1]["name"] == "get_time"
    
    @patch("nimbus.models.llm.anthropic.LazyImporter.import_module")
    def test_complete_with_capability_calls(self, mock_import: Mock) -> None:
        """Test end-to-end completion with capability calls."""
        # Setup mocks
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client
        
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
        
        # Mock response with tool use
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-opus-20240229"
        mock_response.stop_reason = "tool_use"
        mock_response.stop_sequence = None
        
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.id = "toolu_123"
        mock_tool_use.name = "get_weather"
        mock_tool_use.input = {"location": "Boston"}
        
        mock_response.content = [mock_tool_use]
        
        mock_usage = Mock()
        mock_usage.input_tokens = 40
        mock_usage.output_tokens = 15
        mock_response.usage = mock_usage
        
        mock_client.messages.create.return_value = mock_response
        
        # Execute
        provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="sk-ant-test")
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather in Boston?")],
            model="claude-3-opus-20240229",
            capabilities=[mock_capability],
            capability_choice="auto"
        )
        
        result = provider.complete(request)
        
        # Verify
        assert result.finish_reason == "tool_use"
        assert result.has_capability_calls()
        assert len(result.capability_calls) == 1
        assert result.capability_calls[0].name == "get_weather"
        
        # Verify the API was called with tools
        call_args = mock_client.messages.create.call_args
        assert "tools" in call_args[1]
        assert call_args[1]["tool_choice"] == {"type": "auto"}
