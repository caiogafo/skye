"""Unit tests for MCPServerClient class."""

import sys
from unittest.mock import MagicMock

import pytest

from nimbus.tools.exceptions import CapabilityValidationError
from nimbus.tools.registry import CapabilityRegistry

# Mock fastmcp module globally for all tests
sys.modules["fastmcp"] = MagicMock()


class TestMCPServerClient:
    """Test suite for MCPServerClient class."""

    @pytest.fixture
    def sample_server_config(self):
        """Sample MCP server configuration."""
        return {
            "command": "mcp-server-weather",
            "args": ["--port", "8080"],
            "env": {"API_KEY": "test_key"},
        }

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for testing."""
        registry = CapabilityRegistry()
        yield registry
        registry.clear()

    def test_import_without_fastmcp(self, sample_server_config):
        """Test that importing MCPServerClient without FastMCP raises helpful error."""
        # Temporarily remove fastmcp from sys.modules
        fastmcp_backup = sys.modules.get("fastmcp")
        sys.modules["fastmcp"] = None

        try:
            from nimbus.tools.mcp_server_client import MCPServerClient

            with pytest.raises(ImportError) as exc_info:
                MCPServerClient("test_server", sample_server_config)

            assert "FastMCP is required" in str(exc_info.value)
            assert "pip install nimbus[mcp]" in str(exc_info.value)
        finally:
            # Restore fastmcp
            if fastmcp_backup is not None:
                sys.modules["fastmcp"] = fastmcp_backup
            else:
                sys.modules["fastmcp"] = MagicMock()

    def test_initialization_with_valid_config(self, sample_server_config):
        """Test MCPServerClient initialization with valid configuration."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        assert client.server_name == "test_server"
        assert client._server_config == sample_server_config
        assert client.auto_register is False
        assert client.is_connected() is False

    def test_initialization_with_auto_register(self, sample_server_config, registry):
        """Test initialization with auto-registration enabled."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient(
            "test_server",
            sample_server_config,
            auto_register=True,
            registry=registry,
        )

        assert client.auto_register is True
        assert client._registry is registry

    def test_initialization_with_empty_server_name(self, sample_server_config):
        """Test that initialization fails with empty server name."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        with pytest.raises(CapabilityValidationError) as exc_info:
            MCPServerClient("", sample_server_config)

        assert "Server name cannot be empty" in str(exc_info.value)

    def test_initialization_with_invalid_config_type(self):
        """Test that initialization fails with non-dict config."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        with pytest.raises(CapabilityValidationError) as exc_info:
            MCPServerClient("test_server", "not a dict")

        assert "Server config must be a dictionary" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_context_manager(self, sample_server_config):
        """Test async context manager protocol."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        assert not client.is_connected()

        async with client as ctx_client:
            assert ctx_client is client
            assert client.is_connected()

        assert not client.is_connected()

    @pytest.mark.asyncio
    async def test_connect(self, sample_server_config):
        """Test connection to MCP server."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        assert not client.is_connected()

        await client._connect()

        assert client.is_connected()

        # Calling connect again should be safe
        await client._connect()
        assert client.is_connected()

        await client.close()

    @pytest.mark.asyncio
    async def test_load_tools(self, sample_server_config):
        """Test loading tools from MCP server."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        # Load tools should auto-connect
        tools = await client.load_tools()

        assert isinstance(tools, list)
        assert client.is_connected()

        await client.close()

    @pytest.mark.asyncio
    async def test_load_tools_with_auto_register(self, sample_server_config, registry):
        """Test loading tools with auto-registration."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient(
            "test_server",
            sample_server_config,
            auto_register=True,
            registry=registry,
        )

        tools = await client.load_tools()

        # In the placeholder implementation, no tools are loaded
        # In a real implementation, tools would be registered to the registry
        assert isinstance(tools, list)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_tool(self, sample_server_config):
        """Test retrieving a specific tool by name."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        # Get tool when cache is empty should trigger load_tools
        tool = await client.get_tool("nonexistent_tool")

        assert tool is None  # Tool doesn't exist in placeholder implementation

        await client.close()

    @pytest.mark.asyncio
    async def test_get_tool_from_cache(self, sample_server_config):
        """Test retrieving a tool from cache."""
        from nimbus.tools.mcp_capability import MCPCapability
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        # Manually add a tool to cache for testing
        test_tool = MCPCapability(
            {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {"type": "object", "properties": {}},
            },
            server_name="test_server",
        )
        client._tool_cache["test_tool"] = test_tool

        # Get tool should return from cache
        tool = await client.get_tool("test_tool")

        assert tool is test_tool

        await client.close()

    @pytest.mark.asyncio
    async def test_close(self, sample_server_config):
        """Test closing connection to MCP server."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        await client._connect()
        assert client.is_connected()

        await client.close()
        assert not client.is_connected()

        # Calling close again should be safe
        await client.close()
        assert not client.is_connected()

    def test_is_connected(self, sample_server_config):
        """Test is_connected method."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        assert client.is_connected() is False

    def test_get_cached_tools(self, sample_server_config):
        """Test getting list of cached tool names."""
        from nimbus.tools.mcp_capability import MCPCapability
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        # Initially empty
        assert client.get_cached_tools() == []

        # Add some tools to cache
        tool1 = MCPCapability(
            {
                "name": "tool1",
                "description": "Tool 1",
                "inputSchema": {"type": "object", "properties": {}},
            }
        )
        tool2 = MCPCapability(
            {
                "name": "tool2",
                "description": "Tool 2",
                "inputSchema": {"type": "object", "properties": {}},
            }
        )

        client._tool_cache["tool1"] = tool1
        client._tool_cache["tool2"] = tool2

        cached_tools = client.get_cached_tools()
        assert len(cached_tools) == 2
        assert "tool1" in cached_tools
        assert "tool2" in cached_tools

    def test_clear_cache(self, sample_server_config):
        """Test clearing the tool cache."""
        from nimbus.tools.mcp_capability import MCPCapability
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        # Add a tool to cache
        tool = MCPCapability(
            {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {"type": "object", "properties": {}},
            }
        )
        client._tool_cache["test_tool"] = tool

        assert len(client.get_cached_tools()) == 1

        # Clear cache
        client.clear_cache()

        assert len(client.get_cached_tools()) == 0

    def test_server_name_property(self, sample_server_config):
        """Test server_name property."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        assert client.server_name == "test_server"

    def test_auto_register_property(self, sample_server_config):
        """Test auto_register property."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client_without_auto = MCPServerClient("test_server", sample_server_config)
        assert client_without_auto.auto_register is False

        client_with_auto = MCPServerClient(
            "test_server",
            sample_server_config,
            auto_register=True,
        )
        assert client_with_auto.auto_register is True

    @pytest.mark.asyncio
    async def test_multiple_load_tools_calls(self, sample_server_config):
        """Test that multiple load_tools calls work correctly."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        # First load
        tools1 = await client.load_tools()
        assert isinstance(tools1, list)

        # Second load should also work
        tools2 = await client.load_tools()
        assert isinstance(tools2, list)

        await client.close()

    @pytest.mark.asyncio
    async def test_connection_pooling(self, sample_server_config):
        """Test that connection is reused across operations."""
        from nimbus.tools.mcp_server_client import MCPServerClient

        client = MCPServerClient("test_server", sample_server_config)

        # Connect
        await client._connect()
        assert client.is_connected()

        # Load tools should reuse connection
        await client.load_tools()
        assert client.is_connected()

        # Get tool should reuse connection
        await client.get_tool("test_tool")
        assert client.is_connected()

        await client.close()
        assert not client.is_connected()
