"""Tests for ToolCall and ToolResult models."""

import pytest
from pydantic import ValidationError

from nimbus.capabilities.tool_models import ToolCall, ToolResult


class TestToolCallCreation:
    """Test creating valid ToolCall instances."""

    def test_create_valid_tool_call(self) -> None:
        """Test creating a valid tool call."""
        tool_call = ToolCall(
            id="call_123",
            name="weather.get_current",
            arguments={"location": "San Francisco"},
        )

        assert tool_call.id == "call_123"
        assert tool_call.name == "weather.get_current"
        assert tool_call.arguments == {"location": "San Francisco"}

    def test_create_tool_call_with_empty_arguments(self) -> None:
        """Test creating a tool call with no arguments."""
        tool_call = ToolCall(
            id="call_456",
            name="simple_tool",
        )

        assert tool_call.id == "call_456"
        assert tool_call.name == "simple_tool"
        assert tool_call.arguments == {}

    def test_create_tool_call_with_complex_arguments(self) -> None:
        """Test creating a tool call with complex nested arguments."""
        tool_call = ToolCall(
            id="call_789",
            name="database.query",
            arguments={
                "query": "SELECT * FROM users",
                "filters": {
                    "age": {"min": 18, "max": 65},
                    "status": "active",
                },
                "limit": 100,
            },
        )

        assert tool_call.arguments["query"] == "SELECT * FROM users"
        assert tool_call.arguments["filters"]["age"]["min"] == 18
        assert tool_call.arguments["limit"] == 100

    def test_create_tool_call_with_various_argument_types(self) -> None:
        """Test creating a tool call with various argument types."""
        tool_call = ToolCall(
            id="call_mixed",
            name="mixed_types",
            arguments={
                "string_arg": "hello",
                "int_arg": 42,
                "float_arg": 3.14,
                "bool_arg": True,
                "list_arg": [1, 2, 3],
                "dict_arg": {"key": "value"},
                "none_arg": None,
            },
        )

        assert tool_call.arguments["string_arg"] == "hello"
        assert tool_call.arguments["int_arg"] == 42
        assert tool_call.arguments["float_arg"] == 3.14
        assert tool_call.arguments["bool_arg"] is True
        assert tool_call.arguments["list_arg"] == [1, 2, 3]
        assert tool_call.arguments["dict_arg"] == {"key": "value"}
        assert tool_call.arguments["none_arg"] is None


class TestToolCallValidation:
    """Test validation of ToolCall."""

    def test_reject_missing_id(self) -> None:
        """Test that missing id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ToolCall(
                name="test_tool",
                arguments={},
            )
        assert "id" in str(exc_info.value).lower()

    def test_reject_missing_name(self) -> None:
        """Test that missing name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ToolCall(
                id="call_123",
                arguments={},
            )
        assert "name" in str(exc_info.value).lower()

    def test_accept_empty_id_string(self) -> None:
        """Test that empty id string is accepted (validation at provider level)."""
        # Empty strings are technically valid at Pydantic level
        # Provider-specific validation would happen elsewhere
        tool_call = ToolCall(
            id="",
            name="test_tool",
        )
        assert tool_call.id == ""

    def test_accept_empty_name_string(self) -> None:
        """Test that empty name string is accepted (validation at provider level)."""
        # Empty strings are technically valid at Pydantic level
        # Provider-specific validation would happen elsewhere
        tool_call = ToolCall(
            id="call_123",
            name="",
        )
        assert tool_call.name == ""


class TestToolResultCreation:
    """Test creating valid ToolResult instances."""

    def test_create_successful_tool_result(self) -> None:
        """Test creating a successful tool result."""
        result = ToolResult(
            tool_call_id="call_123",
            name="weather.get_current",
            result={"temperature": 72, "condition": "sunny"},
        )

        assert result.tool_call_id == "call_123"
        assert result.name == "weather.get_current"
        assert result.result == {"temperature": 72, "condition": "sunny"}
        assert result.error is None

    def test_create_failed_tool_result(self) -> None:
        """Test creating a failed tool result with error."""
        result = ToolResult(
            tool_call_id="call_456",
            name="weather.get_current",
            result=None,
            error="Location not found",
        )

        assert result.tool_call_id == "call_456"
        assert result.name == "weather.get_current"
        assert result.result is None
        assert result.error == "Location not found"

    def test_create_tool_result_with_string_result(self) -> None:
        """Test creating a tool result with string return value."""
        result = ToolResult(
            tool_call_id="call_789",
            name="text_processor",
            result="Processed text output",
        )

        assert result.result == "Processed text output"
        assert result.error is None

    def test_create_tool_result_with_list_result(self) -> None:
        """Test creating a tool result with list return value."""
        result = ToolResult(
            tool_call_id="call_list",
            name="search",
            result=["item1", "item2", "item3"],
        )

        assert result.result == ["item1", "item2", "item3"]
        assert result.error is None

    def test_create_tool_result_with_numeric_result(self) -> None:
        """Test creating a tool result with numeric return value."""
        result = ToolResult(
            tool_call_id="call_calc",
            name="calculator",
            result=42,
        )

        assert result.result == 42
        assert result.error is None

    def test_create_tool_result_with_complex_result(self) -> None:
        """Test creating a tool result with complex nested result."""
        result = ToolResult(
            tool_call_id="call_complex",
            name="database.query",
            result={
                "rows": [
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"},
                ],
                "count": 2,
                "metadata": {"query_time_ms": 45},
            },
        )

        assert result.result["rows"][0]["name"] == "Alice"
        assert result.result["count"] == 2
        assert result.result["metadata"]["query_time_ms"] == 45

    def test_create_tool_result_with_both_result_and_error(self) -> None:
        """Test creating a tool result with both result and error (edge case)."""
        result = ToolResult(
            tool_call_id="call_edge",
            name="partial_tool",
            result={"partial": "data"},
            error="Partial failure occurred",
        )

        assert result.result == {"partial": "data"}
        assert result.error == "Partial failure occurred"


class TestToolResultValidation:
    """Test validation of ToolResult."""

    def test_reject_missing_tool_call_id(self) -> None:
        """Test that missing tool_call_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ToolResult(
                name="test_tool",
                result="success",
            )
        assert "tool_call_id" in str(exc_info.value).lower()

    def test_reject_missing_name(self) -> None:
        """Test that missing name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ToolResult(
                tool_call_id="call_123",
                result="success",
            )
        assert "name" in str(exc_info.value).lower()

    def test_accept_missing_result(self) -> None:
        """Test that missing result defaults to None."""
        result = ToolResult(
            tool_call_id="call_123",
            name="test_tool",
        )

        assert result.result is None
        assert result.error is None

    def test_accept_missing_error(self) -> None:
        """Test that missing error defaults to None."""
        result = ToolResult(
            tool_call_id="call_123",
            name="test_tool",
            result="success",
        )

        assert result.error is None


class TestToolCallSerialization:
    """Test serialization and deserialization of ToolCall."""

    def test_tool_call_to_dict(self) -> None:
        """Test converting ToolCall to dictionary."""
        tool_call = ToolCall(
            id="call_123",
            name="weather.get_current",
            arguments={"location": "San Francisco"},
        )

        data = tool_call.model_dump()

        assert data["id"] == "call_123"
        assert data["name"] == "weather.get_current"
        assert data["arguments"] == {"location": "San Francisco"}

    def test_tool_call_to_json(self) -> None:
        """Test converting ToolCall to JSON string."""
        tool_call = ToolCall(
            id="call_123",
            name="weather.get_current",
            arguments={"location": "San Francisco"},
        )

        json_str = tool_call.model_dump_json()

        assert "call_123" in json_str
        assert "weather.get_current" in json_str
        assert "San Francisco" in json_str

    def test_tool_call_from_dict(self) -> None:
        """Test creating ToolCall from dictionary."""
        data = {
            "id": "call_456",
            "name": "database.query",
            "arguments": {"query": "SELECT * FROM users"},
        }

        tool_call = ToolCall(**data)

        assert tool_call.id == "call_456"
        assert tool_call.name == "database.query"
        assert tool_call.arguments["query"] == "SELECT * FROM users"

    def test_tool_call_from_json(self) -> None:
        """Test creating ToolCall from JSON string."""
        json_str = '{"id": "call_789", "name": "test_tool", "arguments": {"key": "value"}}'

        tool_call = ToolCall.model_validate_json(json_str)

        assert tool_call.id == "call_789"
        assert tool_call.name == "test_tool"
        assert tool_call.arguments["key"] == "value"


class TestToolResultSerialization:
    """Test serialization and deserialization of ToolResult."""

    def test_tool_result_to_dict(self) -> None:
        """Test converting ToolResult to dictionary."""
        result = ToolResult(
            tool_call_id="call_123",
            name="weather.get_current",
            result={"temperature": 72},
        )

        data = result.model_dump()

        assert data["tool_call_id"] == "call_123"
        assert data["name"] == "weather.get_current"
        assert data["result"] == {"temperature": 72}
        assert data["error"] is None

    def test_tool_result_to_json(self) -> None:
        """Test converting ToolResult to JSON string."""
        result = ToolResult(
            tool_call_id="call_123",
            name="weather.get_current",
            result={"temperature": 72},
            error=None,
        )

        json_str = result.model_dump_json()

        assert "call_123" in json_str
        assert "weather.get_current" in json_str
        assert "72" in json_str

    def test_tool_result_from_dict(self) -> None:
        """Test creating ToolResult from dictionary."""
        data = {
            "tool_call_id": "call_456",
            "name": "database.query",
            "result": [{"id": 1}, {"id": 2}],
            "error": None,
        }

        result = ToolResult(**data)

        assert result.tool_call_id == "call_456"
        assert result.name == "database.query"
        assert len(result.result) == 2

    def test_tool_result_from_json(self) -> None:
        """Test creating ToolResult from JSON string."""
        json_str = '{"tool_call_id": "call_789", "name": "test_tool", "result": "success", "error": null}'

        result = ToolResult.model_validate_json(json_str)

        assert result.tool_call_id == "call_789"
        assert result.name == "test_tool"
        assert result.result == "success"
        assert result.error is None

    def test_tool_result_error_serialization(self) -> None:
        """Test serializing ToolResult with error."""
        result = ToolResult(
            tool_call_id="call_error",
            name="failing_tool",
            result=None,
            error="Tool execution failed",
        )

        data = result.model_dump()

        assert data["error"] == "Tool execution failed"
        assert data["result"] is None

    def test_tool_result_error_json_serialization(self) -> None:
        """Test JSON serializing ToolResult with error."""
        result = ToolResult(
            tool_call_id="call_error",
            name="failing_tool",
            result=None,
            error="Tool execution failed",
        )

        json_str = result.model_dump_json()

        assert "Tool execution failed" in json_str
        assert "call_error" in json_str


class TestToolCallAndResultIntegration:
    """Test integration between ToolCall and ToolResult."""

    def test_tool_call_and_result_correspondence(self) -> None:
        """Test that ToolResult correctly corresponds to ToolCall."""
        tool_call = ToolCall(
            id="call_123",
            name="weather.get_current",
            arguments={"location": "San Francisco"},
        )

        result = ToolResult(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            result={"temperature": 72, "condition": "sunny"},
        )

        assert result.tool_call_id == tool_call.id
        assert result.name == tool_call.name

    def test_multiple_tool_calls_and_results(self) -> None:
        """Test handling multiple tool calls and results."""
        tool_calls = [
            ToolCall(
                id="call_1",
                name="weather.get_current",
                arguments={"location": "SF"},
            ),
            ToolCall(
                id="call_2",
                name="weather.get_forecast",
                arguments={"location": "SF", "days": 3},
            ),
        ]

        results = [
            ToolResult(
                tool_call_id="call_1",
                name="weather.get_current",
                result={"temperature": 72},
            ),
            ToolResult(
                tool_call_id="call_2",
                name="weather.get_forecast",
                result={"forecast": ["sunny", "cloudy", "rainy"]},
            ),
        ]

        assert len(tool_calls) == len(results)
        for tool_call, result in zip(tool_calls, results):
            assert result.tool_call_id == tool_call.id
            assert result.name == tool_call.name
