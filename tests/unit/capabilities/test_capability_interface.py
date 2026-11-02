"""Tests for CapabilityInterface abstract class."""

import pytest

from skye.tools.interface import CapabilityInterface
from skye.tools.schema import CapabilitySchema


class MockCapability(CapabilityInterface):
    """Mock implementation of CapabilityInterface for testing."""

    def __init__(
        self,
        name: str = "mock_tool",
        description: str = "A mock tool",
        result: str = "mock_result",
    ) -> None:
        """Initialize mock capability."""
        self.name = name
        self.description = description
        self.result = result
        self.execute_called = False
        self.aexecute_called = False
        self.last_kwargs: dict = {}

    def get_schema(self) -> CapabilitySchema:
        """Return mock schema."""
        return CapabilitySchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {"param": {"type": "string"}},
            },
            returns={"type": "string"},
        )

    def execute(self, **kwargs) -> str:
        """Execute mock capability."""
        self.execute_called = True
        self.last_kwargs = kwargs
        return self.result

    async def aexecute(self, **kwargs) -> str:
        """Execute mock capability asynchronously."""
        self.aexecute_called = True
        self.last_kwargs = kwargs
        return self.result


class TestCapabilityInterfaceCompliance:
    """Test that implementations comply with CapabilityInterface."""

    def test_mock_capability_implements_interface(self) -> None:
        """Test that MockCapability properly implements CapabilityInterface."""
        capability = MockCapability()
        assert isinstance(capability, CapabilityInterface)

    def test_get_schema_returns_capability_schema(self) -> None:
        """Test that get_schema returns a CapabilitySchema."""
        capability = MockCapability(name="test_tool", description="Test tool")
        schema = capability.get_schema()

        assert isinstance(schema, CapabilitySchema)
        assert schema.name == "test_tool"
        assert schema.description == "Test tool"

    def test_execute_method_exists_and_callable(self) -> None:
        """Test that execute method exists and is callable."""
        capability = MockCapability()
        assert hasattr(capability, "execute")
        assert callable(capability.execute)

    def test_aexecute_method_exists_and_callable(self) -> None:
        """Test that aexecute method exists and is callable."""
        capability = MockCapability()
        assert hasattr(capability, "aexecute")
        assert callable(capability.aexecute)


class TestCapabilityInterfaceExecution:
    """Test capability execution methods."""

    def test_execute_returns_result(self) -> None:
        """Test that execute returns the expected result."""
        capability = MockCapability(result="test_result")
        result = capability.execute()

        assert result == "test_result"
        assert capability.execute_called is True

    def test_execute_receives_kwargs(self) -> None:
        """Test that execute receives keyword arguments."""
        capability = MockCapability()
        capability.execute(param1="value1", param2="value2")

        assert capability.last_kwargs == {"param1": "value1", "param2": "value2"}

    @pytest.mark.asyncio
    async def test_aexecute_returns_result(self) -> None:
        """Test that aexecute returns the expected result."""
        capability = MockCapability(result="async_result")
        result = await capability.aexecute()

        assert result == "async_result"
        assert capability.aexecute_called is True

    @pytest.mark.asyncio
    async def test_aexecute_receives_kwargs(self) -> None:
        """Test that aexecute receives keyword arguments."""
        capability = MockCapability()
        await capability.aexecute(param1="value1", param2="value2")

        assert capability.last_kwargs == {"param1": "value1", "param2": "value2"}


class TestCapabilityInterfaceSchema:
    """Test capability schema retrieval."""

    def test_schema_contains_required_fields(self) -> None:
        """Test that schema contains all required fields."""
        capability = MockCapability()
        schema = capability.get_schema()

        assert hasattr(schema, "name")
        assert hasattr(schema, "description")
        assert hasattr(schema, "parameters")
        assert hasattr(schema, "returns")

    def test_schema_name_matches_capability(self) -> None:
        """Test that schema name matches capability name."""
        capability = MockCapability(name="my_tool")
        schema = capability.get_schema()

        assert schema.name == "my_tool"

    def test_schema_description_matches_capability(self) -> None:
        """Test that schema description matches capability description."""
        capability = MockCapability(description="My tool description")
        schema = capability.get_schema()

        assert schema.description == "My tool description"

    def test_schema_parameters_are_valid_json_schema(self) -> None:
        """Test that schema parameters follow JSON Schema format."""
        capability = MockCapability()
        schema = capability.get_schema()

        assert isinstance(schema.parameters, dict)
        assert "type" in schema.parameters or len(schema.parameters) == 0

    def test_schema_returns_are_valid_json_schema(self) -> None:
        """Test that schema returns follow JSON Schema format."""
        capability = MockCapability()
        schema = capability.get_schema()

        assert isinstance(schema.returns, dict)
        assert "type" in schema.returns or len(schema.returns) == 0


class TestCapabilityInterfaceAbstractness:
    """Test that CapabilityInterface cannot be instantiated directly."""

    def test_cannot_instantiate_interface_directly(self) -> None:
        """Test that CapabilityInterface cannot be instantiated."""
        with pytest.raises(TypeError):
            CapabilityInterface()  # type: ignore

    def test_must_implement_all_abstract_methods(self) -> None:
        """Test that subclasses must implement all abstract methods."""

        class IncompleteCapability(CapabilityInterface):
            """Incomplete implementation missing execute method."""

            def get_schema(self) -> CapabilitySchema:
                return CapabilitySchema(name="test", description="test")

            async def aexecute(self, **kwargs) -> None:
                pass

        # Should raise TypeError because execute is not implemented
        with pytest.raises(TypeError):
            IncompleteCapability()  # type: ignore


class TestCapabilityInterfaceMultipleImplementations:
    """Test multiple implementations of CapabilityInterface."""

    def test_different_implementations_can_coexist(self) -> None:
        """Test that different capability implementations can coexist."""

        class Capability1(CapabilityInterface):
            def get_schema(self) -> CapabilitySchema:
                return CapabilitySchema(name="cap1", description="Capability 1")

            def execute(self, **kwargs) -> str:
                return "cap1"

            async def aexecute(self, **kwargs) -> str:
                return "cap1"

        class Capability2(CapabilityInterface):
            def get_schema(self) -> CapabilitySchema:
                return CapabilitySchema(name="cap2", description="Capability 2")

            def execute(self, **kwargs) -> str:
                return "cap2"

            async def aexecute(self, **kwargs) -> str:
                return "cap2"

        cap1 = Capability1()
        cap2 = Capability2()

        assert cap1.get_schema().name == "cap1"
        assert cap2.get_schema().name == "cap2"
        assert cap1.execute() == "cap1"
        assert cap2.execute() == "cap2"
