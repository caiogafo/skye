#!/usr/bin/env python
"""Unit tests for completion models."""

import pytest
from pydantic import BaseModel, ValidationError

from nimbus.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.messages import UserMessage


def test_token_usage():
    """Test TokenUsage model."""
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30


def test_completion_request():
    """Test CompletionRequest model."""
    # Basic request
    request = CompletionRequest(
        messages=[UserMessage(content="Hello")], model="gpt-4", temperature=0.7, max_tokens=100
    )
    assert request.model == "gpt-4"
    assert request.temperature == 0.7
    assert request.max_tokens == 100
    assert request.top_p == 1.0  # default
    assert request.stream is False  # default

    # Test temperature validation
    with pytest.raises(ValidationError):
        CompletionRequest(
            messages=[UserMessage(content="Hi")], model="gpt-4", temperature=3.0  # Invalid
        )

    # Test top_p validation
    with pytest.raises(ValidationError):
        CompletionRequest(messages=[UserMessage(content="Hi")], model="gpt-4", top_p=1.5)  # Invalid


def test_completion_response():
    """Test CompletionResponse model."""
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    # Text response
    response = CompletionResponse(
        model="gpt-4", provider="openai", content="Hello there!", finish_reason="stop", usage=usage
    )
    assert response.content == "Hello there!"
    assert response.get_output() == "Hello there!"
    assert response.role == "assistant"

    # Structured response
    class Person(BaseModel):
        name: str
        age: int

    person = Person(name="Alice", age=30)
    response.structured_output = person
    output = response.get_output()
    assert isinstance(output, Person)
    assert output.name == "Alice"


def test_stream_chunk():
    """Test StreamChunk model."""
    chunk = StreamChunk(id="stream_123", delta="Hello", index=0)
    assert chunk.id == "stream_123"
    assert chunk.delta == "Hello"
    assert chunk.index == 0
    assert chunk.finish_reason is None

    final_chunk = StreamChunk(id="stream_123", delta="", finish_reason="stop", index=5)
    assert final_chunk.finish_reason == "stop"


def test_completion_response_tool_calls():
    """Test CompletionResponse with tool calls."""
    from nimbus.capabilities.tool_models import ToolCall

    usage = TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70)

    # Response without tool calls
    response_no_tools = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="Hello",
        finish_reason="stop",
        usage=usage,
    )
    assert not response_no_tools.has_tool_calls()
    assert response_no_tools.tool_calls is None

    # Response with tool calls
    tool_call = ToolCall(
        id="call_123",
        name="weather.get_current",
        arguments={"location": "San Francisco"},
    )
    response_with_tools = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="",
        finish_reason="tool_calls",
        usage=usage,
        tool_calls=[tool_call],
    )
    assert response_with_tools.has_tool_calls()
    assert len(response_with_tools.tool_calls) == 1
    assert response_with_tools.tool_calls[0].name == "weather.get_current"

    # Response with empty tool_calls list
    response_empty_tools = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="Hello",
        finish_reason="stop",
        usage=usage,
        tool_calls=[],
    )
    assert not response_empty_tools.has_tool_calls()


@pytest.mark.asyncio
async def test_completion_response_execute_tool_calls():
    """Test executing tool calls from CompletionResponse."""
    from nimbus.capabilities.local_function import LocalFunctionCapability
    from nimbus.capabilities.registry import CapabilityRegistry
    from nimbus.capabilities.tool_models import ToolCall

    # Create a test capability
    def get_weather(location: str) -> dict:
        """Get weather for a location."""
        return {"location": location, "temperature": 72, "condition": "sunny"}

    capability = LocalFunctionCapability(
        func=get_weather,
        name="weather.get_current",
        description="Get current weather for a location",
    )

    # Register capability
    registry = CapabilityRegistry()
    registry.register(capability)

    # Create response with tool calls
    usage = TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70)
    tool_call = ToolCall(
        id="call_123",
        name="weather.get_current",
        arguments={"location": "San Francisco"},
    )
    response = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="",
        finish_reason="tool_calls",
        usage=usage,
        tool_calls=[tool_call],
    )

    # Execute tool calls
    results = await response.execute_tool_calls(registry)

    # Verify results
    assert len(results) == 1
    assert results[0].tool_call_id == "call_123"
    assert results[0].name == "weather.get_current"
    assert results[0].error is None
    assert results[0].result == {
        "location": "San Francisco",
        "temperature": 72,
        "condition": "sunny",
    }


@pytest.mark.asyncio
async def test_completion_response_execute_tool_calls_error():
    """Test executing tool calls with errors."""
    from nimbus.capabilities.local_function import LocalFunctionCapability
    from nimbus.capabilities.registry import CapabilityRegistry
    from nimbus.capabilities.tool_models import ToolCall

    # Create a test capability that raises an error
    def failing_function(value: str) -> str:
        """A function that always fails."""
        raise ValueError(f"Failed to process: {value}")

    capability = LocalFunctionCapability(
        func=failing_function,
        name="failing_tool",
        description="A tool that fails",
    )

    # Register capability
    registry = CapabilityRegistry()
    registry.register(capability)

    # Create response with tool calls
    usage = TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70)
    tool_call = ToolCall(
        id="call_456",
        name="failing_tool",
        arguments={"value": "test"},
    )
    response = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="",
        finish_reason="tool_calls",
        usage=usage,
        tool_calls=[tool_call],
    )

    # Execute tool calls
    results = await response.execute_tool_calls(registry)

    # Verify error result
    assert len(results) == 1
    assert results[0].tool_call_id == "call_456"
    assert results[0].name == "failing_tool"
    assert results[0].result is None
    assert results[0].error is not None
    assert "Failed to process: test" in results[0].error


@pytest.mark.asyncio
async def test_completion_response_execute_tool_calls_no_tools():
    """Test executing tool calls when response has no tool calls."""
    from nimbus.capabilities.registry import CapabilityRegistry

    registry = CapabilityRegistry()
    usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)

    response = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="Hello",
        finish_reason="stop",
        usage=usage,
    )

    # Should raise ValueError
    with pytest.raises(ValueError, match="Response has no tool calls to execute"):
        await response.execute_tool_calls(registry)


@pytest.mark.asyncio
async def test_completion_response_execute_multiple_tool_calls():
    """Test executing multiple tool calls."""
    from nimbus.capabilities.local_function import LocalFunctionCapability
    from nimbus.capabilities.registry import CapabilityRegistry
    from nimbus.capabilities.tool_models import ToolCall

    # Create test capabilities
    def get_weather(location: str) -> dict:
        """Get weather for a location."""
        return {"location": location, "temperature": 72}

    def get_time(timezone: str) -> dict:
        """Get current time for a timezone."""
        return {"timezone": timezone, "time": "12:00 PM"}

    weather_cap = LocalFunctionCapability(
        func=get_weather,
        name="weather.get_current",
        description="Get current weather",
    )
    time_cap = LocalFunctionCapability(
        func=get_time,
        name="time.get_current",
        description="Get current time",
    )

    # Register capabilities
    registry = CapabilityRegistry()
    registry.register(weather_cap)
    registry.register(time_cap)

    # Create response with multiple tool calls
    usage = TokenUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80)
    tool_calls = [
        ToolCall(
            id="call_1",
            name="weather.get_current",
            arguments={"location": "NYC"},
        ),
        ToolCall(
            id="call_2",
            name="time.get_current",
            arguments={"timezone": "EST"},
        ),
    ]
    response = CompletionResponse(
        model="gpt-4",
        provider="openai",
        content="",
        finish_reason="tool_calls",
        usage=usage,
        tool_calls=tool_calls,
    )

    # Execute tool calls
    results = await response.execute_tool_calls(registry)

    # Verify results
    assert len(results) == 2
    assert results[0].tool_call_id == "call_1"
    assert results[0].name == "weather.get_current"
    assert results[0].result["location"] == "NYC"
    assert results[1].tool_call_id == "call_2"
    assert results[1].name == "time.get_current"
    assert results[1].result["timezone"] == "EST"


def test_completion_request_mcp_configuration():
    """Test CompletionRequest with MCP server configuration."""
    # Request with MCP servers
    mcp_config = [
        {
            "name": "weather_server",
            "command": "mcp-server-weather",
            "args": ["--port", "8080"],
            "env": {"API_KEY": "test_key"},
        },
        {
            "name": "search_server",
            "command": "mcp-server-search",
        },
    ]

    request = CompletionRequest(
        messages=[UserMessage(content="What's the weather?")],
        model="gpt-4",
        mcp_servers=mcp_config,
    )

    assert request.mcp_servers is not None
    assert len(request.mcp_servers) == 2
    assert request.mcp_servers[0]["name"] == "weather_server"
    assert request.mcp_servers[1]["name"] == "search_server"


def test_completion_request_mcp_with_capabilities():
    """Test CompletionRequest with both MCP servers and capabilities."""
    # This tests that MCP servers and capabilities can coexist
    mcp_config = [
        {
            "name": "weather_server",
            "command": "mcp-server-weather",
        }
    ]

    # Mock capability (we don't need a real one for this test)
    class MockCapability:
        def get_schema(self):
            return {"name": "test_tool"}

    request = CompletionRequest(
        messages=[UserMessage(content="Test")],
        model="gpt-4",
        capabilities=[MockCapability()],
        mcp_servers=mcp_config,
    )

    assert request.capabilities is not None
    assert len(request.capabilities) == 1
    assert request.mcp_servers is not None
    assert len(request.mcp_servers) == 1


def test_completion_request_mcp_empty_list():
    """Test CompletionRequest with empty MCP servers list."""
    request = CompletionRequest(
        messages=[UserMessage(content="Test")],
        model="gpt-4",
        mcp_servers=[],
    )

    assert request.mcp_servers is not None
    assert len(request.mcp_servers) == 0


def test_completion_request_mcp_none():
    """Test CompletionRequest with mcp_servers=None (default)."""
    request = CompletionRequest(
        messages=[UserMessage(content="Test")],
        model="gpt-4",
    )

    assert request.mcp_servers is None
