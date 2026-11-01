"""Tests for @capability decorator."""

import pytest

from nimbus.tools.decorator import capability
from nimbus.tools.exceptions import CapabilityValidationError
from nimbus.tools.interface import CapabilityInterface
from nimbus.tools.local_function import LocalFunctionCapability
from nimbus.tools.schema import CapabilitySchema


class TestCapabilityDecorator:
    """Test @capability decorator."""

    def test_decorator_without_arguments(self) -> None:
        """Test @capability decorator without arguments."""

        @capability
        def my_tool(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        assert isinstance(my_tool, CapabilityInterface)
        assert isinstance(my_tool, LocalFunctionCapability)

    def test_decorator_with_name_argument(self) -> None:
        """Test @capability decorator with name argument."""

        @capability(name="custom_name")
        def my_tool(location: str) -> str:
            """Get weather for a location."""
            return f"Weather for {location}"

        schema = my_tool.get_schema()
        assert schema.name == "custom_name"

    def test_decorator_with_description_argument(self) -> None:
        """Test @capability decorator with description argument."""

        @capability(description="Custom description")
        def my_tool(location: str) -> str:
            """Original docstring."""
            return f"Weather for {location}"

        schema = my_tool.get_schema()
        assert schema.description == "Custom description"

    def test_decorator_with_both_arguments(self) -> None:
        """Test @capability decorator with both name and description."""

        @capability(name="weather_tool", description="Get weather information")
        def my_tool(location: str) -> str:
            """Original docstring."""
            return f"Weather for {location}"

        schema = my_tool.get_schema()
        assert schema.name == "weather_tool"
        assert schema.description == "Get weather information"

    def test_decorated_function_is_executable(self) -> None:
        """Test that decorated function can be executed."""

        @capability
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        result = add.execute(a=2, b=3)
        assert result == 5

    def test_decorated_async_function_is_executable(self) -> None:
        """Test that decorated async function raises error when called sync."""

        @capability
        async def async_add(a: int, b: int) -> int:
            """Add two numbers asynchronously."""
            return a + b

        # Async functions should raise error when called with execute()
        with pytest.raises(CapabilityValidationError):
            async_add.execute(a=2, b=3)

    @pytest.mark.asyncio
    async def test_decorated_async_function_with_aexecute(self) -> None:
        """Test that decorated async function works with aexecute."""

        @capability
        async def async_add(a: int, b: int) -> int:
            """Add two numbers asynchronously."""
            return a + b

        result = await async_add.aexecute(a=2, b=3)
        assert result == 5


class TestFunctionCapabilitySchemaExtraction:
    """Test schema extraction from function signatures."""

    def test_extract_name_from_function(self) -> None:
        """Test that capability name is extracted from function name."""

        @capability
        def my_function() -> None:
            """Docstring."""
            pass

        schema = my_function.get_schema()
        assert schema.name == "my_function"

    def test_extract_description_from_docstring(self) -> None:
        """Test that description is extracted from docstring."""

        @capability
        def my_function() -> None:
            """This is my function description."""
            pass

        schema = my_function.get_schema()
        assert schema.description == "This is my function description."

    def test_extract_parameters_from_signature(self) -> None:
        """Test that parameters are extracted from function signature."""

        @capability
        def my_function(name: str, age: int) -> str:
            """Get user info."""
            return f"{name} is {age}"

        schema = my_function.get_schema()
        assert "name" in schema.parameters["properties"]
        assert "age" in schema.parameters["properties"]
        assert schema.parameters["properties"]["name"]["type"] == "string"
        assert schema.parameters["properties"]["age"]["type"] == "integer"

    def test_extract_required_parameters(self) -> None:
        """Test that required parameters are identified."""

        @capability
        def my_function(required_param: str, optional_param: str = "default") -> str:
            """Function with optional parameter."""
            return f"{required_param} {optional_param}"

        schema = my_function.get_schema()
        assert "required_param" in schema.parameters["required"]
        assert "optional_param" not in schema.parameters["required"]

    def test_extract_return_type(self) -> None:
        """Test that return type is extracted."""

        @capability
        def my_function() -> str:
            """Returns a string."""
            return "result"

        schema = my_function.get_schema()
        assert schema.returns["type"] == "string"

    def test_extract_return_type_integer(self) -> None:
        """Test that integer return type is extracted."""

        @capability
        def my_function() -> int:
            """Returns an integer."""
            return 42

        schema = my_function.get_schema()
        assert schema.returns["type"] == "integer"

    def test_extract_return_type_list(self) -> None:
        """Test that list return type is extracted."""

        @capability
        def my_function() -> list[str]:
            """Returns a list of strings."""
            return ["a", "b"]

        schema = my_function.get_schema()
        assert schema.returns["type"] == "array"

    def test_extract_return_type_dict(self) -> None:
        """Test that dict return type is extracted."""

        @capability
        def my_function() -> dict[str, str]:
            """Returns a dictionary."""
            return {"key": "value"}

        schema = my_function.get_schema()
        assert schema.returns["type"] == "object"

    def test_handle_no_docstring(self) -> None:
        """Test handling of function with no docstring."""

        @capability
        def my_function() -> None:
            pass

        schema = my_function.get_schema()
        assert schema.description == "No description provided"

    def test_handle_multiline_docstring(self) -> None:
        """Test that only first line of docstring is used."""

        @capability
        def my_function() -> None:
            """First line of description.
            
            Second line of description.
            """
            pass

        schema = my_function.get_schema()
        assert schema.description == "First line of description."

    def test_handle_no_type_hints(self) -> None:
        """Test handling of function with no type hints."""

        @capability
        def my_function(param):
            """Function without type hints."""
            return param

        schema = my_function.get_schema()
        # Should default to string type
        assert schema.parameters["properties"]["param"]["type"] == "string"


class TestFunctionCapabilityExecution:
    """Test execution of decorated functions."""

    def test_execute_sync_function(self) -> None:
        """Test executing a synchronous function."""

        @capability
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        result = add.execute(a=5, b=3)
        assert result == 8

    def test_execute_sync_function_with_kwargs(self) -> None:
        """Test executing sync function with keyword arguments."""

        @capability
        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone."""
            return f"{greeting}, {name}!"

        result = greet.execute(name="Alice", greeting="Hi")
        assert result == "Hi, Alice!"

    def test_execute_with_no_arguments(self) -> None:
        """Test executing function with no arguments."""

        @capability
        def get_time() -> str:
            """Get current time."""
            return "12:00"

        result = get_time.execute()
        assert result == "12:00"

    @pytest.mark.asyncio
    async def test_aexecute_async_function(self) -> None:
        """Test executing an async function with aexecute."""

        @capability
        async def async_add(a: int, b: int) -> int:
            """Add two numbers asynchronously."""
            return a + b

        result = await async_add.aexecute(a=5, b=3)
        assert result == 8

    def test_execute_async_function_sync_raises_error(self) -> None:
        """Test that calling execute on async function raises error."""

        @capability
        async def async_function() -> str:
            """Async function."""
            return "result"

        with pytest.raises(CapabilityValidationError):
            async_function.execute()

    @pytest.mark.asyncio
    async def test_aexecute_sync_function(self) -> None:
        """Test that aexecute works with sync functions."""

        @capability
        def sync_add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        result = await sync_add.aexecute(a=5, b=3)
        assert result == 8


class TestFunctionCapabilitySchemaOverride:
    """Test schema override functionality."""

    def test_schema_override_replaces_extracted_schema(self) -> None:
        """Test that schema override replaces extracted schema."""
        custom_schema = CapabilitySchema(
            name="custom_name",
            description="Custom description",
            parameters={"type": "object", "properties": {"custom": {"type": "string"}}},
            returns={"type": "string"},
        )

        def my_function(a: int) -> int:
            """Original description."""
            return a

        # Create capability with schema override
        capability_instance = LocalFunctionCapability(
            my_function, schema_override=custom_schema
        )

        schema = capability_instance.get_schema()
        assert schema.name == "custom_name"
        assert schema.description == "Custom description"
        assert "custom" in schema.parameters["properties"]
