"""Unit tests for CapabilityCallHandler."""

import json

import pytest

from skye.base.completion import CompleteResponse, TokenUsage
from skye.tools.capability_call_handler import CapabilityCallHandler
from skye.tools.capability_models import CapabilityCall, CapabilityResult
from skye.tools.exceptions import CapabilityCallParsingError
from skye.tools.interface import CapabilityInterface
from skye.tools.registry import CapabilityRegistry
from skye.tools.schema import CapabilitySchema


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


class MockProvider:
    """Mock provider for testing capability call parsing and formatting."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
    
    def parse_capability_calls(self, response: CompleteResponse) -> list[CapabilityCall]:
        """Parse capability calls based on provider type."""
        if self.provider_name.lower() in ("openai", "azure"):
            return self._parse_openai_capability_calls(response)
        elif self.provider_name.lower() == "anthropic":
            return self._parse_anthropic_capability_calls(response)
        elif self.provider_name.lower() == "bedrock":
            return self._parse_bedrock_capability_calls(response)
        elif self.provider_name.lower() == "google":
            return self._parse_google_capability_calls(response)
        else:
            return []
    
    def format_capability_results(self, results: list[CapabilityResult]) -> list[dict]:
        """Format capability results based on provider type."""
        if self.provider_name.lower() in ("openai", "azure"):
            return self._format_openai_results(results)
        elif self.provider_name.lower() == "anthropic":
            return self._format_anthropic_results(results)
        elif self.provider_name.lower() == "bedrock":
            return self._format_bedrock_results(results)
        elif self.provider_name.lower() == "google":
            return self._format_google_results(results)
        else:
            return []
    
    def _parse_openai_capability_calls(self, response: CompleteResponse) -> list[CapabilityCall]:
        """Parse OpenAI/Azure capability calls."""
        tool_calls_data = response.metadata.get("tool_calls", [])
        if not tool_calls_data:
            return []

        capability_calls = []
        for call_data in tool_calls_data:
            call_id = call_data.get("id")
            if not call_id:
                raise CapabilityCallParsingError("Missing tool call id", provider="openai")
                
            function_data = call_data.get("function", {})
            name = function_data.get("name")
            arguments_str = function_data.get("arguments", "{}")
            
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                raise CapabilityCallParsingError(f"Invalid JSON in arguments: {e}", provider="openai")

            capability_calls.append(
                CapabilityCall(id=call_id, name=name, arguments=arguments)
            )
        return capability_calls
    
    def _parse_anthropic_capability_calls(self, response: CompleteResponse) -> list[CapabilityCall]:
        """Parse Anthropic capability calls."""
        content_blocks = response.metadata.get("content", [])
        capability_calls = []
        
        for block in content_blocks:
            if block.get("type") == "tool_use":
                capability_calls.append(
                    CapabilityCall(
                        id=block.get("id"),
                        name=block.get("name"),
                        arguments=block.get("input", {})
                    )
                )
        return capability_calls
    
    def _parse_bedrock_capability_calls(self, response: CompleteResponse) -> list[CapabilityCall]:
        """Parse Bedrock capability calls."""
        output = response.metadata.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        
        capability_calls = []
        for block in content_blocks:
            tool_use = block.get("toolUse")
            if tool_use:
                capability_calls.append(
                    CapabilityCall(
                        id=tool_use.get("toolUseId"),
                        name=tool_use.get("name"),
                        arguments=tool_use.get("input", {})
                    )
                )
        return capability_calls
    
    def _parse_google_capability_calls(self, response: CompleteResponse) -> list[CapabilityCall]:
        """Parse Google capability calls."""
        candidates = response.metadata.get("candidates", [])
        if not candidates:
            return []
        
        capability_calls = []
        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        for idx, part in enumerate(parts):
            function_call = part.get("functionCall")
            if function_call:
                capability_calls.append(
                    CapabilityCall(
                        id=f"google_call_{idx}",
                        name=function_call.get("name"),
                        arguments=function_call.get("args", {})
                    )
                )
        return capability_calls
    
    def _format_openai_results(self, results: list[CapabilityResult]) -> list[dict]:
        """Format results for OpenAI/Azure."""
        formatted = []
        for result in results:
            if result.error:
                content = json.dumps({"error": result.error})
            elif isinstance(result.result, str):
                content = result.result
            else:
                content = json.dumps(result.result)

            formatted.append({
                "tool_call_id": result.capability_call_id,
                "role": "tool",
                "content": content,
            })
        return formatted
    
    def _format_anthropic_results(self, results: list[CapabilityResult]) -> list[dict]:
        """Format results for Anthropic."""
        formatted = []
        for result in results:
            if result.error:
                content = json.dumps({"error": result.error})
            elif isinstance(result.result, str):
                content = result.result
            else:
                content = json.dumps(result.result)

            formatted.append({
                "type": "tool_result",
                "tool_use_id": result.capability_call_id,
                "content": content,
            })
        return formatted
    
    def _format_bedrock_results(self, results: list[CapabilityResult]) -> list[dict]:
        """Format results for Bedrock."""
        formatted = []
        for result in results:
            if result.error:
                result_data = {"error": result.error}
            elif isinstance(result.result, dict):
                result_data = result.result
            elif isinstance(result.result, str):
                try:
                    result_data = json.loads(result.result)
                except json.JSONDecodeError:
                    result_data = {"result": result.result}
            else:
                result_data = {"result": result.result}

            formatted.append({
                "toolResult": {
                    "toolUseId": result.capability_call_id,
                    "content": [{"json": result_data}],
                }
            })
        return formatted
    
    def _format_google_results(self, results: list[CapabilityResult]) -> list[dict]:
        """Format results for Google."""
        formatted = []
        for result in results:
            if result.error:
                response_data = {"error": result.error}
            elif isinstance(result.result, dict):
                response_data = result.result
            elif isinstance(result.result, str):
                try:
                    response_data = json.loads(result.result)
                except json.JSONDecodeError:
                    response_data = {"result": result.result}
            else:
                response_data = {"result": result.result}

            formatted.append({
                "functionResponse": {
                    "name": result.name,
                    "response": response_data,
                }
            })
        return formatted


class MockUnsupportedProvider:
    """Mock unsupported provider that doesn't implement capability methods."""
    
    def __init__(self):
        self.provider_name = "unknown"
    
    # Intentionally does not implement parse_capability_calls or format_capability_results


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    reg = CapabilityRegistry()
    yield reg
    reg.clear()


@pytest.fixture
def openai_provider():
    """Create a mock OpenAI provider."""
    return MockProvider("openai")


@pytest.fixture
def anthropic_provider():
    """Create a mock Anthropic provider."""
    return MockProvider("anthropic")


@pytest.fixture
def bedrock_provider():
    """Create a mock Bedrock provider."""
    return MockProvider("bedrock")


@pytest.fixture
def google_provider():
    """Create a mock Google provider."""
    return MockProvider("google")


@pytest.fixture
def azure_provider():
    """Create a mock Azure provider."""
    return MockProvider("azure")


@pytest.fixture
def unsupported_provider():
    """Create a mock unsupported provider."""
    return MockUnsupportedProvider()


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

    def test_parse_openai_tool_calls_success(self, handler, openai_provider):
        """Test parsing valid OpenAI tool calls."""
        response = CompleteResponse(
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

        tool_calls = handler.parse_capability_calls(response, openai_provider)

        assert len(tool_calls) == 1
        assert tool_calls[0].id == "call_123"
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {
            "location": "San Francisco",
            "units": "celsius",
        }

    def test_parse_openai_multiple_tool_calls(self, handler, openai_provider):
        """Test parsing multiple OpenAI tool calls."""
        response = CompleteResponse(
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

        tool_calls = handler.parse_capability_calls(response, openai_provider)

        assert len(tool_calls) == 2
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[1].name == "get_time"

    def test_parse_openai_empty_tool_calls(self, handler, openai_provider):
        """Test parsing response with no tool calls."""
        response = CompleteResponse(
            model="gpt-4",
            provider="openai",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={},
        )

        tool_calls = handler.parse_capability_calls(response, openai_provider)

        assert len(tool_calls) == 0

    def test_parse_openai_invalid_json_arguments(self, handler, openai_provider):
        """Test parsing OpenAI tool call with invalid JSON arguments."""
        response = CompleteResponse(
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

        with pytest.raises(CapabilityCallParsingError) as exc_info:
            handler.parse_capability_calls(response, openai_provider)

        assert "Invalid JSON" in str(exc_info.value)

    def test_parse_openai_missing_id(self, handler, openai_provider):
        """Test parsing OpenAI tool call with missing id."""
        response = CompleteResponse(
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

        with pytest.raises(CapabilityCallParsingError):
            handler.parse_capability_calls(response, openai_provider)


class TestParseAnthropicCapabilityCalls:
    """Tests for parsing Anthropic tool calls."""

    def test_parse_anthropic_tool_calls_success(self, handler, anthropic_provider):
        """Test parsing valid Anthropic tool calls."""
        response = CompleteResponse(
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

        tool_calls = handler.parse_capability_calls(response, anthropic_provider)

        assert len(tool_calls) == 1
        assert tool_calls[0].id == "toolu_123"
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {
            "location": "San Francisco",
            "units": "celsius",
        }

    def test_parse_anthropic_mixed_content(self, handler, anthropic_provider):
        """Test parsing Anthropic response with mixed content blocks."""
        response = CompleteResponse(
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

        tool_calls = handler.parse_capability_calls(response, anthropic_provider)

        assert len(tool_calls) == 1
        assert tool_calls[0].name == "get_weather"

    def test_parse_anthropic_empty_content(self, handler, anthropic_provider):
        """Test parsing Anthropic response with no content."""
        response = CompleteResponse(
            model="claude-3-sonnet",
            provider="anthropic",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={},
        )

        tool_calls = handler.parse_capability_calls(response, anthropic_provider)

        assert len(tool_calls) == 0


class TestParseBedrockCapabilityCalls:
    """Tests for parsing Bedrock tool calls."""

    def test_parse_bedrock_tool_calls_success(self, handler, bedrock_provider):
        """Test parsing valid Bedrock tool calls."""
        response = CompleteResponse(
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

        tool_calls = handler.parse_capability_calls(response, bedrock_provider)

        assert len(tool_calls) == 1
        assert tool_calls[0].id == "tooluse_123"
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {
            "location": "San Francisco",
            "units": "celsius",
        }

    def test_parse_bedrock_empty_output(self, handler, bedrock_provider):
        """Test parsing Bedrock response with no output."""
        response = CompleteResponse(
            model="anthropic.claude-3-sonnet",
            provider="bedrock",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={},
        )

        tool_calls = handler.parse_capability_calls(response, bedrock_provider)

        assert len(tool_calls) == 0


class TestParseGoogleCapabilityCalls:
    """Tests for parsing Google tool calls."""

    def test_parse_google_tool_calls_success(self, handler, google_provider):
        """Test parsing valid Google tool calls."""
        response = CompleteResponse(
            model="gemini-pro",
            provider="google",
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

        tool_calls = handler.parse_capability_calls(response, google_provider)

        assert len(tool_calls) == 1
        assert tool_calls[0].id.startswith("google_call_")
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {
            "location": "San Francisco",
            "units": "celsius",
        }

    def test_parse_google_multiple_function_calls(self, handler, google_provider):
        """Test parsing multiple Google function calls."""
        response = CompleteResponse(
            model="gemini-pro",
            provider="google",
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

        tool_calls = handler.parse_capability_calls(response, google_provider)

        assert len(tool_calls) == 2
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[1].name == "get_time"

    def test_parse_google_empty_candidates(self, handler, google_provider):
        """Test parsing Google response with no candidates."""
        response = CompleteResponse(
            model="gemini-pro",
            provider="google",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            metadata={},
        )

        tool_calls = handler.parse_capability_calls(response, google_provider)

        assert len(tool_calls) == 0


class TestParseAzureCapabilityCalls:
    """Tests for parsing Azure tool calls (same as OpenAI)."""

    def test_parse_azure_tool_calls_success(self, handler, azure_provider):
        """Test parsing valid Azure tool calls."""
        response = CompleteResponse(
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

        tool_calls = handler.parse_capability_calls(response, azure_provider)

        assert len(tool_calls) == 1
        assert tool_calls[0].id == "call_123"
        assert tool_calls[0].name == "get_weather"


class TestParseUnsupportedProvider:
    """Tests for unsupported provider."""

    def test_parse_unsupported_provider(self, handler, unsupported_provider):
        """Test parsing with unsupported provider."""
        response = CompleteResponse(
            model="test-model",
            provider="unknown",
            content="Hello",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

        with pytest.raises(CapabilityCallParsingError) as exc_info:
            handler.parse_capability_calls(response, unsupported_provider)

        assert "does not support capability call parsing" in str(exc_info.value)


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

    def test_format_openai_results_success(self, handler, openai_provider):
        """Test formatting successful OpenAI results."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result={"temperature": 72, "condition": "sunny"},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, openai_provider)

        assert len(formatted) == 1
        assert formatted[0]["tool_call_id"] == "call_1"
        assert formatted[0]["role"] == "tool"
        assert json.loads(formatted[0]["content"]) == {
            "temperature": 72,
            "condition": "sunny",
        }

    def test_format_openai_results_with_error(self, handler, openai_provider):
        """Test formatting OpenAI results with error."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result=None,
                error="Location not found",
            )
        ]

        formatted = handler.format_capability_results(results, openai_provider)

        assert len(formatted) == 1
        assert json.loads(formatted[0]["content"]) == {"error": "Location not found"}

    def test_format_openai_results_string_result(self, handler, openai_provider):
        """Test formatting OpenAI results with string result."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result="Sunny and 72 degrees",
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, openai_provider)

        assert formatted[0]["content"] == "Sunny and 72 degrees"


class TestFormatAnthropicResults:
    """Tests for formatting Anthropic results."""

    def test_format_anthropic_results_success(self, handler, anthropic_provider):
        """Test formatting successful Anthropic results."""
        results = [
            CapabilityResult(
                capability_call_id="toolu_1",
                name="get_weather",
                result={"temperature": 72, "condition": "sunny"},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, anthropic_provider)

        assert len(formatted) == 1
        assert formatted[0]["type"] == "tool_result"
        assert formatted[0]["tool_use_id"] == "toolu_1"
        assert json.loads(formatted[0]["content"]) == {
            "temperature": 72,
            "condition": "sunny",
        }


class TestFormatBedrockResults:
    """Tests for formatting Bedrock results."""

    def test_format_bedrock_results_success(self, handler, bedrock_provider):
        """Test formatting successful Bedrock results."""
        results = [
            CapabilityResult(
                capability_call_id="tooluse_1",
                name="get_weather",
                result={"temperature": 72, "condition": "sunny"},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, bedrock_provider)

        assert len(formatted) == 1
        assert "toolResult" in formatted[0]
        assert formatted[0]["toolResult"]["toolUseId"] == "tooluse_1"
        assert formatted[0]["toolResult"]["content"][0]["json"] == {
            "temperature": 72,
            "condition": "sunny",
        }

    def test_format_bedrock_results_string_result(self, handler, bedrock_provider):
        """Test formatting Bedrock results with string result."""
        results = [
            CapabilityResult(
                capability_call_id="tooluse_1",
                name="get_weather",
                result='{"temperature": 72}',
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, bedrock_provider)

        assert formatted[0]["toolResult"]["content"][0]["json"] == {"temperature": 72}


class TestFormatGoogleResults:
    """Tests for formatting Google results."""

    def test_format_google_results_success(self, handler, google_provider):
        """Test formatting successful Google results."""
        results = [
            CapabilityResult(
                capability_call_id="google_call_0",
                name="get_weather",
                result={"temperature": 72, "condition": "sunny"},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, google_provider)

        assert len(formatted) == 1
        assert "functionResponse" in formatted[0]
        assert formatted[0]["functionResponse"]["name"] == "get_weather"
        assert formatted[0]["functionResponse"]["response"] == {
            "temperature": 72,
            "condition": "sunny",
        }


class TestFormatAzureResults:
    """Tests for formatting Azure results (same as OpenAI)."""

    def test_format_azure_results_success(self, handler, azure_provider):
        """Test formatting successful Azure results."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result={"temperature": 72},
                error=None,
            )
        ]

        formatted = handler.format_capability_results(results, azure_provider)

        assert len(formatted) == 1
        assert formatted[0]["tool_call_id"] == "call_1"
        assert formatted[0]["role"] == "tool"


class TestFormatUnsupportedProvider:
    """Tests for formatting with unsupported provider."""

    def test_format_unsupported_provider(self, handler, unsupported_provider):
        """Test formatting with unsupported provider."""
        results = [
            CapabilityResult(
                capability_call_id="call_1",
                name="get_weather",
                result={"temperature": 72},
                error=None,
            )
        ]

        with pytest.raises(CapabilityCallParsingError) as exc_info:
            handler.format_capability_results(results, unsupported_provider)

        assert "does not support capability result formatting" in str(exc_info.value)
