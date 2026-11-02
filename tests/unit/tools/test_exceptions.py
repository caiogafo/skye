"""Unit tests for capability exceptions.

Tests exception creation, messages, and error context preservation.
"""

import pytest

from skye.tools.exceptions import (
    CapabilityError,
    CapabilityExecutionError,
    CapabilityNotFoundError,
    CapabilityValidationError,
    CapabilityCallParsingError,
)
from skye.base.exceptions import SkyeError


class TestCapabilityError:
    """Tests for CapabilityError base class."""

    def test_inherits_from_skye_error(self):
        """Test that CapabilityError inherits from SkyeError."""
        assert issubclass(CapabilityError, SkyeError)

    def test_basic_creation(self):
        """Test basic exception creation with message."""
        error = CapabilityError("Test error")
        assert error.message == "Test error"
        assert error.details == {}
        assert str(error) == "Test error"

    def test_creation_with_details(self):
        """Test exception creation with additional details."""
        error = CapabilityError("Test error", details={"key": "value"})
        assert error.message == "Test error"
        assert error.details == {"key": "value"}
        assert "key" in str(error)
        assert "value" in str(error)

    def test_repr(self):
        """Test exception repr."""
        error = CapabilityError("Test error", details={"key": "value"})
        repr_str = repr(error)
        assert "CapabilityError" in repr_str
        assert "Test error" in repr_str
        assert "key" in repr_str


class TestCapabilityNotFoundError:
    """Tests for CapabilityNotFoundError."""

    def test_inherits_from_capability_error(self):
        """Test that CapabilityNotFoundError inherits from CapabilityError."""
        assert issubclass(CapabilityNotFoundError, CapabilityError)

    def test_creation_with_capability_name(self):
        """Test exception creation with capability name."""
        error = CapabilityNotFoundError(
            "Capability not found", capability_name="get_weather"
        )
        assert error.message == "Capability not found"
        assert error.details["capability_name"] == "get_weather"

    def test_creation_with_additional_context(self):
        """Test exception creation with additional context."""
        error = CapabilityNotFoundError(
            "Capability not found",
            capability_name="get_weather",
            registry="global",
            available_capabilities=["get_time", "get_date"],
        )
        assert error.details["capability_name"] == "get_weather"
        assert error.details["registry"] == "global"
        assert error.details["available_capabilities"] == ["get_time", "get_date"]

    def test_error_message_includes_context(self):
        """Test that error message includes context in string representation."""
        error = CapabilityNotFoundError(
            "Capability not found", capability_name="get_weather"
        )
        error_str = str(error)
        assert "Capability not found" in error_str
        assert "get_weather" in error_str


class TestCapabilityValidationError:
    """Tests for CapabilityValidationError."""

    def test_inherits_from_capability_error(self):
        """Test that CapabilityValidationError inherits from CapabilityError."""
        assert issubclass(CapabilityValidationError, CapabilityError)

    def test_creation_with_capability_name(self):
        """Test exception creation with capability name."""
        error = CapabilityValidationError(
            "Schema validation failed", capability_name="get_weather"
        )
        assert error.message == "Schema validation failed"
        assert error.details["capability_name"] == "get_weather"

    def test_creation_with_validation_details(self):
        """Test exception creation with validation details."""
        error = CapabilityValidationError(
            "Invalid parameter type",
            capability_name="get_weather",
            parameter="location",
            expected_type="string",
            actual_type="integer",
        )
        assert error.details["capability_name"] == "get_weather"
        assert error.details["parameter"] == "location"
        assert error.details["expected_type"] == "string"
        assert error.details["actual_type"] == "integer"

    def test_error_context_preservation(self):
        """Test that error context is preserved in details."""
        error = CapabilityValidationError(
            "Validation failed",
            capability_name="test_capability",
            field="temperature",
            value=-100,
            constraint="must be >= 0",
        )
        assert error.details["field"] == "temperature"
        assert error.details["value"] == -100
        assert error.details["constraint"] == "must be >= 0"


class TestCapabilityExecutionError:
    """Tests for CapabilityExecutionError."""

    def test_inherits_from_capability_error(self):
        """Test that CapabilityExecutionError inherits from CapabilityError."""
        assert issubclass(CapabilityExecutionError, CapabilityError)

    def test_creation_with_capability_name(self):
        """Test exception creation with capability name."""
        error = CapabilityExecutionError(
            "Execution failed", capability_name="get_weather"
        )
        assert error.message == "Execution failed"
        assert error.details["capability_name"] == "get_weather"

    def test_creation_with_execution_context(self):
        """Test exception creation with execution context."""
        error = CapabilityExecutionError(
            "HTTP request failed",
            capability_name="fetch_data",
            status_code=500,
            url="https://api.example.com/data",
            original_error="Connection timeout",
        )
        assert error.details["capability_name"] == "fetch_data"
        assert error.details["status_code"] == 500
        assert error.details["url"] == "https://api.example.com/data"
        assert error.details["original_error"] == "Connection timeout"

    def test_error_context_with_exception(self):
        """Test that original exception context is preserved."""
        original_exception = ValueError("Invalid input")
        error = CapabilityExecutionError(
            "Capability failed",
            capability_name="process_data",
            original_exception=str(original_exception),
            exception_type=type(original_exception).__name__,
        )
        assert error.details["original_exception"] == "Invalid input"
        assert error.details["exception_type"] == "ValueError"


class TestCapabilityCallParsingError:
    """Tests for CapabilityCallParsingError."""

    def test_inherits_from_capability_error(self):
        """Test that CapabilityCallParsingError inherits from CapabilityError."""
        assert issubclass(CapabilityCallParsingError, CapabilityError)

    def test_creation_with_provider(self):
        """Test exception creation with provider name."""
        error = CapabilityCallParsingError("Failed to parse capability call", provider="openai")
        assert error.message == "Failed to parse capability call"
        assert error.details["provider"] == "openai"

    def test_creation_with_parsing_context(self):
        """Test exception creation with parsing context."""
        error = CapabilityCallParsingError(
            "Invalid capability call format",
            provider="anthropic",
            raw_response={"type": "tool_use", "name": "invalid"},
            expected_format="tool_use with id and input",
        )
        assert error.details["provider"] == "anthropic"
        assert error.details["raw_response"] == {"type": "tool_use", "name": "invalid"}
        assert error.details["expected_format"] == "tool_use with id and input"

    def test_error_context_preservation(self):
        """Test that parsing error context is preserved."""
        raw_data = {"function": {"name": "test", "arguments": "invalid json"}}
        error = CapabilityCallParsingError(
            "JSON parsing failed",
            provider="openai",
            raw_data=raw_data,
            parse_error="Expecting value: line 1 column 1 (char 0)",
        )
        assert error.details["raw_data"] == raw_data
        assert error.details["parse_error"] == "Expecting value: line 1 column 1 (char 0)"


class TestExceptionChaining:
    """Tests for exception chaining and context preservation."""

    def test_exception_chaining_with_from(self):
        """Test that exceptions can be chained with 'from' clause."""
        original = ValueError("Original error")
        try:
            try:
                raise original
            except ValueError as e:
                raise CapabilityExecutionError(
                    "Wrapped error", capability_name="test"
                ) from e
        except CapabilityExecutionError as wrapped:
            assert wrapped.__cause__ is original
            assert isinstance(wrapped.__cause__, ValueError)

    def test_context_preservation_across_chain(self):
        """Test that context is preserved across exception chain."""
        try:
            try:
                raise ValueError("Original error with context")
            except ValueError as e:
                raise CapabilityExecutionError(
                    "Execution failed",
                    capability_name="test_capability",
                    original_error=str(e),
                ) from e
        except CapabilityExecutionError as wrapped:
            assert "Original error with context" in wrapped.details["original_error"]
            assert wrapped.details["capability_name"] == "test_capability"


class TestExceptionMessages:
    """Tests for exception message formatting."""

    def test_message_without_details(self):
        """Test message formatting without details."""
        error = CapabilityError("Simple error")
        assert str(error) == "Simple error"

    def test_message_with_details(self):
        """Test message formatting with details."""
        error = CapabilityError("Error with context", details={"key": "value"})
        error_str = str(error)
        assert "Error with context" in error_str
        assert "Details:" in error_str
        assert "key" in error_str

    def test_nested_details(self):
        """Test message formatting with nested details."""
        error = CapabilityExecutionError(
            "Complex error",
            capability_name="test",
            nested_context={"inner_key": "inner_value", "count": 42},
        )
        error_str = str(error)
        assert "Complex error" in error_str
        assert "capability_name" in error_str
