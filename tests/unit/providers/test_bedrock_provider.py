"""Unit tests for BedrockProvider.

These tests verify the Bedrock provider implementation including:
- Optional boto3 import (pre-installed vs lazy import)
- Request transformation to Bedrock Converse API format
- Response transformation from Bedrock to CompletionResponse
- Tool use format handling
- Streaming support
"""

import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from nimbus.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.messages import AssistantMessage, SystemMessage, UserMessage
from nimbus.providers.llm.bedrock_provider import BedrockProvider


class TestBedrockProviderInitialization:
    """Test BedrockProvider initialization and client setup."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        provider = BedrockProvider()
        assert provider.region_name == "us-east-1"
        assert provider.profile_name is None
    
    def test_init_with_custom_region(self):
        """Test initialization with custom region."""
        provider = BedrockProvider(region_name="us-west-2")
        assert provider.region_name == "us-west-2"
    
    def test_init_with_profile(self):
        """Test initialization with AWS profile."""
        provider = BedrockProvider(region_name="us-east-1", profile_name="my-profile")
        assert provider.profile_name == "my-profile"
    
    @patch("nimbus.providers.llm.bedrock_provider.LazyImporter.import_module")
    def test_initialize_client_with_lazy_import(self, mock_import):
        """Test client initialization with lazy boto3 import."""
        # Setup mock boto3
        mock_boto3 = MagicMock()
        mock_session = MagicMock()
        mock_client = MagicMock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_import.return_value = mock_boto3
        
        # Ensure boto3 is not in sys.modules
        if "boto3" in sys.modules:
            del sys.modules["boto3"]
        
        provider = BedrockProvider(region_name="us-west-2", profile_name="test-profile")
        client = provider.client
        
        # Verify lazy import was called
        mock_import.assert_called_once_with(
            "boto3",
            package_name="boto3",
            install_extra="bedrock"
        )
        
        # Verify session was created with correct parameters
        mock_boto3.Session.assert_called_once_with(
            region_name="us-west-2",
            profile_name="test-profile"
        )
        
        # Verify bedrock-runtime client was created
        mock_session.client.assert_called_once_with("bedrock-runtime")
        assert client == mock_client
    
    def test_initialize_client_with_preinstalled_boto3(self):
        """Test client initialization with pre-installed boto3 (Lambda scenario)."""
        # Setup mock boto3 in sys.modules
        mock_boto3 = MagicMock()
        mock_session = MagicMock()
        mock_client = MagicMock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            provider = BedrockProvider(region_name="us-east-1")
            client = provider.client
            
            # Verify session was created
            mock_boto3.Session.assert_called_once_with(
                region_name="us-east-1",
                profile_name=None
            )
            
            # Verify bedrock-runtime client was created
            mock_session.client.assert_called_once_with("bedrock-runtime")
            assert client == mock_client


class TestBedrockRequestTransformation:
    """Test request transformation to Bedrock Converse API format."""
    
    def test_transform_basic_request(self):
        """Test transformation of basic completion request."""
        provider = BedrockProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="Hello, world!")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            temperature=0.7
        )
        
        bedrock_request = provider._transform_request(request)
        
        assert bedrock_request["modelId"] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert bedrock_request["inferenceConfig"]["temperature"] == 0.7
        assert len(bedrock_request["messages"]) == 1
        assert bedrock_request["messages"][0]["role"] == "user"
        assert bedrock_request["messages"][0]["content"][0]["text"] == "Hello, world!"
    
    def test_transform_request_with_system_message(self):
        """Test transformation with system message."""
        provider = BedrockProvider()
        request = CompletionRequest(
            messages=[
                SystemMessage(content="You are a helpful assistant"),
                UserMessage(content="Hello")
            ],
            model="anthropic.claude-3-sonnet-20240229-v1:0"
        )
        
        bedrock_request = provider._transform_request(request)
        
        # System message should be in messages array for Bedrock
        assert len(bedrock_request["messages"]) == 2
        assert bedrock_request["messages"][0]["role"] == "system"
        assert bedrock_request["messages"][0]["content"][0]["text"] == "You are a helpful assistant"
    
    def test_transform_request_with_max_tokens(self):
        """Test transformation with max_tokens parameter."""
        provider = BedrockProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            max_tokens=1000
        )
        
        bedrock_request = provider._transform_request(request)
        
        assert bedrock_request["inferenceConfig"]["maxTokens"] == 1000
    
    def test_transform_request_with_top_p(self):
        """Test transformation with top_p parameter."""
        provider = BedrockProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            top_p=0.9
        )
        
        bedrock_request = provider._transform_request(request)
        
        assert bedrock_request["inferenceConfig"]["topP"] == 0.9
    
    def test_transform_request_with_stop_sequences(self):
        """Test transformation with stop sequences."""
        provider = BedrockProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            stop=["STOP", "END"]
        )
        
        bedrock_request = provider._transform_request(request)
        
        assert bedrock_request["inferenceConfig"]["stopSequences"] == ["STOP", "END"]
    
    def test_transform_request_with_capabilities(self):
        """Test transformation with function/tool calling."""
        provider = BedrockProvider()
        capabilities = [
            {
                "name": "get_weather",
                "description": "Get weather information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        ]
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            capabilities=capabilities
        )
        
        bedrock_request = provider._transform_request(request)
        
        assert "toolConfig" in bedrock_request
        assert len(bedrock_request["toolConfig"]["tools"]) == 1
        assert bedrock_request["toolConfig"]["tools"][0]["toolSpec"] == capabilities[0]
    
    def test_transform_request_with_bedrock_metadata(self):
        """Test transformation with Bedrock-specific metadata."""
        provider = BedrockProvider()
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            metadata={
                "bedrock_system": [{"text": "Custom system prompt"}],
                "bedrock_additionalModelRequestFields": {"top_k": 250}
            }
        )
        
        bedrock_request = provider._transform_request(request)
        
        assert bedrock_request["system"] == [{"text": "Custom system prompt"}]
        assert bedrock_request["additionalModelRequestFields"] == {"top_k": 250}
    
    def test_transform_request_without_messages_raises_error(self):
        """Test that transformation fails without messages."""
        provider = BedrockProvider()
        request = CompletionRequest(
            messages=[],
            model="anthropic.claude-3-sonnet-20240229-v1:0"
        )
        
        with pytest.raises(ValueError, match="messages must be provided"):
            provider._transform_request(request)


class TestBedrockResponseTransformation:
    """Test response transformation from Bedrock to CompletionResponse."""
    
    def test_transform_basic_response(self):
        """Test transformation of basic Bedrock response."""
        provider = BedrockProvider()
        bedrock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "Hello! How can I help you today?"}
                    ]
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 10,
                "outputTokens": 20,
                "totalTokens": 30
            },
            "ResponseMetadata": {
                "RequestId": "test-request-id",
                "HTTPHeaders": {
                    "x-amzn-bedrock-model-id": "anthropic.claude-3-sonnet-20240229-v1:0"
                }
            }
        }
        
        response = provider._transform_response(bedrock_response)
        
        assert isinstance(response, CompletionResponse)
        assert response.content == "Hello! How can I help you today?"
        assert response.provider == "bedrock"
        assert response.role == "assistant"
        assert response.finish_reason == "stop"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30
        assert response.id == "test-request-id"
    
    def test_transform_response_with_tool_use(self):
        """Test transformation of response with tool use."""
        provider = BedrockProvider()
        bedrock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-123",
                                "name": "get_weather",
                                "input": {"location": "San Francisco"}
                            }
                        }
                    ]
                }
            },
            "stopReason": "tool_use",
            "usage": {
                "inputTokens": 15,
                "outputTokens": 25,
                "totalTokens": 40
            },
            "ResponseMetadata": {
                "RequestId": "test-request-id",
                "HTTPHeaders": {}
            }
        }
        
        response = provider._transform_response(bedrock_response)
        
        assert response.finish_reason == "tool_calls"
        assert response.metadata["tool_calls"] is not None
        assert len(response.metadata["tool_calls"]) == 1
        
        tool_call = response.metadata["tool_calls"][0]
        assert tool_call["id"] == "tool-123"
        assert tool_call["type"] == "function"
        assert tool_call["function"]["name"] == "get_weather"
        assert tool_call["function"]["arguments"] == {"location": "San Francisco"}
    
    def test_transform_response_with_multiple_content_blocks(self):
        """Test transformation with multiple text content blocks."""
        provider = BedrockProvider()
        bedrock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "First part. "},
                        {"text": "Second part."}
                    ]
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 10,
                "outputTokens": 15,
                "totalTokens": 25
            },
            "ResponseMetadata": {
                "RequestId": "test-request-id",
                "HTTPHeaders": {}
            }
        }
        
        response = provider._transform_response(bedrock_response)
        
        assert response.content == "First part. Second part."
    
    def test_transform_response_stop_reason_mapping(self):
        """Test stop reason mapping from Bedrock to standard format."""
        provider = BedrockProvider()
        
        stop_reason_tests = [
            ("end_turn", "stop"),
            ("tool_use", "tool_calls"),
            ("max_tokens", "length"),
            ("stop_sequence", "stop"),
            ("content_filtered", "content_filter"),
            ("unknown_reason", "unknown_reason")  # Unmapped reasons pass through
        ]
        
        for bedrock_reason, expected_reason in stop_reason_tests:
            bedrock_response = {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "Test"}]
                    }
                },
                "stopReason": bedrock_reason,
                "usage": {"inputTokens": 5, "outputTokens": 5, "totalTokens": 10},
                "ResponseMetadata": {"RequestId": "test", "HTTPHeaders": {}}
            }
            
            response = provider._transform_response(bedrock_response)
            assert response.finish_reason == expected_reason


class TestBedrockStreamTransformation:
    """Test stream chunk transformation."""
    
    def test_transform_content_block_delta(self):
        """Test transformation of content block delta event."""
        provider = BedrockProvider()
        chunk = {
            "contentBlockDelta": {
                "delta": {
                    "text": "Hello"
                },
                "contentBlockIndex": 0
            }
        }
        
        stream_chunk = provider._transform_stream_chunk(chunk)
        
        assert isinstance(stream_chunk, StreamChunk)
        assert stream_chunk.delta == "Hello"
        assert stream_chunk.finish_reason is None
        assert stream_chunk.index == 0
    
    def test_transform_message_stop_event(self):
        """Test transformation of message stop event."""
        provider = BedrockProvider()
        chunk = {
            "messageStop": {
                "stopReason": "end_turn"
            }
        }
        
        stream_chunk = provider._transform_stream_chunk(chunk)
        
        assert stream_chunk.delta == ""
        assert stream_chunk.finish_reason == "stop"
    
    def test_transform_empty_chunk(self):
        """Test transformation of empty/unknown chunk."""
        provider = BedrockProvider()
        chunk = {}
        
        stream_chunk = provider._transform_stream_chunk(chunk)
        
        assert stream_chunk.delta == ""
        assert stream_chunk.finish_reason is None


class TestBedrockProviderCalls:
    """Test provider API calls."""
    
    @patch("nimbus.providers.llm.bedrock_provider.LazyImporter.import_module")
    def test_call_provider(self, mock_import):
        """Test synchronous provider call."""
        # Setup mock client
        mock_boto3 = MagicMock()
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_response = {"output": {"message": {"content": [{"text": "Response"}]}}}
        
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.converse.return_value = mock_response
        mock_import.return_value = mock_boto3
        
        # Ensure boto3 is not in sys.modules
        if "boto3" in sys.modules:
            del sys.modules["boto3"]
        
        provider = BedrockProvider()
        request = {"modelId": "test-model", "messages": []}
        
        response = provider._call_provider(request)
        
        mock_client.converse.assert_called_once_with(**request)
        assert response == mock_response
    
    @patch("nimbus.providers.llm.bedrock_provider.LazyImporter.import_module")
    def test_call_provider_stream(self, mock_import):
        """Test streaming provider call."""
        # Setup mock client
        mock_boto3 = MagicMock()
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_stream = [
            {"contentBlockDelta": {"delta": {"text": "Hello"}}},
            {"messageStop": {"stopReason": "end_turn"}}
        ]
        mock_response = {"stream": mock_stream}
        
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.converse_stream.return_value = mock_response
        mock_import.return_value = mock_boto3
        
        # Ensure boto3 is not in sys.modules
        if "boto3" in sys.modules:
            del sys.modules["boto3"]
        
        provider = BedrockProvider()
        request = {"modelId": "test-model", "messages": []}
        
        stream = provider._call_provider_stream(request)
        chunks = list(stream)
        
        mock_client.converse_stream.assert_called_once_with(**request)
        assert len(chunks) == 2
        assert chunks[0] == mock_stream[0]
        assert chunks[1] == mock_stream[1]


class TestBedrockModelInfo:
    """Test model info and capabilities."""
    
    def test_get_model_info(self):
        """Test get_model_info returns correct capabilities."""
        provider = BedrockProvider()
        info = provider.get_model_info()
        
        assert info["provider"] == "bedrock"
        assert info["supports_streaming"] is True
        assert info["supports_function_calling"] is True
        assert info["supports_structured_output"] is False
        assert info["supports_multimodal"] is True


class TestBedrockToolCalling:
    """Test tool calling integration with capabilities."""
    
    def test_transform_request_with_capabilities(self):
        """Test transformation of request with capabilities to Bedrock format."""
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
        
        provider = BedrockProvider(model="anthropic.claude-3-sonnet-20240229-v1:0")
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather in NYC?")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            capabilities=[mock_capability],
            capability_choice="auto"
        )
        
        result = provider._transform_request(request)
        
        # Verify tools are converted to Bedrock format
        assert "toolConfig" in result
        assert "tools" in result["toolConfig"]
        assert len(result["toolConfig"]["tools"]) == 1
        
        # Verify Bedrock toolSpec format
        tool = result["toolConfig"]["tools"][0]
        assert "toolSpec" in tool
        assert tool["toolSpec"]["name"] == "get_weather"
        assert tool["toolSpec"]["description"] == "Get weather for a location"
        assert "inputSchema" in tool["toolSpec"]
        assert "json" in tool["toolSpec"]["inputSchema"]
        
        # Verify tool_choice is formatted correctly
        assert "toolChoice" in result["toolConfig"]
        assert "auto" in result["toolConfig"]["toolChoice"]
    
    def test_transform_request_with_specific_tool_choice(self):
        """Test transformation with specific tool name in tool_choice."""
        # Mock capability
        mock_capability = Mock()
        mock_schema = Mock()
        mock_schema.name = "get_weather"
        mock_schema.description = "Get weather"
        mock_schema.parameters = {"type": "object", "properties": {}}
        mock_capability.get_schema.return_value = mock_schema
        
        provider = BedrockProvider(model="anthropic.claude-3-sonnet-20240229-v1:0")
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            capabilities=[mock_capability],
            capability_choice="get_weather"
        )
        
        result = provider._transform_request(request)
        
        # Verify tool_choice is formatted correctly for specific tool
        assert "toolChoice" in result["toolConfig"]
        assert "tool" in result["toolConfig"]["toolChoice"]
        assert result["toolConfig"]["toolChoice"]["tool"]["name"] == "get_weather"
    
    def test_transform_request_with_required_tool_choice(self):
        """Test transformation with 'required' tool_choice."""
        # Mock capability
        mock_capability = Mock()
        mock_schema = Mock()
        mock_schema.name = "calculator"
        mock_schema.description = "Calculate"
        mock_schema.parameters = {"type": "object", "properties": {}}
        mock_capability.get_schema.return_value = mock_schema
        
        provider = BedrockProvider(model="anthropic.claude-3-sonnet-20240229-v1:0")
        request = CompletionRequest(
            messages=[UserMessage(content="Calculate 2+2")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            capabilities=[mock_capability],
            capability_choice="required"
        )
        
        result = provider._transform_request(request)
        
        # Verify tool_choice is formatted correctly for 'required' (maps to 'any' in Bedrock)
        assert "toolChoice" in result["toolConfig"]
        assert "any" in result["toolConfig"]["toolChoice"]
    
    def test_transform_response_with_tool_calls_creates_tool_call_objects(self):
        """Test that tool calls in response are converted to CapabilityCall objects."""
        provider = BedrockProvider(model="anthropic.claude-3-sonnet-20240229-v1:0")
        
        # Mock Bedrock response with tool use
        bedrock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_abc123",
                                "name": "get_weather",
                                "input": {"location": "San Francisco", "unit": "celsius"}
                            }
                        }
                    ]
                }
            },
            "stopReason": "tool_use",
            "usage": {
                "inputTokens": 50,
                "outputTokens": 20,
                "totalTokens": 70
            },
            "ResponseMetadata": {
                "RequestId": "test-request-id",
                "HTTPHeaders": {}
            }
        }
        
        result = provider._transform_response(bedrock_response)
        
        # Verify capability_calls are present in response
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        
        # Verify CapabilityCall object structure
        capability_call = result.capability_calls[0]
        assert capability_call.id == "tooluse_abc123"
        assert capability_call.name == "get_weather"
        assert capability_call.arguments == {"location": "San Francisco", "unit": "celsius"}
        
        # Verify metadata also contains raw tool calls
        assert result.metadata["tool_calls"] is not None
        assert len(result.metadata["tool_calls"]) == 1
        assert result.metadata["tool_calls"][0]["id"] == "tooluse_abc123"
        assert result.finish_reason == "tool_calls"
    
    def test_transform_response_with_parallel_tool_calls(self):
        """Test handling of parallel tool calls in response."""
        provider = BedrockProvider(model="anthropic.claude-3-sonnet-20240229-v1:0")
        
        # Mock Bedrock response with multiple parallel tool calls
        bedrock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_1",
                                "name": "get_weather",
                                "input": {"location": "NYC"}
                            }
                        },
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_2",
                                "name": "get_time",
                                "input": {"timezone": "EST"}
                            }
                        }
                    ]
                }
            },
            "stopReason": "tool_use",
            "usage": {
                "inputTokens": 60,
                "outputTokens": 30,
                "totalTokens": 90
            },
            "ResponseMetadata": {
                "RequestId": "test-request-id",
                "HTTPHeaders": {}
            }
        }
        
        result = provider._transform_response(bedrock_response)
        
        # Verify both capability calls are present
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 2
        
        # Verify first capability call
        assert result.capability_calls[0].id == "tooluse_1"
        assert result.capability_calls[0].name == "get_weather"
        assert result.capability_calls[0].arguments == {"location": "NYC"}
        
        # Verify second capability call
        assert result.capability_calls[1].id == "tooluse_2"
        assert result.capability_calls[1].name == "get_time"
        assert result.capability_calls[1].arguments == {"timezone": "EST"}
    
    def test_transform_response_with_text_and_tool_use(self):
        """Test handling of response with both text and tool use."""
        provider = BedrockProvider(model="anthropic.claude-3-sonnet-20240229-v1:0")
        
        # Mock Bedrock response with text and tool use
        bedrock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "Let me check the weather for you. "},
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_123",
                                "name": "get_weather",
                                "input": {"location": "Boston"}
                            }
                        }
                    ]
                }
            },
            "stopReason": "tool_use",
            "usage": {
                "inputTokens": 40,
                "outputTokens": 25,
                "totalTokens": 65
            },
            "ResponseMetadata": {
                "RequestId": "test-request-id",
                "HTTPHeaders": {}
            }
        }
        
        result = provider._transform_response(bedrock_response)
        
        # Verify both text content and tool calls are present
        assert result.content == "Let me check the weather for you. "
        assert result.capability_calls is not None
        assert len(result.capability_calls) == 1
        assert result.capability_calls[0].name == "get_weather"
    
    def test_transform_request_with_multiple_capabilities(self):
        """Test transformation with multiple capabilities."""
        provider = BedrockProvider(model="anthropic.claude-3-sonnet-20240229-v1:0")
        
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
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            capabilities=[mock_capability_1, mock_capability_2]
        )
        
        result = provider._transform_request(request)
        
        # Verify both tools are present
        assert "toolConfig" in result
        assert len(result["toolConfig"]["tools"]) == 2
        assert result["toolConfig"]["tools"][0]["toolSpec"]["name"] == "get_weather"
        assert result["toolConfig"]["tools"][1]["toolSpec"]["name"] == "get_time"
    
    @patch("nimbus.providers.llm.bedrock_provider.LazyImporter.import_module")
    def test_complete_with_tool_calls(self, mock_import):
        """Test end-to-end completion with tool calls."""
        # Setup mocks
        mock_boto3 = MagicMock()
        mock_session = MagicMock()
        mock_client = MagicMock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_import.return_value = mock_boto3
        
        # Ensure boto3 is not in sys.modules
        if "boto3" in sys.modules:
            del sys.modules["boto3"]
        
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
        mock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_123",
                                "name": "get_weather",
                                "input": {"location": "Boston"}
                            }
                        }
                    ]
                }
            },
            "stopReason": "tool_use",
            "usage": {
                "inputTokens": 40,
                "outputTokens": 15,
                "totalTokens": 55
            },
            "ResponseMetadata": {
                "RequestId": "test-request-id",
                "HTTPHeaders": {}
            }
        }
        
        mock_client.converse.return_value = mock_response
        
        # Execute
        provider = BedrockProvider(model="anthropic.claude-3-sonnet-20240229-v1:0")
        request = CompletionRequest(
            messages=[UserMessage(content="What's the weather in Boston?")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
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
        call_args = mock_client.converse.call_args[1]
        assert "toolConfig" in call_args
        assert "tools" in call_args["toolConfig"]
        assert "toolChoice" in call_args["toolConfig"]


class TestBedrockIntegration:
    """Integration tests for complete request/response flow."""
    
    @patch("nimbus.providers.llm.bedrock_provider.LazyImporter.import_module")
    def test_complete_request_flow(self, mock_import):
        """Test complete request flow from CompletionRequest to CompletionResponse."""
        # Setup mock client
        mock_boto3 = MagicMock()
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Hello! How can I help?"}]
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 10,
                "outputTokens": 15,
                "totalTokens": 25
            },
            "ResponseMetadata": {
                "RequestId": "test-123",
                "HTTPHeaders": {
                    "x-amzn-bedrock-model-id": "anthropic.claude-3-sonnet-20240229-v1:0"
                }
            }
        }
        
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.converse.return_value = mock_response
        mock_import.return_value = mock_boto3
        
        # Ensure boto3 is not in sys.modules
        if "boto3" in sys.modules:
            del sys.modules["boto3"]
        
        provider = BedrockProvider(region_name="us-west-2")
        request = CompletionRequest(
            messages=[UserMessage(content="Hello")],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            temperature=0.7,
            max_tokens=1000
        )
        
        response = provider.complete(request)
        
        assert isinstance(response, CompletionResponse)
        assert response.content == "Hello! How can I help?"
        assert response.provider == "bedrock"
        assert response.usage.total_tokens == 25
        
        # Verify the client was called with correct parameters
        call_args = mock_client.converse.call_args[1]
        assert call_args["modelId"] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert call_args["inferenceConfig"]["temperature"] == 0.7
        assert call_args["inferenceConfig"]["maxTokens"] == 1000
