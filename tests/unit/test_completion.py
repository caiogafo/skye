"""Unit tests for completion models."""

from datetime import datetime

import pytest
from skye.base.validated import Validated, validated

from skye.base.completion import (
    CompleteRequest,
    CompleteResponse,
    StreamChunk,
    TokenUsage,
)
from skye.base.exceptions import ValidationError
from skye.base.messages import UserMessage


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_token_usage_creation(self):
        """Test creating a TokenUsage instance."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30

    def test_token_usage_validation(self):
        """Test TokenUsage validates required fields."""
        with pytest.raises(ValidationError):
            TokenUsage(prompt_tokens=10)  # Missing required fields


class TestCompleteRequest:
    """Tests for CompleteRequest model."""

    def test_completion_request_minimal(self):
        """Test creating a minimal CompleteRequest."""
        request = CompleteRequest(messages=[UserMessage(content="Hello")], model="gpt-4")
        assert len(request.messages) == 1
        assert request.model == "gpt-4"
        assert request.temperature == 0.7  # Default
        assert request.top_p == 1.0  # Default
        assert request.stream is False  # Default

    def test_completion_request_with_parameters(self):
        """Test CompleteRequest with custom parameters."""
        request = CompleteRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            temperature=0.5,
            max_tokens=100,
            top_p=0.9,
            stop=["END"],
            stream=True,
        )
        assert request.temperature == 0.5
        assert request.max_tokens == 100
        assert request.top_p == 0.9
        assert request.stop == ["END"]
        assert request.stream is True

    def test_temperature_validation(self):
        """Test temperature must be between 0.0 and 2.0."""
        # Valid temperatures
        CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", temperature=0.0)
        CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", temperature=2.0)

        # Invalid temperatures
        with pytest.raises(ValidationError):
            CompleteRequest(
                messages=[UserMessage(content="test")], model="gpt-4", temperature=-0.1
            )

        with pytest.raises(ValidationError):
            CompleteRequest(
                messages=[UserMessage(content="test")], model="gpt-4", temperature=2.1
            )

    def test_top_p_validation(self):
        """Test top_p must be between 0.0 and 1.0."""
        # Valid top_p
        CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", top_p=0.0)
        CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", top_p=1.0)

        # Invalid top_p
        with pytest.raises(ValidationError):
            CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", top_p=-0.1)

        with pytest.raises(ValidationError):
            CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", top_p=1.1)

    def test_max_tokens_validation(self):
        """Test max_tokens must be positive."""
        # Valid max_tokens
        CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", max_tokens=100)

        # Invalid max_tokens
        with pytest.raises(ValidationError):
            CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", max_tokens=0)

        with pytest.raises(ValidationError):
            CompleteRequest(messages=[UserMessage(content="test")], model="gpt-4", max_tokens=-1)

    def test_capabilities_field(self):
        """Test capabilities field for tool/function calling."""
        capabilities = [
            {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {"location": "string"},
            }
        ]
        request = CompleteRequest(
            messages=[UserMessage(content="What's the weather?")],
            model="gpt-4",
            capabilities=capabilities,
            capability_choice="auto",
        )
        assert request.capabilities == capabilities
        assert request.capability_choice == "auto"

    def test_structured_output_fields(self):
        """Test response_format and response_schema fields."""

        @validated
        class OutputSchema(Validated):
            answer: str
            confidence: float

        request = CompleteRequest(
            messages=[UserMessage(content="Answer this")],
            model="gpt-4",
            response_format={"type": "json_object"},
            response_schema=OutputSchema,
        )
        assert request.response_format == {"type": "json_object"}
        assert request.response_schema == OutputSchema

    def test_metadata_field(self):
        """Test metadata field for additional context."""
        request = CompleteRequest(
            messages=[UserMessage(content="test")],
            model="gpt-4",
            metadata={"user_id": "123", "session_id": "abc"},
        )
        assert request.metadata["user_id"] == "123"
        assert request.metadata["session_id"] == "abc"

    def test_completion_request_capabilities(self):
        """Test CompleteRequest with capabilities field."""
        # Test with None (default)
        request = CompleteRequest(messages=[UserMessage(content="Hello")], model="gpt-4")
        assert request.capabilities is None
        assert request.capability_choice is None

        # Test with empty list
        request = CompleteRequest(
            messages=[UserMessage(content="Hello")], model="gpt-4", capabilities=[]
        )
        assert request.capabilities == []

        # Test with mock capabilities (using dict as placeholder since we don't want to import capabilities)
        mock_capabilities = [
            {"name": "get_weather", "description": "Get weather"},
            {"name": "search", "description": "Search the web"},
        ]
        request = CompleteRequest(
            messages=[UserMessage(content="Hello")],
            model="gpt-4",
            capabilities=mock_capabilities,
        )
        assert len(request.capabilities) == 2
        assert request.capabilities[0]["name"] == "get_weather"

    def test_completion_request_capability_choice_validation(self):
        """Test capability_choice field validation."""
        # Valid: None (default)
        request = CompleteRequest(messages=[UserMessage(content="Hello")], model="gpt-4")
        assert request.capability_choice is None

        # Valid: "auto"
        request = CompleteRequest(
            messages=[UserMessage(content="Hello")], model="gpt-4", capability_choice="auto"
        )
        assert request.capability_choice == "auto"

        # Valid: "required"
        request = CompleteRequest(
            messages=[UserMessage(content="Hello")], model="gpt-4", capability_choice="required"
        )
        assert request.capability_choice == "required"

        # Valid: specific capability name
        request = CompleteRequest(
            messages=[UserMessage(content="Hello")], model="gpt-4", capability_choice="get_weather"
        )
        assert request.capability_choice == "get_weather"

        # Invalid: empty string
        with pytest.raises(ValidationError):
            CompleteRequest(
                messages=[UserMessage(content="Hello")], model="gpt-4", capability_choice=""
            )

        # Invalid: whitespace only
        with pytest.raises(ValidationError):
            CompleteRequest(
                messages=[UserMessage(content="Hello")], model="gpt-4", capability_choice="   "
            )


class TestCompleteResponse:
    """Tests for CompleteResponse model."""

    def test_completion_response_creation(self):
        """Test creating a CompleteResponse."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        response = CompleteResponse(
            model="gpt-4",
            provider="openai",
            content="Hello, world!",
            finish_reason="stop",
            usage=usage,
        )
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.content == "Hello, world!"
        assert response.finish_reason == "stop"
        assert response.usage.total_tokens == 30
        assert response.role == "assistant"  # Default

    def test_completion_response_with_id(self):
        """Test CompleteResponse generates unique ID."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        response1 = CompleteResponse(
            model="gpt-4", provider="openai", content="test", finish_reason="stop", usage=usage
        )
        response2 = CompleteResponse(
            model="gpt-4", provider="openai", content="test", finish_reason="stop", usage=usage
        )
        assert response1.id != response2.id

    def test_completion_response_with_timestamp(self):
        """Test CompleteResponse includes timestamp."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        response = CompleteResponse(
            model="gpt-4", provider="openai", content="test", finish_reason="stop", usage=usage
        )
        assert isinstance(response.created_at, datetime)

    def test_get_output_text_content(self):
        """Test get_output returns text content when no structured output."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        response = CompleteResponse(
            model="gpt-4",
            provider="openai",
            content="Hello, world!",
            finish_reason="stop",
            usage=usage,
        )
        assert response.get_output() == "Hello, world!"

    def test_get_output_structured(self):
        """Test get_output returns structured output when available."""

        @validated
        class Person(Validated):
            name: str
            age: int

        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        person = Person(name="Alice", age=30)
        response = CompleteResponse(
            model="gpt-4",
            provider="openai",
            content='{"name": "Alice", "age": 30}',
            structured_output=person,
            finish_reason="stop",
            usage=usage,
        )
        output = response.get_output()
        assert isinstance(output, Person)
        assert output.name == "Alice"
        assert output.age == 30

    def test_completion_response_metadata(self):
        """Test CompleteResponse with metadata."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        response = CompleteResponse(
            model="gpt-4",
            provider="openai",
            content="test",
            finish_reason="stop",
            usage=usage,
            metadata={"request_id": "req_123", "latency_ms": 234},
        )
        assert response.metadata["request_id"] == "req_123"
        assert response.metadata["latency_ms"] == 234


class TestStreamChunk:
    """Tests for StreamChunk model."""

    def test_stream_chunk_creation(self):
        """Test creating a StreamChunk."""
        chunk = StreamChunk(id="stream_123", delta="Hello", index=0)
        assert chunk.id == "stream_123"
        assert chunk.delta == "Hello"
        assert chunk.index == 0
        assert chunk.finish_reason is None

    def test_stream_chunk_final(self):
        """Test final StreamChunk with finish_reason."""
        chunk = StreamChunk(id="stream_123", delta="", finish_reason="stop", index=5)
        assert chunk.delta == ""
        assert chunk.finish_reason == "stop"
        assert chunk.index == 5

    def test_stream_chunk_sequence(self):
        """Test sequence of StreamChunks."""
        chunks = [
            StreamChunk(id="stream_123", delta="Hello", index=0),
            StreamChunk(id="stream_123", delta=" ", index=1),
            StreamChunk(id="stream_123", delta="world", index=2),
            StreamChunk(id="stream_123", delta="!", index=3),
            StreamChunk(id="stream_123", delta="", finish_reason="stop", index=4),
        ]

        # Reconstruct message from chunks
        message = "".join(chunk.delta for chunk in chunks)
        assert message == "Hello world!"

        # Verify final chunk
        assert chunks[-1].finish_reason == "stop"

    def test_completion_request_with_prompt(self):
        """Test creating a CompleteRequest with prompt template."""
        request = CompleteRequest(
            prompt="greeting", prompt_variables={"name": "Alice"}, model="gpt-4"
        )
        assert request.prompt == "greeting"
        assert request.prompt_variables == {"name": "Alice"}
        assert request.messages is None
        assert request.model == "gpt-4"

    def test_completion_request_requires_messages_or_prompt(self):
        """Test that either messages or prompt must be provided."""
        with pytest.raises(ValidationError, match="Either 'messages' or 'prompt' must be provided"):
            CompleteRequest(model="gpt-4")

    def test_completion_request_cannot_have_both(self):
        """Test that both messages and prompt cannot be provided."""
        with pytest.raises(ValidationError, match="Cannot provide both 'messages' and 'prompt'"):
            CompleteRequest(
                messages=[UserMessage(content="Hello")], prompt="greeting", model="gpt-4"
            )

    def test_completion_request_prompt_with_empty_variables(self):
        """Test prompt request with no variables."""
        request = CompleteRequest(prompt="simple_greeting", model="gpt-4")
        assert request.prompt == "simple_greeting"
        assert request.prompt_variables == {}
