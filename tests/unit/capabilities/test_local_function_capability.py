"""Tests for LocalFunctionCapability."""

import asyncio
from typing import Any

import pytest

from nimbus.capabilities.exceptions import CapabilityValidationError
from nimbus.capabilities.local_function import LocalFunctionCapability
from nimbus.capabilities.schema import CapabilitySchema


class TestLocalFunctionCapabilityCreation:
    """Test creating LocalFunctionCapability instances."""

    def test_create_from_simple_function(self) -> None:
        """Test creating capability from a simple function."""

        def simple_func(x: str) -> str:
            """A simple function."""
            return x.upper()

        capability = LocalFunctionCapability(simple_func)
        assert capability.func is simple_func
        assert capability._name == "simple_func"

    def test_create_with_custom_name(self) -> None:
        """Test creating capability with custom name."""

        def my_func() -> str:
            """A function."""
            return "result"

        capability = LocalFunctionCapability(my_func, name="custom_name")
        assert capability._name == "custom_name"

    def test_create_with_custom_description(self) -> None:
        """Test creating capability with custom description."""

        def my_func() -> str:
            return "result"

        capability = LocalFunctionCapability(
            my_func, description="Custom description"
        )
        assert capability._description == "Custom description"

    def test_create_with_schema_override(self) -> None:
        """Test creating capability with schema override."""

        def my_func(x: str) -> str:
            return x

        schema = CapabilitySchema(
            name="override_name",
            description="Override description",
            parameters={"type": "object", "properties": {"x": {"type": "string"}}},
            returns={"type": "string"},
        )

        capability = LocalFunctionCapability(my_func, schema_override=schema)
        assert capability._schema_override is schema

    def test_reject_non_callable(self) -> None:
        """Test that non-callable objects are rejected."""
        with pytest.raises(CapabilityValidationError) as exc_info:
            LocalFunctionCapability("not_callable")  # type: ignore

        assert "callable" in str(exc_info.value).lower()

    def test_extract_docstring_from_function(self) -> None:
        """Test that docstring is extracted from function."""

        def my_func() -> str:
            """This is my function."""
            return "result"

        capability = LocalFunctionCapability(my_func)
        assert capability._description == "This is my function."

    def test_extract_multiline_docstring(self) -> None:
        """Test that only first line of docstring is extracted."""

        def my_func() -> str:
            """First line of docstring.
            
            Second line of docstring.
            """
            return "result"

        capability = LocalFunctionCapability(my_func)
        assert capability._description == "First line of docstring."

    def test_handle_function_without_docstring(self) -> None:
        """Test handling function without docstring."""

        def my_func() -> str:
            return "result"

        capability = LocalFunctionCapability(my_func)
        assert capability._description == ""


class TestLocalFunctionCapabilitySchema:
    """Test schema extraction from functions."""

    def test_schema_extraction_simple_function(self) -> None:
        """Test schema extraction from simple function."""

        def get_greeting(name: str) -> str:
            """Get a greeting."""
            return f"Hello, {name}!"

        capability = LocalFunctionCapability(get_greeting)
        schema = capability.get_schema()

        assert schema.name == "get_greeting"
        assert schema.description == "Get a greeting."
        assert schema.parameters["type"] == "object"
        assert "name" in schema.parameters["properties"]
        assert schema.parameters["required"] == ["name"]

    def test_schema_extraction_with_multiple_parameters(self) -> None:
        """Test schema extraction with multiple parameters."""

        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        capability = LocalFunctionCapability(add)
        schema = capability.get_schema()

        assert "a" in schema.parameters["properties"]
        assert "b" in schema.parameters["properties"]
        assert schema.parameters["properties"]["a"]["type"] == "integer"
        assert schema.parameters["properties"]["b"]["type"] == "integer"
        assert set(schema.parameters["required"]) == {"a", "b"}

    def test_schema_extraction_with_optional_parameters(self) -> None:
        """Test schema extraction with optional parameters."""

        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone."""
            return f"{greeting}, {name}!"

        capability = LocalFunctionCapability(greet)
        schema = capability.get_schema()

        assert "name" in schema.parameters["required"]
        assert "greeting" not in schema.parameters["required"]

    def test_schema_extraction_with_type_hints(self) -> None:
        """Test schema extraction with various type hints."""

        def process(
            text: str, count: int, ratio: float, enabled: bool
        ) -> dict[str, Any]:
            """Process data."""
            return {"text": text, "count": count}

        capability = LocalFunctionCapability(process)
        schema = capability.get_schema()

        assert schema.parameters["properties"]["text"]["type"] == "string"
        assert schema.parameters["properties"]["count"]["type"] == "integer"
        assert schema.parameters["properties"]["ratio"]["type"] == "number"
        assert schema.parameters["properties"]["enabled"]["type"] == "boolean"

    def test_schema_extraction_with_list_parameter(self) -> None:
        """Test schema extraction with list parameter."""

        def process_items(items: list[str]) -> int:
            """Process a list of items."""
            return len(items)

        capability = LocalFunctionCapability(process_items)
        schema = capability.get_schema()

        assert schema.parameters["properties"]["items"]["type"] == "array"

    def test_schema_extraction_with_dict_parameter(self) -> None:
        """Test schema extraction with dict parameter."""

        def process_config(config: dict[str, Any]) -> str:
            """Process configuration."""
            return str(config)

        capability = LocalFunctionCapability(process_config)
        schema = capability.get_schema()

        assert schema.parameters["properties"]["config"]["type"] == "object"

    def test_schema_extraction_without_type_hints(self) -> None:
        """Test schema extraction for function without type hints."""

        def my_func(x, y):
            """A function without type hints."""
            return x + y

        capability = LocalFunctionCapability(my_func)
        schema = capability.get_schema()

        # Should default to string type
        assert schema.parameters["properties"]["x"]["type"] == "string"
        assert schema.parameters["properties"]["y"]["type"] == "string"

    def test_schema_extraction_return_type(self) -> None:
        """Test schema extraction of return type."""

        def get_count() -> int:
            """Get a count."""
            return 42

        capability = LocalFunctionCapability(get_count)
        schema = capability.get_schema()

        assert schema.returns["type"] == "integer"

    def test_schema_extraction_no_return_type(self) -> None:
        """Test schema extraction when no return type is specified."""

        def my_func():
            """A function."""
            return "result"

        capability = LocalFunctionCapability(my_func)
        schema = capability.get_schema()

        # Should default to string type
        assert schema.returns["type"] == "string"

    def test_schema_override_takes_precedence(self) -> None:
        """Test that schema override takes precedence over extraction."""

        def my_func(x: int) -> int:
            """A function."""
            return x * 2

        override_schema = CapabilitySchema(
            name="override",
            description="Override description",
            parameters={"type": "object", "properties": {}},
            returns={"type": "string"},
        )

        capability = LocalFunctionCapability(my_func, schema_override=override_schema)
        schema = capability.get_schema()

        assert schema.name == "override"
        assert schema.description == "Override description"


class TestLocalFunctionCapabilityExecution:
    """Test executing local functions."""

    def test_execute_simple_function(self) -> None:
        """Test executing a simple function."""

        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        capability = LocalFunctionCapability(add)
        result = capability.execute(a=2, b=3)

        assert result == 5

    def test_execute_with_string_parameter(self) -> None:
        """Test executing function with string parameter."""

        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        capability = LocalFunctionCapability(greet)
        result = capability.execute(name="Alice")

        assert result == "Hello, Alice!"

    def test_execute_with_optional_parameter(self) -> None:
        """Test executing function with optional parameter."""

        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone."""
            return f"{greeting}, {name}!"

        capability = LocalFunctionCapability(greet)

        # With optional parameter
        result = capability.execute(name="Alice", greeting="Hi")
        assert result == "Hi, Alice!"

        # Without optional parameter
        result = capability.execute(name="Bob")
        assert result == "Hello, Bob!"

    def test_execute_returns_various_types(self) -> None:
        """Test that execute can return various types."""

        def return_dict() -> dict[str, Any]:
            """Return a dictionary."""
            return {"key": "value", "number": 42}

        capability = LocalFunctionCapability(return_dict)
        result = capability.execute()

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_execute_function_that_raises_exception(self) -> None:
        """Test that exceptions from function are propagated."""

        def failing_func() -> None:
            """A function that fails."""
            raise ValueError("Something went wrong")

        capability = LocalFunctionCapability(failing_func)

        with pytest.raises(ValueError) as exc_info:
            capability.execute()

        assert "Something went wrong" in str(exc_info.value)

    def test_execute_async_function_raises_error(self) -> None:
        """Test that executing async function synchronously raises error."""

        async def async_func() -> str:
            """An async function."""
            return "result"

        capability = LocalFunctionCapability(async_func)

        with pytest.raises(CapabilityValidationError) as exc_info:
            capability.execute()

        assert "async" in str(exc_info.value).lower()


class TestLocalFunctionCapabilityAsyncExecution:
    """Test async execution of local functions."""

    @pytest.mark.asyncio
    async def test_aexecute_async_function(self) -> None:
        """Test executing an async function."""

        async def async_add(a: int, b: int) -> int:
            """Add two numbers asynchronously."""
            await asyncio.sleep(0.01)
            return a + b

        capability = LocalFunctionCapability(async_add)
        result = await capability.aexecute(a=2, b=3)

        assert result == 5

    @pytest.mark.asyncio
    async def test_aexecute_sync_function(self) -> None:
        """Test executing a sync function asynchronously."""

        def sync_add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        capability = LocalFunctionCapability(sync_add)
        result = await capability.aexecute(a=2, b=3)

        assert result == 5

    @pytest.mark.asyncio
    async def test_aexecute_with_string_parameter(self) -> None:
        """Test async execution with string parameter."""

        async def greet(name: str) -> str:
            """Greet someone asynchronously."""
            await asyncio.sleep(0.01)
            return f"Hello, {name}!"

        capability = LocalFunctionCapability(greet)
        result = await capability.aexecute(name="Alice")

        assert result == "Hello, Alice!"

    @pytest.mark.asyncio
    async def test_aexecute_returns_various_types(self) -> None:
        """Test that aexecute can return various types."""

        async def return_dict() -> dict[str, Any]:
            """Return a dictionary asynchronously."""
            await asyncio.sleep(0.01)
            return {"key": "value", "number": 42}

        capability = LocalFunctionCapability(return_dict)
        result = await capability.aexecute()

        assert isinstance(result, dict)
        assert result["key"] == "value"

    @pytest.mark.asyncio
    async def test_aexecute_async_function_that_raises_exception(self) -> None:
        """Test that exceptions from async function are propagated."""

        async def failing_func() -> None:
            """An async function that fails."""
            await asyncio.sleep(0.01)
            raise ValueError("Something went wrong")

        capability = LocalFunctionCapability(failing_func)

        with pytest.raises(ValueError) as exc_info:
            await capability.aexecute()

        assert "Something went wrong" in str(exc_info.value)


class TestLocalFunctionCapabilityArgumentValidation:
    """Test argument validation."""

    def test_validate_missing_required_parameter(self) -> None:
        """Test that missing required parameter is caught."""

        def my_func(required_param: str) -> str:
            """A function."""
            return required_param

        capability = LocalFunctionCapability(my_func)

        with pytest.raises(CapabilityValidationError) as exc_info:
            capability.execute()

        assert "required_param" in str(exc_info.value)

    def test_validate_unexpected_parameter(self) -> None:
        """Test that unexpected parameter is caught."""

        def my_func(x: str) -> str:
            """A function."""
            return x

        capability = LocalFunctionCapability(my_func)

        with pytest.raises(CapabilityValidationError) as exc_info:
            capability.execute(x="value", unexpected="param")

        assert "unexpected" in str(exc_info.value)

    def test_validate_all_required_parameters_present(self) -> None:
        """Test that validation passes when all required parameters are present."""

        def my_func(a: str, b: int) -> str:
            """A function."""
            return f"{a}:{b}"

        capability = LocalFunctionCapability(my_func)
        result = capability.execute(a="test", b=42)

        assert result == "test:42"

    def test_validate_optional_parameters_not_required(self) -> None:
        """Test that optional parameters are not required."""

        def my_func(required: str, optional: str = "default") -> str:
            """A function."""
            return f"{required}:{optional}"

        capability = LocalFunctionCapability(my_func)
        result = capability.execute(required="test")

        assert result == "test:default"

    @pytest.mark.asyncio
    async def test_validate_arguments_in_aexecute(self) -> None:
        """Test that argument validation works in aexecute."""

        async def my_func(required_param: str) -> str:
            """A function."""
            return required_param

        capability = LocalFunctionCapability(my_func)

        with pytest.raises(CapabilityValidationError) as exc_info:
            await capability.aexecute()

        assert "required_param" in str(exc_info.value)


class TestLocalFunctionCapabilityIntegration:
    """Integration tests for LocalFunctionCapability."""

    def test_full_workflow_sync(self) -> None:
        """Test full workflow: create, get schema, execute."""

        def calculate(x: int, y: int) -> int:
            """Calculate sum of two numbers."""
            return x + y

        capability = LocalFunctionCapability(calculate)

        # Get schema
        schema = capability.get_schema()
        assert schema.name == "calculate"
        assert schema.description == "Calculate sum of two numbers."

        # Execute
        result = capability.execute(x=10, y=20)
        assert result == 30

    @pytest.mark.asyncio
    async def test_full_workflow_async(self) -> None:
        """Test full workflow with async function."""

        async def calculate(x: int, y: int) -> int:
            """Calculate sum of two numbers."""
            await asyncio.sleep(0.01)
            return x + y

        capability = LocalFunctionCapability(calculate)

        # Get schema
        schema = capability.get_schema()
        assert schema.name == "calculate"

        # Execute async
        result = await capability.aexecute(x=10, y=20)
        assert result == 30

    def test_capability_with_complex_return_type(self) -> None:
        """Test capability that returns complex types."""

        def get_user_info(user_id: int) -> dict[str, Any]:
            """Get user information."""
            return {
                "id": user_id,
                "name": "John Doe",
                "email": "john@example.com",
                "tags": ["admin", "user"],
            }

        capability = LocalFunctionCapability(get_user_info)
        result = capability.execute(user_id=123)

        assert result["id"] == 123
        assert result["name"] == "John Doe"
        assert "admin" in result["tags"]

    def test_capability_with_no_parameters(self) -> None:
        """Test capability with no parameters."""

        def get_timestamp() -> str:
            """Get current timestamp."""
            return "2024-01-01T00:00:00Z"

        capability = LocalFunctionCapability(get_timestamp)
        schema = capability.get_schema()

        assert schema.parameters["required"] == []
        result = capability.execute()
        assert result == "2024-01-01T00:00:00Z"

    def test_capability_with_list_return_type(self) -> None:
        """Test capability that returns a list."""

        def get_items() -> list[str]:
            """Get list of items."""
            return ["item1", "item2", "item3"]

        capability = LocalFunctionCapability(get_items)
        result = capability.execute()

        assert isinstance(result, list)
        assert len(result) == 3
        assert "item1" in result
