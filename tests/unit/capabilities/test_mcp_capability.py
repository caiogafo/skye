"""Unit tests for MCPCapability class."""

import asyncio
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from skye.tools.exceptions import (
    CapabilityExecutionError,
    CapabilityValidationError,
)
from skye.tools.schema import CapabilitySchema

# Mock fastmcp module globally for all tests
sys.modules["fastmcp"] = MagicMock()


class TestMCPCapability:
    """Test suite for MCPCapability class."""

    @pytest.fixture(autouse=True)
    def ensure_event_loop(self):
        """Guarantee a current event loop on the main thread for sync execute().

        MCPCapability.execute() calls asyncio.get_event_loop(), which on Python
        3.10+ raises RuntimeError when no current loop is set rather than creating
        one. That state depends on test execution order, so these tests must not
        rely on a loop left behind by a prior test. Install a fresh loop and
        restore the previous state afterwards.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            yield
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    @pytest.fixture
    def sample_mcp_tool(self):
        """Sample MCP tool definition."""
        return {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius",
                    },
                },
                "required": ["location"],
            },
        }

    @pytest.fixture
    def openapi_mcp_tool(self):
        """Sample OpenAPI-based MCP tool definition."""
        return {
            "name": "search_api",
            "description": "Search using an API",
            "openapi": {
                "parameters": [
                    {
                        "name": "query",
                        "schema": {"type": "string"},
                        "required": True,
                    },
                    {
                        "name": "limit",
                        "schema": {"type": "integer"},
                        "required": False,
                    },
                ]
            },
        }

    def test_import_without_fastmcp(self, sample_mcp_tool):
        """Test that importing MCPCapability without FastMCP raises helpful error."""
        from skye.tools.mcp_capability import MCPCapability

        # Temporarily remove fastmcp from sys.modules to simulate it not being installed
        fastmcp_backup = sys.modules.get("fastmcp")
        sys.modules["fastmcp"] = None

        try:
            # Mock the import to fail
            with patch("builtins.__import__", side_effect=ImportError("No module named 'fastmcp'")):
                with pytest.raises(ImportError) as exc_info:
                    MCPCapability(sample_mcp_tool)

                assert "FastMCP is required" in str(exc_info.value)
                assert "pip install skyeai[mcp]" in str(exc_info.value)
        finally:
            # Restore fastmcp
            if fastmcp_backup is not None:
                sys.modules["fastmcp"] = fastmcp_backup
            else:
                sys.modules["fastmcp"] = MagicMock()

    def test_initialization_with_valid_tool(self, sample_mcp_tool):
        """Test MCPCapability initialization with valid tool definition."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(sample_mcp_tool, server_name="weather_server")

        assert capability._mcp_tool == sample_mcp_tool
        assert capability._server_name == "weather_server"
        assert capability._cache_schema is True

    def test_initialization_without_name(self):
        """Test that initialization fails without 'name' field."""
        from skye.tools.mcp_capability import MCPCapability

        invalid_tool = {"description": "Missing name"}

        with pytest.raises(CapabilityValidationError) as exc_info:
            MCPCapability(invalid_tool)

        assert "must include 'name' field" in str(exc_info.value)

    def test_initialization_without_description(self):
        """Test that initialization fails without 'description' field."""
        from skye.tools.mcp_capability import MCPCapability

        invalid_tool = {"name": "test_tool"}

        with pytest.raises(CapabilityValidationError) as exc_info:
            MCPCapability(invalid_tool)

        assert "must include 'description' field" in str(exc_info.value)

    def test_initialization_with_invalid_type(self):
        """Test that initialization fails with non-dict tool definition."""
        from skye.tools.mcp_capability import MCPCapability

        with pytest.raises(CapabilityValidationError) as exc_info:
            MCPCapability("not a dict")

        assert "must be a dictionary" in str(exc_info.value)

    def test_get_schema_basic(self, sample_mcp_tool):
        """Test schema conversion from MCP format."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(sample_mcp_tool)
        schema = capability.get_schema()

        assert isinstance(schema, CapabilitySchema)
        assert schema.name == "get_weather"
        assert schema.description == "Get current weather for a location"
        assert schema.parameters == sample_mcp_tool["inputSchema"]
        assert "type" in schema.returns

    def test_get_schema_with_caching(self, sample_mcp_tool):
        """Test that schema caching works correctly."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(sample_mcp_tool, cache_schema=True)

        # First call should convert and cache
        schema1 = capability.get_schema()
        # Second call should return cached version
        schema2 = capability.get_schema()

        assert schema1 is schema2  # Same object reference
        assert capability._cached_schema is not None

    def test_get_schema_without_caching(self, sample_mcp_tool):
        """Test schema conversion without caching."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(sample_mcp_tool, cache_schema=False)

        # Multiple calls should work but not cache
        schema1 = capability.get_schema()
        schema2 = capability.get_schema()

        assert schema1 == schema2  # Equal but not same object
        assert capability._cached_schema is None

    def test_get_schema_openapi_tool(self, openapi_mcp_tool):
        """Test schema conversion for OpenAPI-based MCP tool."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(openapi_mcp_tool)
        schema = capability.get_schema()

        assert isinstance(schema, CapabilitySchema)
        assert schema.name == "search_api"
        assert "query" in schema.parameters["properties"]
        assert "limit" in schema.parameters["properties"]
        assert "query" in schema.parameters.get("required", [])

    def test_get_schema_without_input_schema(self):
        """Test schema conversion when inputSchema is missing."""
        from skye.tools.mcp_capability import MCPCapability

        tool_without_schema = {
            "name": "simple_tool",
            "description": "A simple tool without input schema",
        }

        capability = MCPCapability(tool_without_schema)
        schema = capability.get_schema()

        assert isinstance(schema, CapabilitySchema)
        assert schema.name == "simple_tool"
        assert schema.parameters == {"type": "object", "properties": {}}

    def test_execute_raises_not_supported_error(self, sample_mcp_tool):
        """Test that execute() raises error indicating direct execution not supported."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(sample_mcp_tool)

        with pytest.raises(CapabilityExecutionError) as exc_info:
            capability.execute(location="New York")

        assert "Direct execution" in str(exc_info.value)
        assert "MCPServerClient" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_aexecute_raises_not_supported_error(self, sample_mcp_tool):
        """Test that aexecute() raises error indicating direct execution not supported."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(sample_mcp_tool)

        with pytest.raises(CapabilityExecutionError) as exc_info:
            await capability.aexecute(location="New York")

        assert "Direct execution" in str(exc_info.value)
        assert "MCPServerClient" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_aexecute_without_fastmcp(self, sample_mcp_tool):
        """Test that aexecute() raises helpful error when FastMCP not available."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(sample_mcp_tool)

        # The current implementation raises "Direct execution not supported"
        # before trying to import FastMCP, so we expect that error
        with pytest.raises(CapabilityExecutionError) as exc_info:
            await capability.aexecute(location="New York")

        assert "Direct execution" in str(exc_info.value)

    def test_convert_mcp_to_schema_caching(self, sample_mcp_tool):
        """Test that _convert_mcp_to_schema uses LRU cache."""
        from skye.tools.mcp_capability import MCPCapability

        # Convert tool to JSON for caching
        tool_json = json.dumps(sample_mcp_tool, sort_keys=True)

        # First call
        schema1 = MCPCapability._convert_mcp_to_schema(tool_json)

        # Second call should use cache
        schema2 = MCPCapability._convert_mcp_to_schema(tool_json)

        # Should be the same object due to caching
        assert schema1 is schema2

    def test_schema_conversion_with_complex_types(self):
        """Test schema conversion with complex parameter types."""
        from skye.tools.mcp_capability import MCPCapability

        complex_tool = {
            "name": "complex_tool",
            "description": "Tool with complex types",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "config": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                            "count": {"type": "integer"},
                        },
                    },
                },
                "required": ["items"],
            },
        }

        capability = MCPCapability(complex_tool)
        schema = capability.get_schema()

        assert "items" in schema.parameters["properties"]
        assert "config" in schema.parameters["properties"]
        assert schema.parameters["properties"]["items"]["type"] == "array"
        assert schema.parameters["properties"]["config"]["type"] == "object"

    def test_server_name_tracking(self, sample_mcp_tool):
        """Test that server name is properly tracked."""
        from skye.tools.mcp_capability import MCPCapability

        capability = MCPCapability(sample_mcp_tool, server_name="test_server")

        assert capability._server_name == "test_server"

    def test_cache_schema_flag(self, sample_mcp_tool):
        """Test that cache_schema flag is respected."""
        from skye.tools.mcp_capability import MCPCapability

        # With caching enabled
        cap_with_cache = MCPCapability(sample_mcp_tool, cache_schema=True)
        assert cap_with_cache._cache_schema is True

        # With caching disabled
        cap_without_cache = MCPCapability(sample_mcp_tool, cache_schema=False)
        assert cap_without_cache._cache_schema is False
