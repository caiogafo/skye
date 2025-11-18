#!/usr/bin/env python
"""Quick validation script for completion models."""

from nimbus.completion import TokenUsage, CompletionRequest, CompletionResponse, StreamChunk
from nimbus.messages import UserMessage
from pydantic import BaseModel, ValidationError


def test_token_usage():
    """Test TokenUsage model."""
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30
    print("✓ TokenUsage model works")


def test_completion_request():
    """Test CompletionRequest model."""
    # Basic request
    request = CompletionRequest(
        messages=[UserMessage(content="Hello")],
        model="gpt-4",
        temperature=0.7,
        max_tokens=100
    )
    assert request.model == "gpt-4"
    assert request.temperature == 0.7
    assert request.max_tokens == 100
    assert request.top_p == 1.0  # default
    assert request.stream is False  # default
    print("✓ CompletionRequest basic creation works")
    
    # Test temperature validation
    try:
        CompletionRequest(
            messages=[UserMessage(content="Hi")],
            model="gpt-4",
            temperature=3.0  # Invalid
        )
        assert False, "Should have raised ValidationError"
    except ValidationError:
        print("✓ CompletionRequest temperature validation works")
    
    # Test top_p validation
    try:
        CompletionRequest(
            messages=[UserMessage(content="Hi")],
            model="gpt-4",
            top_p=1.5  # Invalid
        )
        assert False, "Should have raised ValidationError"
    except ValidationError:
        print("✓ CompletionRequest top_p validation works")


def test_completion_response():
    """Test CompletionResponse model."""
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    
    # Text response
    response = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="Hello there!",
        finish_reason="stop",
        usage=usage
    )
    assert response.content == "Hello there!"
    assert response.get_output() == "Hello there!"
    assert response.role == "assistant"
    print("✓ CompletionResponse text output works")
    
    # Structured response
    class Person(BaseModel):
        name: str
        age: int
    
    person = Person(name="Alice", age=30)
    response.structured_output = person
    output = response.get_output()
    assert isinstance(output, Person)
    assert output.name == "Alice"
    print("✓ CompletionResponse structured output works")


def test_stream_chunk():
    """Test StreamChunk model."""
    chunk = StreamChunk(id="stream_123", delta="Hello", index=0)
    assert chunk.id == "stream_123"
    assert chunk.delta == "Hello"
    assert chunk.index == 0
    assert chunk.finish_reason is None
    
    final_chunk = StreamChunk(
        id="stream_123",
        delta="",
        finish_reason="stop",
        index=5
    )
    assert final_chunk.finish_reason == "stop"
    print("✓ StreamChunk model works")


if __name__ == "__main__":
    test_token_usage()
    test_completion_request()
    test_completion_response()
    test_stream_chunk()
    print("\n✅ All completion models validated successfully!")
