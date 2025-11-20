"""Tests for ToolTransformer class."""

import pytest

from nimbus.capabilities.interface import CapabilityInterface
from nimbus.capabilities.schema import CapabilitySchema
from nimbus.capabilities.tool_transformer import ToolTransformer


class MockCapability(CapabilityInterface):
    """Mock capability for testing."""

    def __init__(self, schema: CapabilitySchema) -> None:
        """Initialize with a schema."""
        self._schema = schema

    def get_schema(self) -> CapabilitySchema:
        """Return the schema."""
        return self._schema

    def execute(self, **kwargs):  # type: ignore
        """Execute the capability."""
        return "result"

    async def aexecute(self, **kwargs):  # type: ignore
        """Execute the capability asynchronously."""
        return "result"


class TestToolTransformerOpenAI:
    """Test OpenAI format conversion."""

    def test_convert_simple_capability_to_openai_format(self) -> None:
        """Test converting a simple capability to OpenAI format."""
        schema = CapabilitySchema(
            name="get_weather",
            description="Get weather for a location",
            parameters={
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_openai_format([capability])

        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "get_weather"
        assert tools[0]["function"]["description"] == "Get weather for a location"
        assert tools[0]["function"]["parameters"]["type"] == "object"
        assert "location" in tools[0]["function"]["parameters"]["properties"]

    def test_convert_multiple_capabilities_to_openai_format(self) -> None:
        """Test converting multiple capabilities to OpenAI format."""
        schema1 = CapabilitySchema(
            name="tool1",
            description="First tool",
            parameters={"type": "object", "properties": {}},
        )
        schema2 = CapabilitySchema(
            name="tool2",
            description="Second tool",
            parameters={"type": "object", "properties": {}},
        )
        capabilities = [MockCapability(schema1), MockCapability(schema2)]

        tools = ToolTransformer.to_openai_format(capabilities)

        assert len(tools) == 2
        assert tools[0]["function"]["name"] == "tool1"
        assert tools[1]["function"]["name"] == "tool2"

    def test_openai_format_with_empty_parameters(self) -> None:
        """Test OpenAI format with empty parameters."""
        schema = CapabilitySchema(
            name="simple_tool",
            description="A simple tool",
            parameters={},
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_openai_format([capability])

        assert tools[0]["function"]["parameters"]["type"] == "object"
        assert tools[0]["function"]["parameters"]["properties"] == {}

    def test_openai_format_with_complex_parameters(self) -> None:
        """Test OpenAI format with complex parameter definitions."""
        schema = CapabilitySchema(
            name="complex_tool",
            description="Tool with complex parameters",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "metadata": {
                        "type": "object",
                        "properties": {"key": {"type": "string"}},
                    },
                },
                "required": ["name"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_openai_format([capability])

        params = tools[0]["function"]["parameters"]
        assert params["properties"]["age"]["minimum"] == 0
        assert params["properties"]["tags"]["items"]["type"] == "string"
        assert params["required"] == ["name"]


class TestToolTransformerAnthropic:
    """Test Anthropic format conversion."""

    def test_convert_simple_capability_to_anthropic_format(self) -> None:
        """Test converting a simple capability to Anthropic format."""
        schema = CapabilitySchema(
            name="get_weather",
            description="Get weather for a location",
            parameters={
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_anthropic_format([capability])

        assert len(tools) == 1
        assert tools[0]["name"] == "get_weather"
        assert tools[0]["description"] == "Get weather for a location"
        assert tools[0]["input_schema"]["type"] == "object"
        assert "location" in tools[0]["input_schema"]["properties"]

    def test_convert_multiple_capabilities_to_anthropic_format(self) -> None:
        """Test converting multiple capabilities to Anthropic format."""
        schema1 = CapabilitySchema(
            name="tool1",
            description="First tool",
            parameters={"type": "object", "properties": {}},
        )
        schema2 = CapabilitySchema(
            name="tool2",
            description="Second tool",
            parameters={"type": "object", "properties": {}},
        )
        capabilities = [MockCapability(schema1), MockCapability(schema2)]

        tools = ToolTransformer.to_anthropic_format(capabilities)

        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[1]["name"] == "tool2"

    def test_anthropic_format_with_empty_parameters(self) -> None:
        """Test Anthropic format with empty parameters."""
        schema = CapabilitySchema(
            name="simple_tool",
            description="A simple tool",
            parameters={},
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_anthropic_format([capability])

        assert tools[0]["input_schema"]["type"] == "object"
        assert tools[0]["input_schema"]["properties"] == {}

    def test_anthropic_format_with_complex_parameters(self) -> None:
        """Test Anthropic format with complex parameter definitions."""
        schema = CapabilitySchema(
            name="complex_tool",
            description="Tool with complex parameters",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_anthropic_format([capability])

        input_schema = tools[0]["input_schema"]
        assert input_schema["properties"]["age"]["minimum"] == 0
        assert input_schema["properties"]["tags"]["items"]["type"] == "string"
        assert input_schema["required"] == ["name"]


class TestToolTransformerBedrock:
    """Test Bedrock format conversion."""

    def test_convert_simple_capability_to_bedrock_format(self) -> None:
        """Test converting a simple capability to Bedrock format."""
        schema = CapabilitySchema(
            name="get_weather",
            description="Get weather for a location",
            parameters={
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_bedrock_format([capability])

        assert len(tools) == 1
        assert "toolSpec" in tools[0]
        assert tools[0]["toolSpec"]["name"] == "get_weather"
        assert tools[0]["toolSpec"]["description"] == "Get weather for a location"
        assert tools[0]["toolSpec"]["inputSchema"]["json"]["type"] == "object"
        assert "location" in tools[0]["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_convert_multiple_capabilities_to_bedrock_format(self) -> None:
        """Test converting multiple capabilities to Bedrock format."""
        schema1 = CapabilitySchema(
            name="tool1",
            description="First tool",
            parameters={"type": "object", "properties": {}},
        )
        schema2 = CapabilitySchema(
            name="tool2",
            description="Second tool",
            parameters={"type": "object", "properties": {}},
        )
        capabilities = [MockCapability(schema1), MockCapability(schema2)]

        tools = ToolTransformer.to_bedrock_format(capabilities)

        assert len(tools) == 2
        assert tools[0]["toolSpec"]["name"] == "tool1"
        assert tools[1]["toolSpec"]["name"] == "tool2"

    def test_bedrock_format_with_empty_parameters(self) -> None:
        """Test Bedrock format with empty parameters."""
        schema = CapabilitySchema(
            name="simple_tool",
            description="A simple tool",
            parameters={},
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_bedrock_format([capability])

        json_schema = tools[0]["toolSpec"]["inputSchema"]["json"]
        assert json_schema["type"] == "object"
        assert json_schema["properties"] == {}

    def test_bedrock_format_with_complex_parameters(self) -> None:
        """Test Bedrock format with complex parameter definitions."""
        schema = CapabilitySchema(
            name="complex_tool",
            description="Tool with complex parameters",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_bedrock_format([capability])

        json_schema = tools[0]["toolSpec"]["inputSchema"]["json"]
        assert json_schema["properties"]["age"]["minimum"] == 0
        assert json_schema["properties"]["tags"]["items"]["type"] == "string"
        assert json_schema["required"] == ["name"]


class TestToolTransformerAzure:
    """Test Azure format conversion."""

    def test_convert_simple_capability_to_azure_format(self) -> None:
        """Test converting a simple capability to Azure format."""
        schema = CapabilitySchema(
            name="get_weather",
            description="Get weather for a location",
            parameters={
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_azure_format([capability])

        # Azure uses OpenAI format
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "get_weather"
        assert tools[0]["function"]["description"] == "Get weather for a location"

    def test_azure_format_matches_openai_format(self) -> None:
        """Test that Azure format matches OpenAI format."""
        schema = CapabilitySchema(
            name="test_tool",
            description="Test tool",
            parameters={
                "type": "object",
                "properties": {"param": {"type": "string"}},
            },
        )
        capability = MockCapability(schema)

        azure_tools = ToolTransformer.to_azure_format([capability])
        openai_tools = ToolTransformer.to_openai_format([capability])

        assert azure_tools == openai_tools


class TestToolTransformerVertex:
    """Test Vertex AI format conversion."""

    def test_convert_simple_capability_to_vertex_format(self) -> None:
        """Test converting a simple capability to Vertex format."""
        schema = CapabilitySchema(
            name="get_weather",
            description="Get weather for a location",
            parameters={
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_vertex_format([capability])

        assert len(tools) == 1
        assert tools[0]["name"] == "get_weather"
        assert tools[0]["description"] == "Get weather for a location"
        assert tools[0]["parameters"]["type"] == "object"
        assert "location" in tools[0]["parameters"]["properties"]

    def test_convert_multiple_capabilities_to_vertex_format(self) -> None:
        """Test converting multiple capabilities to Vertex format."""
        schema1 = CapabilitySchema(
            name="tool1",
            description="First tool",
            parameters={"type": "object", "properties": {}},
        )
        schema2 = CapabilitySchema(
            name="tool2",
            description="Second tool",
            parameters={"type": "object", "properties": {}},
        )
        capabilities = [MockCapability(schema1), MockCapability(schema2)]

        tools = ToolTransformer.to_vertex_format(capabilities)

        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[1]["name"] == "tool2"

    def test_vertex_format_with_empty_parameters(self) -> None:
        """Test Vertex format with empty parameters."""
        schema = CapabilitySchema(
            name="simple_tool",
            description="A simple tool",
            parameters={},
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_vertex_format([capability])

        assert tools[0]["parameters"]["type"] == "object"
        assert tools[0]["parameters"]["properties"] == {}

    def test_vertex_format_with_complex_parameters(self) -> None:
        """Test Vertex format with complex parameter definitions."""
        schema = CapabilitySchema(
            name="complex_tool",
            description="Tool with complex parameters",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name"],
            },
        )
        capability = MockCapability(schema)

        tools = ToolTransformer.to_vertex_format([capability])

        params = tools[0]["parameters"]
        assert params["properties"]["age"]["minimum"] == 0
        assert params["properties"]["tags"]["items"]["type"] == "string"
        assert params["required"] == ["name"]


class TestToolTransformerEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_capabilities_list(self) -> None:
        """Test converting an empty capabilities list."""
        tools_openai = ToolTransformer.to_openai_format([])
        tools_anthropic = ToolTransformer.to_anthropic_format([])
        tools_bedrock = ToolTransformer.to_bedrock_format([])
        tools_azure = ToolTransformer.to_azure_format([])
        tools_vertex = ToolTransformer.to_vertex_format([])

        assert tools_openai == []
        assert tools_anthropic == []
        assert tools_bedrock == []
        assert tools_azure == []
        assert tools_vertex == []

    def test_capability_with_no_parameters(self) -> None:
        """Test converting capability with no parameters."""
        schema = CapabilitySchema(
            name="no_params_tool",
            description="Tool with no parameters",
        )
        capability = MockCapability(schema)

        openai_tools = ToolTransformer.to_openai_format([capability])
        anthropic_tools = ToolTransformer.to_anthropic_format([capability])
        bedrock_tools = ToolTransformer.to_bedrock_format([capability])
        vertex_tools = ToolTransformer.to_vertex_format([capability])

        # All should have default empty object schema
        assert openai_tools[0]["function"]["parameters"]["type"] == "object"
        assert anthropic_tools[0]["input_schema"]["type"] == "object"
        assert bedrock_tools[0]["toolSpec"]["inputSchema"]["json"]["type"] == "object"
        assert vertex_tools[0]["parameters"]["type"] == "object"

    def test_capability_with_special_characters_in_name(self) -> None:
        """Test converting capability with special characters in name."""
        schema = CapabilitySchema(
            name="tool_with_underscores_123",
            description="Tool with special name",
        )
        capability = MockCapability(schema)

        openai_tools = ToolTransformer.to_openai_format([capability])
        anthropic_tools = ToolTransformer.to_anthropic_format([capability])

        assert openai_tools[0]["function"]["name"] == "tool_with_underscores_123"
        assert anthropic_tools[0]["name"] == "tool_with_underscores_123"

    def test_capability_with_long_description(self) -> None:
        """Test converting capability with long description."""
        long_description = "This is a very long description. " * 20
        schema = CapabilitySchema(
            name="long_desc_tool",
            description=long_description,
        )
        capability = MockCapability(schema)

        openai_tools = ToolTransformer.to_openai_format([capability])
        anthropic_tools = ToolTransformer.to_anthropic_format([capability])

        # Description is trimmed by the schema validator
        expected_description = long_description.strip()
        assert openai_tools[0]["function"]["description"] == expected_description
        assert anthropic_tools[0]["description"] == expected_description

    def test_capability_with_nested_object_parameters(self) -> None:
        """Test converting capability with deeply nested object parameters."""
        schema = CapabilitySchema(
            name="nested_tool",
            description="Tool with nested parameters",
            parameters={
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "profile": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "age": {"type": "integer"},
                                },
                            }
                        },
                    }
                },
            },
        )
        capability = MockCapability(schema)

        openai_tools = ToolTransformer.to_openai_format([capability])
        anthropic_tools = ToolTransformer.to_anthropic_format([capability])

        # Verify nested structure is preserved
        openai_params = openai_tools[0]["function"]["parameters"]
        assert openai_params["properties"]["user"]["properties"]["profile"]["properties"]["name"]["type"] == "string"

        anthropic_params = anthropic_tools[0]["input_schema"]
        assert anthropic_params["properties"]["user"]["properties"]["profile"]["properties"]["age"]["type"] == "integer"

    def test_capability_with_array_of_objects(self) -> None:
        """Test converting capability with array of objects parameters."""
        schema = CapabilitySchema(
            name="array_tool",
            description="Tool with array of objects",
            parameters={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"},
                            },
                        },
                    }
                },
            },
        )
        capability = MockCapability(schema)

        openai_tools = ToolTransformer.to_openai_format([capability])

        items_schema = openai_tools[0]["function"]["parameters"]["properties"]["items"]
        assert items_schema["type"] == "array"
        assert items_schema["items"]["type"] == "object"
        assert "id" in items_schema["items"]["properties"]

    def test_capability_with_enum_values(self) -> None:
        """Test converting capability with enum parameter values."""
        schema = CapabilitySchema(
            name="enum_tool",
            description="Tool with enum parameters",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"],
                    }
                },
            },
        )
        capability = MockCapability(schema)

        openai_tools = ToolTransformer.to_openai_format([capability])

        status_schema = openai_tools[0]["function"]["parameters"]["properties"]["status"]
        assert status_schema["enum"] == ["active", "inactive", "pending"]

    def test_capability_with_multiple_required_fields(self) -> None:
        """Test converting capability with multiple required fields."""
        schema = CapabilitySchema(
            name="multi_required_tool",
            description="Tool with multiple required fields",
            parameters={
                "type": "object",
                "properties": {
                    "field1": {"type": "string"},
                    "field2": {"type": "integer"},
                    "field3": {"type": "boolean"},
                    "field4": {"type": "string"},
                },
                "required": ["field1", "field2", "field3"],
            },
        )
        capability = MockCapability(schema)

        openai_tools = ToolTransformer.to_openai_format([capability])
        anthropic_tools = ToolTransformer.to_anthropic_format([capability])

        assert openai_tools[0]["function"]["parameters"]["required"] == ["field1", "field2", "field3"]
        assert anthropic_tools[0]["input_schema"]["required"] == ["field1", "field2", "field3"]
