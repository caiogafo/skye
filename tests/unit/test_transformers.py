"""Unit tests for message transformers."""

from nimbus.messages import (
    AssistantMessage,
    CapabilityMessage,
    SystemMessage,
    UserMessage,
)
from nimbus.providers.transformers import MessageTransformer


class TestMessageTransformer:
    """Test MessageTransformer class."""

    def test_to_openai_format_basic(self):
        """Test basic OpenAI format conversion."""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="Hello!"),
            AssistantMessage(content="Hi there!"),
        ]

        result = MessageTransformer.to_openai_format(messages)

        assert len(result) == 3
        assert result[0] == {"role": "system", "content": "You are a helpful assistant."}
        assert result[1] == {"role": "user", "content": "Hello!"}
        assert result[2] == {"role": "assistant", "content": "Hi there!"}

    def test_to_openai_format_with_capability_calls(self):
        """Test OpenAI format with capability calls."""
        messages = [
            UserMessage(content="What's the weather?"),
            AssistantMessage(
                content="Let me check that for you.",
                capability_calls=[
                    {
                        "id": "call_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": {"city": "San Francisco"},
                        },
                    }
                ],
            ),
        ]

        result = MessageTransformer.to_openai_format(messages)

        assert len(result) == 2
        assert result[1]["role"] == "assistant"
        assert "tool_calls" in result[1]
        assert len(result[1]["tool_calls"]) == 1
        assert result[1]["tool_calls"][0]["id"] == "call_123"

    def test_to_openai_format_with_capability_message(self):
        """Test OpenAI format with capability result."""
        messages = [
            CapabilityMessage(
                content='{"temperature": 72, "condition": "sunny"}',
                capability_id="call_123",
                capability_name="get_weather",
            )
        ]

        result = MessageTransformer.to_openai_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "tool"
        assert result[0]["tool_call_id"] == "call_123"
        assert result[0]["name"] == "get_weather"
        assert "temperature" in result[0]["content"]

    def test_to_anthropic_format_basic(self):
        """Test basic Anthropic format conversion."""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="Hello!"),
            AssistantMessage(content="Hi there!"),
        ]

        system, result = MessageTransformer.to_anthropic_format(messages)

        assert system == "You are a helpful assistant."
        assert len(result) == 2
        assert result[0] == {"role": "user", "content": "Hello!"}
        assert result[1] == {"role": "assistant", "content": "Hi there!"}

    def test_to_anthropic_format_no_system(self):
        """Test Anthropic format without system message."""
        messages = [
            UserMessage(content="Hello!"),
            AssistantMessage(content="Hi there!"),
        ]

        system, result = MessageTransformer.to_anthropic_format(messages)

        assert system is None
        assert len(result) == 2

    def test_to_anthropic_format_with_capability_calls(self):
        """Test Anthropic format with tool use."""
        messages = [
            UserMessage(content="What's the weather?"),
            AssistantMessage(
                content="",
                capability_calls=[
                    {
                        "id": "call_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": {"city": "San Francisco"},
                        },
                    }
                ],
            ),
        ]

        system, result = MessageTransformer.to_anthropic_format(messages)

        assert len(result) == 2
        assert result[1]["role"] == "assistant"
        assert isinstance(result[1]["content"], list)
        assert result[1]["content"][0]["type"] == "tool_use"
        assert result[1]["content"][0]["id"] == "call_123"
        assert result[1]["content"][0]["name"] == "get_weather"

    def test_to_anthropic_format_with_capability_message(self):
        """Test Anthropic format with tool result."""
        messages = [
            CapabilityMessage(
                content='{"temperature": 72}',
                capability_id="call_123",
                capability_name="get_weather",
            )
        ]

        system, result = MessageTransformer.to_anthropic_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert isinstance(result[0]["content"], list)
        assert result[0]["content"][0]["type"] == "tool_result"
        assert result[0]["content"][0]["tool_use_id"] == "call_123"

    def test_to_bedrock_format_basic(self):
        """Test basic Bedrock format conversion."""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="Hello!"),
            AssistantMessage(content="Hi there!"),
        ]

        result = MessageTransformer.to_bedrock_format(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[0]["content"][0]["text"] == "You are a helpful assistant."
        assert result[1]["role"] == "user"
        assert result[1]["content"][0]["text"] == "Hello!"
        assert result[2]["role"] == "assistant"
        assert result[2]["content"][0]["text"] == "Hi there!"

    def test_to_bedrock_format_with_capability_calls(self):
        """Test Bedrock format with tool use."""
        messages = [
            UserMessage(content="What's the weather?"),
            AssistantMessage(
                content="",
                capability_calls=[
                    {
                        "id": "call_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": {"city": "San Francisco"},
                        },
                    }
                ],
            ),
        ]

        result = MessageTransformer.to_bedrock_format(messages)

        assert len(result) == 2
        assert result[1]["role"] == "assistant"
        assert "toolUse" in result[1]["content"][0]
        assert result[1]["content"][0]["toolUse"]["toolUseId"] == "call_123"
        assert result[1]["content"][0]["toolUse"]["name"] == "get_weather"

    def test_to_bedrock_format_with_capability_message(self):
        """Test Bedrock format with tool result."""
        messages = [
            CapabilityMessage(
                content='{"temperature": 72}',
                capability_id="call_123",
                capability_name="get_weather",
            )
        ]

        result = MessageTransformer.to_bedrock_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "toolResult" in result[0]["content"][0]
        assert result[0]["content"][0]["toolResult"]["toolUseId"] == "call_123"
        assert result[0]["content"][0]["toolResult"]["content"][0]["text"] == '{"temperature": 72}'

    def test_to_vertex_format_basic(self):
        """Test basic Vertex AI format conversion."""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="Hello!"),
            AssistantMessage(content="Hi there!"),
        ]

        result = MessageTransformer.to_vertex_format(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[0]["parts"][0]["text"] == "You are a helpful assistant."
        assert result[1]["role"] == "user"
        assert result[1]["parts"][0]["text"] == "Hello!"
        assert result[2]["role"] == "model"  # assistant -> model
        assert result[2]["parts"][0]["text"] == "Hi there!"

    def test_to_vertex_format_with_capability_calls(self):
        """Test Vertex AI format with function calls."""
        messages = [
            UserMessage(content="What's the weather?"),
            AssistantMessage(
                content="",
                capability_calls=[
                    {
                        "id": "call_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": {"city": "San Francisco"},
                        },
                    }
                ],
            ),
        ]

        result = MessageTransformer.to_vertex_format(messages)

        assert len(result) == 2
        assert result[1]["role"] == "model"
        assert "functionCall" in result[1]["parts"][0]
        assert result[1]["parts"][0]["functionCall"]["name"] == "get_weather"
        assert result[1]["parts"][0]["functionCall"]["args"] == {"city": "San Francisco"}

    def test_to_vertex_format_with_capability_message(self):
        """Test Vertex AI format with function response."""
        messages = [
            CapabilityMessage(
                content='{"temperature": 72}',
                capability_id="call_123",
                capability_name="get_weather",
            )
        ]

        result = MessageTransformer.to_vertex_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "functionResponse" in result[0]["parts"][0]
        assert result[0]["parts"][0]["functionResponse"]["name"] == "get_weather"
        assert "content" in result[0]["parts"][0]["functionResponse"]["response"]


class TestMessageTransformerEdgeCases:
    """Test edge cases for message transformers."""

    def test_empty_messages_openai(self):
        """Test OpenAI format with empty message list."""
        messages = []
        result = MessageTransformer.to_openai_format(messages)
        assert result == []

    def test_empty_messages_anthropic(self):
        """Test Anthropic format with empty message list."""
        messages = []
        system, result = MessageTransformer.to_anthropic_format(messages)
        assert system is None
        assert result == []

    def test_empty_messages_bedrock(self):
        """Test Bedrock format with empty message list."""
        messages = []
        result = MessageTransformer.to_bedrock_format(messages)
        assert result == []

    def test_empty_messages_vertex(self):
        """Test Vertex AI format with empty message list."""
        messages = []
        result = MessageTransformer.to_vertex_format(messages)
        assert result == []

    def test_messages_with_metadata(self):
        """Test that messages with metadata are transformed correctly."""
        messages = [
            UserMessage(
                content="Hello",
                metadata={"source": "web", "user_id": "123"},
            )
        ]

        # Metadata should not affect transformation
        openai_result = MessageTransformer.to_openai_format(messages)
        assert openai_result[0]["role"] == "user"
        assert openai_result[0]["content"] == "Hello"
        # Metadata is not included in provider format
        assert "metadata" not in openai_result[0]

    def test_multiple_capability_calls(self):
        """Test multiple capability calls in a single message."""
        messages = [
            AssistantMessage(
                content="Let me check multiple things.",
                capability_calls=[
                    {
                        "id": "call_1",
                        "function": {"name": "get_weather", "arguments": {"city": "SF"}},
                    },
                    {
                        "id": "call_2",
                        "function": {"name": "get_time", "arguments": {"timezone": "PST"}},
                    },
                ],
            )
        ]

        openai_result = MessageTransformer.to_openai_format(messages)
        assert len(openai_result[0]["tool_calls"]) == 2

        system, anthropic_result = MessageTransformer.to_anthropic_format(messages)
        assert len(anthropic_result[0]["content"]) == 2

        bedrock_result = MessageTransformer.to_bedrock_format(messages)
        assert len(bedrock_result[0]["content"]) == 2

        vertex_result = MessageTransformer.to_vertex_format(messages)
        assert len(vertex_result[0]["parts"]) == 2

    def test_empty_content(self):
        """Test messages with empty content."""
        messages = [UserMessage(content="")]

        openai_result = MessageTransformer.to_openai_format(messages)
        assert openai_result[0]["content"] == ""

        system, anthropic_result = MessageTransformer.to_anthropic_format(messages)
        assert anthropic_result[0]["content"] == ""

        bedrock_result = MessageTransformer.to_bedrock_format(messages)
        assert bedrock_result[0]["content"][0]["text"] == ""

        vertex_result = MessageTransformer.to_vertex_format(messages)
        assert vertex_result[0]["parts"][0]["text"] == ""

    def test_mixed_message_types(self):
        """Test a complex conversation with all message types."""
        messages = [
            SystemMessage(content="You are helpful."),
            UserMessage(content="What's the weather?"),
            AssistantMessage(
                content="Checking...",
                capability_calls=[
                    {
                        "id": "call_1",
                        "function": {"name": "get_weather", "arguments": {"city": "NYC"}},
                    }
                ],
            ),
            CapabilityMessage(
                content='{"temp": 70}',
                capability_id="call_1",
                capability_name="get_weather",
            ),
            AssistantMessage(content="It's 70 degrees in NYC."),
        ]

        # Test all formats handle the complex conversation
        openai_result = MessageTransformer.to_openai_format(messages)
        assert len(openai_result) == 5

        system, anthropic_result = MessageTransformer.to_anthropic_format(messages)
        assert system == "You are helpful."
        assert len(anthropic_result) == 4

        bedrock_result = MessageTransformer.to_bedrock_format(messages)
        assert len(bedrock_result) == 5

        vertex_result = MessageTransformer.to_vertex_format(messages)
        assert len(vertex_result) == 5

    def test_assistant_message_without_capability_calls(self):
        """Test assistant message with empty capability_calls list."""
        messages = [
            AssistantMessage(content="Hello", capability_calls=[])
        ]

        openai_result = MessageTransformer.to_openai_format(messages)
        # Empty capability_calls should not add tool_calls field
        assert "tool_calls" not in openai_result[0]
        assert openai_result[0]["content"] == "Hello"

    def test_multiple_system_messages_anthropic(self):
        """Test Anthropic format with multiple system messages (last one wins)."""
        messages = [
            SystemMessage(content="First system message."),
            SystemMessage(content="Second system message."),
            UserMessage(content="Hello"),
        ]

        system, result = MessageTransformer.to_anthropic_format(messages)
        # Last system message should be used
        assert system == "Second system message."
        assert len(result) == 1

    def test_multimodal_messages_with_images(self):
        """Test that messages with image content are transformed correctly.

        Note: This tests the transformer's ability to handle messages that
        would contain image data. Actual image processing is handled by
        ImageHandler (task 4).
        """
        # Simulate a message that would contain image data
        # In practice, this would be processed by ImageHandler first
        messages = [
            UserMessage(
                content="What's in this image?",
                metadata={"has_image": True, "image_url": "https://example.com/image.jpg"},
            )
        ]

        # Test that transformers handle messages with image metadata
        openai_result = MessageTransformer.to_openai_format(messages)
        assert openai_result[0]["role"] == "user"
        assert openai_result[0]["content"] == "What's in this image?"

        system, anthropic_result = MessageTransformer.to_anthropic_format(messages)
        assert anthropic_result[0]["role"] == "user"
        assert anthropic_result[0]["content"] == "What's in this image?"

        bedrock_result = MessageTransformer.to_bedrock_format(messages)
        assert bedrock_result[0]["role"] == "user"
        assert bedrock_result[0]["content"][0]["text"] == "What's in this image?"

        vertex_result = MessageTransformer.to_vertex_format(messages)
        assert vertex_result[0]["role"] == "user"
        assert vertex_result[0]["parts"][0]["text"] == "What's in this image?"

    def test_function_call_messages_complete_flow(self):
        """Test complete function call flow with all message types."""
        messages = [
            UserMessage(content="Calculate 5 + 3"),
            AssistantMessage(
                content="I'll calculate that for you.",
                capability_calls=[
                    {
                        "id": "call_calc",
                        "function": {
                            "name": "calculator",
                            "arguments": {"operation": "add", "a": 5, "b": 3},
                        },
                    }
                ],
            ),
            CapabilityMessage(
                content="8",
                capability_id="call_calc",
                capability_name="calculator",
            ),
            AssistantMessage(content="The result is 8."),
        ]

        # Test OpenAI format
        openai_result = MessageTransformer.to_openai_format(messages)
        assert len(openai_result) == 4
        assert openai_result[1]["tool_calls"][0]["function"]["name"] == "calculator"
        assert openai_result[2]["role"] == "tool"
        assert openai_result[2]["content"] == "8"

        # Test Anthropic format
        system, anthropic_result = MessageTransformer.to_anthropic_format(messages)
        assert len(anthropic_result) == 4
        assert anthropic_result[1]["content"][0]["type"] == "tool_use"
        assert anthropic_result[2]["content"][0]["type"] == "tool_result"

        # Test Bedrock format
        bedrock_result = MessageTransformer.to_bedrock_format(messages)
        assert len(bedrock_result) == 4
        assert "toolUse" in bedrock_result[1]["content"][0]
        assert "toolResult" in bedrock_result[2]["content"][0]

        # Test Vertex format
        vertex_result = MessageTransformer.to_vertex_format(messages)
        assert len(vertex_result) == 4
        assert "functionCall" in vertex_result[1]["parts"][0]
        assert "functionResponse" in vertex_result[2]["parts"][0]
