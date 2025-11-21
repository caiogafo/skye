"""Unit tests for CapabilityCallHandler."""

import json

import pytest

from nimbus.capabilities.exceptions import ToolCallParsingError
from nimbus.capabilities.interface import CapabilityInterface
from nimbus.capabilities.registry import CapabilityRegistry
from nimbus.capabilities.schema import CapabilitySchema
from nimbus.capabilities.capability_call_handler import CapabilityCallHandler
from nimbus.capabilities.capability_models import CapabilityCall, CapabilityResult
from nimbus.completion import CompletionResponse, TokenUsage


class MockCapability(CapabilityInterface):
    """Mock capability for testing."""

    def __init__(self, name: str, result: any = "mock_result"):
        self.name = name
        self.result = result

    def get_schema(self) -> CapabilitySchema:
        return CapabilitySchema(
            name=self.name,
            description=f"Mock capability {self.name}",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "units": {"type": "string"},
                },
                "required": ["location"],
            },
            returns={"type": "object"},
        )

    def execute(self, **kwargs):
        return self.result

    async def aexecute(self, **kwargs):
        return self.result


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    reg = CapabilityRegistry()
    yield reg
    reg.clear()


@pytest.fixture
def handler(registry):
    """Create a CapabilityCallHandler with a registry."""
    return CapabilityCallHandler(registry)


@pytest.fixture
def mock_capability():
    """Create a mock capability."""
    return MockCapability("get_weather", {"temperature": 72, "condition": "sunny"})


class TestCapabilityCallHandlerInit:
    """Tests for CapabilityCallHandler initialization."""

    def test_init_with_registry(self, registry):
        """Test initialization with a registry."""
        handler = CapabilityCallHandler(registry)
        assert handler.registry is registry


class TestParseOpenAICapabilityCalls:
    """Tests for parsing OpenAI tool calls."""

    def test_parse_openai_tool_calls_success(self, handler):
        """Test parsing valid OpenAI tool calls."""
        response = CompletionResponse(
            model="gpt-4",
            provider="openai",
            content="",
            finish_reason="tool_calls",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "San Francisco", "units": "celsius"}',
                        },
                    }
                ]
            },
        )

        tool_calls = handler.parse_capability_calls(response, "openai")

        assert len(tool_calls) == 1
        assert tool_calls[0].id == "call_123"
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {
            "location": "San Francisco",
            "units": "celsius",
        }

    def test_parse_openai_multiple_tool_calls(self, handler):
        """Test parsing multiple OpenAI tool calls."""
        response = CompletionResponse(
            model="gpt-4",
            provider="openai",
            content="",
            finish_reason="tool_calls",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "NYC"}',
                        },
                    },
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "get_time",
                            "arguments": '{"timezone": "EST"}',
                        },
                    },
                ]
            },
        )

        tool_calls = handler.parse_capability_calls(response, "openai")

        assert len(tool_calls) == 2
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[1].name == "get_time"

    def test_parse_openai_empty_tool_calls(self, handler):
        """Test parsing response with no tool calls."""
        response = CompletionResponse(
            model="gpt-4",
            provider="openai",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={},
        )

        tool_calls = handler.parse_capability_calls(response, "openai")

        assert len(tool_calls) == 0

    def test_parse_openai_invalid_json_arguments(self, handler):
        """Test parsing OpenAI tool call with invalid JSON arguments."""
        response = CompletionResponse(
            model="gpt-4",
            provider="openai",
            content="",
            finish_reason="tool_calls",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": "invalid json",
                        },
                    }
                ]
            },
        )

        with pytest.raises(ToolCallParsingError) as exc_info:
            handler.parse_capability_calls(response, "openai")

        assert "Invalid JSON" in str(exc_info.value)

    def test_parse_openai_missing_id(self, handler):
        """Test parsing OpenAI tool call with missing id."""
        response = CompletionResponse(
            model="gpt-4",
            provider="openai",
            content="",
            finish_reason="tool_calls",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "NYC"}',
                        },
                    }
                ]
            },
        )

        with pytest.raises(ToolCallParsingError):
            handler.parse_capability_calls(response, "openai")


class TestParseAnthropicCapabilityCalls:
    """Tests for parsing Anthropic tool calls."""

    def test_parse_anthropic_tool_calls_success(self, handler):
        """Test parsing valid Anthropic tool calls."""
        response = CompletionResponse(
            model="claude-3-sonnet",
            provider="anthropic",
            content="",
            finish_reason="tool_use",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_123",
                        "name": "get_weather",
                        "input": {"location": "San Francisco", "units": "celsius"},
                    }
                ]
            },
        )

        tool_calls = handler.parse_capability_calls(response, "anthropic")

        assert len(tool_calls) == 1
        assert tool_calls[0].id == "toolu_123"
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {
            "location": "San Francisco",
            "units": "celsius",
        }

    def test_parse_anthropic_mixed_content(self, handler):
        """Test parsing Anthropic response with mixed content blocks."""
        response = CompletionResponse(
            model="claude-3-sonnet",
            provider="anthropic",
            content="",
            finish_reason="tool_use",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "content": [
                    {"type": "text", "text": "Let me check the weather"},
                    {
                        "type": "tool_use",
                        "id": "toolu_123",
                        "name": "get_weather",
                        "input": {"location": "NYC"},
                    },
                ]
            },
        )

        tool_calls = handler.parse_capability_calls(response, "anthropic")

        assert len(tool_calls) == 1
        assert tool_calls[0].name == "get_weather"

    def test_parse_anthropic_empty_content(self, handler):
        """Test parsing Anthropic response with no content."""
        response = CompletionResponse(
            model="claude-3-sonnet",
            provider="anthropic",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={},
        )

        tool_calls = handler.parse_capability_calls(response, "anthropic")

        assert len(tool_calls) == 0


class TestParseBedrockCapabilityCalls:
    """Tests for parsing Bedrock tool calls."""

    def test_parse_bedrock_tool_calls_success(self, handler):
        """Test parsing valid Bedrock tool calls."""
        response = CompletionResponse(
            model="anthropic.claude-3-sonnet",
            provider="bedrock",
            content="",
            finish_reason="tool_use",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "output": {
                    "message": {
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tooluse_123",
                                    "name": "get_weather",
                                    "input": {
                                        "location": "San Francisco",
                                        "units": "celsius",
                                    },
                                }
                            }
                        ]
                    }
                }
            },
        )

        tool_calls = handler.parse_capability_calls(response, "bedrock")

        assert len(tool_calls) == 1
        assert tool_calls[0].id == "tooluse_123"
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {
            "location": "San Francisco",
            "units": "celsius",
        }

    def test_parse_bedrock_empty_output(self, handler):
        """Test parsing Bedrock response with no output."""
        response = CompletionResponse(
            model="anthropic.claude-3-sonnet",
            provider="bedrock",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={},
        )

        tool_calls = handler.parse_capability_calls(response, "bedrock")

        assert len(tool_calls) == 0


class TestParseVertexCapabilityCalls:
    """Tests for parsing Vertex AI tool calls."""

    def test_parse_vertex_tool_calls_success(self, handler):
        """Test parsing valid Vertex AI tool calls."""
        response = CompletionResponse(
            model="gemini-pro",
            provider="vertex",
            content="",
            finish_reason="tool_calls",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "functionCall": {
                                        "name": "get_weather",
                                        "args": {
                                            "location": "San Francisco",
                                            "units": "celsius",
                                        },
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

        tool_calls = handler.parse_capability_calls(response, "vertex")

        assert len(tool_calls) == 1
        assert tool_calls[0].id.startswith("vertex_call_")
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {
            "location": "San Francisco",
            "units": "celsius",
        }

    def test_parse_vertex_multiple_function_calls(self, handler):
        """Test parsing multiple Vertex AI function calls."""
        response = CompletionResponse(
            model="gemini-pro",
            provider="vertex",
            content="",
            finish_reason="tool_calls",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "functionCall": {
                                        "name": "get_weather",
                                        "args": {"location": "NYC"},
                                    }
                                },
                                {
                                    "functionCall": {
                                        "name": "get_time",
                                        "args": {"timezone": "EST"},
                                    }
                                },
                            ]
                        }
                    }
                ]
            },
        )

        tool_calls = handler.parse_capability_calls(response, "vertex")

        assert len(tool_calls) == 2
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[1].name == "get_time"

    def test_parse_vertex_empty_candidates(self, handler):
        """Test parsing Vertex response with no candidates."""
        response = CompletionResponse(
            model="gemini-pro",
            provider="vertex",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={},
        )

        tool_calls = handler.parse_capability_calls(response, "vertex")

        assert len(tool_calls) == 0


class TestParseAzureCapabilityCalls:
    """Tests for parsing Azure tool calls (same as OpenAI)."""

    def test_parse_azure_tool_calls_success(self, handler):
        """Test parsing valid Azure tool calls."""
        response = CompletionResponse(
            model="gpt-4",
            provider="azure",
            content="",
            finish_reason="tool_calls",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "San Francisco"}',
                        },
                    }
                ]
            },
        )

        tool_calls = handler.parse_capability_calls(response, "azure")

        assert len(tool_calls) == 1
        assert tool_calls[0].id == "call_123"
        assert tool_calls[0].name == "get_weather"


class TestParseUnsupportedProvider:
    """Tests for unsupported provider."""

    def test_parse_unsupported_provider(self, handler):
        """Test parsing with unsupported provider."""
        response = CompletionResponse(
            model="test-model",
            provider="unknown",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

        with pytest.raises(ToolCallParsingError) as exc_info:
            handler.parse_capability_calls(response, "unknown")

        assert "Unsupported provider" in str(exc_info.value)


class TestExecuteCapabilityCalls:
    """Tests for executing tool calls."""

    @pytest.mark.asyncio
    async def test_execute_capability_calls_success(self, handler, registry, mock_capability):
        """Test successful execution of tool calls."""
        registry.register(mock_capability)

        tool_calls = [
            CapabilityCall(
                id="call_1",
                name="get_weather",
                arguments={"location": "San Francisco"},
            )
        ]

        results = await handler.execute_capability_calls(tool_calls)

        assert len(results) == 1
        assert results[0].capability_call_id == "call_1"
        assert results[0].name == "get_weather"
        assert results[0].result == {"temperature": 72, "condition": "sunny"}
        assert results[0].error is None

    @pytest.mark.asyncio
    async def test_execute_multiple_tool_calls(self, handler, registry):
        """Test executing multiple tool calls."""
        cap1 = MockCapability("tool1", "result1")
        cap2 = MockCapability("tool2", "result2")
        registry.register(cap1)
        registry.register(cap2)

        tool_calls = [
            CapabilityCall(id="call_1", name="tool1", arguments={"location": "NYC"}),
            CapabilityCall(id="call_2", name="tool2", arguments={"location": "LA"}),
        ]

        results = await handler.execute_capability_calls(tool_calls)

        assert len(results) == 2
        assert results[0].result == "result1"
        assert results[1].result == "result2"

    @pytest.mark.asyncio
    async def test_execute_tool_call_not_found(self, handler, registry):
        """Test executing tool call for non-existent capability."""
        tool_calls = [
            CapabilityCall(
                id="call_1",
                name="nonexistent",
                arguments={"location": "NYC"},
            )
        ]

        results = await handler.execute_capability_calls(tool_calls)

        assert len(results) == 1
        assert results[0].error is not None
        assert "not found" in results[0].error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_call_missing_required_param(
        self, handler, registry, mock_capability
    ):
        """Test executing tool call with missing required parameter."""
        registry.register(mock_capability)

        tool_calls = [
            CapabilityCall(
                id="call_1",
                name="get_weather",
                arguments={},  # Missing required 'location'
            )
        ]

        results = await handler.execute_capability_calls(tool_calls)

        assert len(results) == 1
        assert results[0].error is not None
        assert "required parameter" in results[0].error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_call_wrong_type(self, handler, registry, mock_capability):
        """Test executing tool call with wrong parameter type."""
        registry.register(mock_capability)

        tool_calls = [
            CapabilityCall(
                id="call_1",
                name="get_weather",
                arguments={"location": 123},  # Should be string
            )
        ]

        results = await handler.execute_capability_calls(tool_calls)

        assert len(results) == 1
        assert results[0].error is not None
        assert "wrong type" in results[0].error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_call_execution_error(self, handler, registry):
        """Test handling execution errors."""

        class FailingCapability(CapabilityInterface):
            def get_schema(self):
                return CapabilitySchema(
                    name="failing_tool",
                    description="A tool that fails",
                    parameters={"type": "object", "properties": {}},
                    returns={"type": "string"},
                )

            def execute(self, **kwargs):
                raise RuntimeError("Execution failed")

            async def aexecute(self, **kwargs):
                raise RuntimeError("Execution failed")

        registry.register(FailingCapability())

        tool_calls = [CapabilityCall(id="call_1", name="failing_tool", arguments={})]

        results = await handler.execute_capability_calls(tool_calls)

        assert len(results) == 1
        assert results[0].error is not None
        assert "Execution failed" in results[0].error


class TestFormatOpenAIResults:
    """Tests for formatting OpenAI results."""

    def test_format_openai_results_success(self, handler):
        """Test formatting successful OpenAI results."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result={"temperature": 72, "condition": "sunny"},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, "openai")

        assert len(formatted) == 1
        assert formatted[0]["tool_call_id"] == "call_1"
        assert formatted[0]["role"] == "tool"
        assert json.loads(formatted[0]["content"]) == {
            "temperature": 72,
            "condition": "sunny",
        }

    def test_format_openai_results_with_error(self, handler):
        """Test formatting OpenAI results with error."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result=None,
                error="Location not found",
            )
        ]

        formatted = handler.format_capability_results(results, "openai")

        assert len(formatted) == 1
        assert json.loads(formatted[0]["content"]) == {"error": "Location not found"}

    def test_format_openai_results_string_result(self, handler):
        """Test formatting OpenAI results with string result."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result="Sunny and 72 degrees",
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, "openai")

        assert formatted[0]["content"] == "Sunny and 72 degrees"


class TestFormatAnthropicResults:
    """Tests for formatting Anthropic results."""

    def test_format_anthropic_results_success(self, handler):
        """Test formatting successful Anthropic results."""
        results = [
            CapabilityResult(
                capability_call_id="toolu_1",
                name="get_weather",
                result={"temperature": 72, "condition": "sunny"},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, "anthropic")

        assert len(formatted) == 1
        assert formatted[0]["type"] == "tool_result"
        assert formatted[0]["tool_use_id"] == "toolu_1"
        assert json.loads(formatted[0]["content"]) == {
            "temperature": 72,
            "condition": "sunny",
        }


class TestFormatBedrockResults:
    """Tests for formatting Bedrock results."""

    def test_format_bedrock_results_success(self, handler):
        """Test formatting successful Bedrock results."""
        results = [
            CapabilityResult(
                capability_call_id="tooluse_1",
                name="get_weather",
                result={"temperature": 72, "condition": "sunny"},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, "bedrock")

        assert len(formatted) == 1
        assert "toolResult" in formatted[0]
        assert formatted[0]["toolResult"]["toolUseId"] == "tooluse_1"
        assert formatted[0]["toolResult"]["content"][0]["json"] == {
            "temperature": 72,
            "condition": "sunny",
        }

    def test_format_bedrock_results_string_result(self, handler):
        """Test formatting Bedrock results with string result."""
        results = [
            CapabilityResult(
                capability_call_id="tooluse_1",
                name="get_weather",
                result='{"temperature": 72}',
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, "bedrock")

        assert formatted[0]["toolResult"]["content"][0]["json"] == {"temperature": 72}


class TestFormatVertexResults:
    """Tests for formatting Vertex AI results."""

    def test_format_vertex_results_success(self, handler):
        """Test formatting successful Vertex AI results."""
        results = [
            CapabilityResult(
                capability_call_id="vertex_call_0",
                name="get_weather",
                result={"temperature": 72, "condition": "sunny"},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, "vertex")

        assert len(formatted) == 1
        assert "functionResponse" in formatted[0]
        assert formatted[0]["functionResponse"]["name"] == "get_weather"
        assert formatted[0]["functionResponse"]["response"] == {
            "temperature": 72,
            "condition": "sunny",
        }


class TestFormatAzureResults:
    """Tests for formatting Azure results (same as OpenAI)."""

    def test_format_azure_results_success(self, handler):
        """Test formatting successful Azure results."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result={"temperature": 72},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, "azure")

        assert len(formatted) == 1
        assert formatted[0]["tool_call_id"] == "call_1"
        assert formatted[0]["role"] == "tool"


class TestFormatUnsupportedProvider:
    """Tests for formatting with unsupported provider."""

    def test_format_unsupported_provider(self, handler):
        """Test formatting with unsupported provider."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result={"temperature": 72},
                error=None,
            )
        ]

        with pytest.raises(ToolCallParsingError) as exc_info:
            handler.format_capability_results(results, "unknown")

        assert "Unsupported provider" in str(exc_info.value)
