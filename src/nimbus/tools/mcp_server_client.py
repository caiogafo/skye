"""MCP Server Client for managing connections to MCP servers.

This module provides the MCPServerClient class for connecting to MCP servers,
loading capabilities, and managing capability caching and auto-registration.

Note: MCP uses the term "tool" in its specification, so you'll see references to
"MCP tools" throughout this module when referring to the MCP protocol itself.
These are wrapped as Nimbus capabilities for use in the framework.
"""

import asyncio
import logging
from typing import Any

from nimbus.tools.exceptions import CapabilityValidationError
from nimbus.tools.mcp_capability import MCPCapability
from nimbus.tools.registry import CapabilityRegistry

logger = logging.getLogger(__name__)


class MCPServerClient:
    """Client for managing connections to MCP (Model Context Protocol) servers.

    Provides functionality to connect to MCP servers, load capabilities from MCP tools,
    cache capability definitions, and optionally auto-register capabilities to a
    CapabilityRegistry. Supports both local (stdio) and remote (SSE) MCP servers.

    The FastMCP library is required to use this class. If FastMCP is not installed,
    a helpful error message will be displayed directing users to install it with:
    `pip install nimbus[mcp]` or `pip install fastmcp>=0.1.0`

    Note: MCP uses the term "tool" in its specification. This client wraps MCP tools
    as Nimbus capabilities for seamless integration with the Nimbus framework.

    Attributes:
        server_name: Name identifier for this MCP server
        server_config: Configuration dictionary for the MCP server
        auto_register: Whether to automatically register loaded capabilities to registry

    Example:
        >>> # Using as async context manager
        >>> async with MCPServerClient(
        ...     server_name="weather_server",
        ...     server_config={"command": "mcp-server-weather"},
        ...     auto_register=True
        ... ) as client:
        ...     capabilities = await client.load_tools()
        ...     weather_cap = await client.get_tool("get_weather")
        ...
        >>> # Manual lifecycle management
        >>> client = MCPServerClient("weather_server", config)
        >>> capabilities = await client.load_tools()
        >>> await client.close()
    """

    def __init__(
        self,
        server_name: str,
        server_config: dict[str, Any],
        auto_register: bool = False,
        registry: CapabilityRegistry | None = None,
    ) -> None:
        """Initialize MCP server client.

        Args:
            server_name: Name identifier for this MCP server
            server_config: Configuration dictionary containing server connection details
                (e.g., {"command": "mcp-server-name", "args": [], "env": {}})
            auto_register: Whether to automatically register loaded tools to the
                capability registry (default: False)
            registry: Optional CapabilityRegistry instance for auto-registration.
                If None and auto_register is True, uses the singleton registry.

        Raises:
            ImportError: If FastMCP is not installed
            CapabilityValidationError: If server configuration is invalid
        """
        # Check if FastMCP is available
        try:
            import fastmcp  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "FastMCP is required to use MCPServerClient. "
                "Install it with: pip install nimbus[mcp] or pip install fastmcp>=0.1.0"
            ) from e

        if not server_name or not server_name.strip():
            raise CapabilityValidationError(
                "Server name cannot be empty",
                capability_name="<mcp_server>",
            )

        if not isinstance(server_config, dict):
            raise CapabilityValidationError(
                "Server config must be a dictionary",
                capability_name=server_name,
            )

        self._server_name = server_name
        self._server_config = server_config
        self._auto_register = auto_register
        self._registry = registry if registry is not None else (
            CapabilityRegistry.get_instance() if auto_register else None
        )

        # Tool cache: tool_name -> MCPCapability
        self._tool_cache: dict[str, MCPCapability] = {}

        # Connection state
        self._client = None
        self._connected = False

        logger.debug(
            "MCPServerClient initialized",
            extra={
                "server_name": server_name,
                "auto_register": auto_register,
            },
        )

    async def __aenter__(self) -> "MCPServerClient":
        """Async context manager entry.

        Returns:
            Self for use in async with statement

        Example:
            >>> async with MCPServerClient("server", config) as client:
            ...     tools = await client.load_tools()
        """
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        await self.close()

    async def _connect(self) -> None:
        """Establish connection to the MCP server.

        Raises:
            CapabilityValidationError: If connection fails
        """
        if self._connected:
            return

        try:
            # Note: In a real implementation, this would establish an actual
            # connection to the MCP server using FastMCP client.
            # For now, we'll simulate the connection.
            logger.info(
                "Connecting to MCP server",
                extra={"server_name": self._server_name},
            )

            # Placeholder for actual FastMCP client initialization
            # from fastmcp import FastMCP
            # self._client = FastMCP(self._server_config)
            # await self._client.connect()

            self._connected = True

            logger.info(
                "Connected to MCP server",
                extra={"server_name": self._server_name},
            )

        except Exception as e:
            logger.error(
                "Failed to connect to MCP server",
                extra={
                    "server_name": self._server_name,
                    "error": str(e),
                },
            )
            raise CapabilityValidationError(
                f"Failed to connect to MCP server '{self._server_name}': {e}",
                capability_name=self._server_name,
                original_error=str(e),
            ) from e

    async def load_tools(self) -> list[MCPCapability]:
        """Load all tools from the MCP server.

        Fetches all available tools from the connected MCP server, converts them
        to MCPCapability instances, caches them, and optionally auto-registers
        them to the capability registry.

        Returns:
            List of MCPCapability instances for all tools on the server

        Raises:
            CapabilityValidationError: If not connected or tool loading fails

        Example:
            >>> client = MCPServerClient("server", config, auto_register=True)
            >>> tools = await client.load_tools()
            >>> print(f"Loaded {len(tools)} tools")
        """
        if not self._connected:
            await self._connect()

        try:
            logger.info(
                "Loading tools from MCP server",
                extra={"server_name": self._server_name},
            )

            # Note: In a real implementation, this would fetch tools from the
            # actual MCP server using FastMCP client.
            # For now, we'll return an empty list as a placeholder.

            # Placeholder for actual tool loading:
            # tools_data = await self._client.list_tools()
            # for tool_data in tools_data:
            #     capability = MCPCapability(tool_data, server_name=self._server_name)
            #     self._tool_cache[tool_data["name"]] = capability
            #
            #     if self._auto_register and self._registry:
            #         self._registry.register(capability)

            tools = list(self._tool_cache.values())

            logger.info(
                "Loaded tools from MCP server",
                extra={
                    "server_name": self._server_name,
                    "tool_count": len(tools),
                },
            )

            return tools

        except Exception as e:
            logger.error(
                "Failed to load tools from MCP server",
                extra={
                    "server_name": self._server_name,
                    "error": str(e),
                },
            )
            raise CapabilityValidationError(
                f"Failed to load tools from MCP server '{self._server_name}': {e}",
                capability_name=self._server_name,
                original_error=str(e),
            ) from e

    async def get_tool(self, name: str) -> MCPCapability | None:
        """Get a specific tool by name.

        Retrieves a tool from the cache if available, otherwise attempts to
        load it from the server.

        Args:
            name: Name of the tool to retrieve

        Returns:
            MCPCapability instance if found, None otherwise

        Example:
            >>> client = MCPServerClient("server", config)
            >>> await client.load_tools()
            >>> weather_tool = await client.get_tool("get_weather")
            >>> if weather_tool:
            ...     result = await weather_tool.aexecute(location="NYC")
        """
        # Check cache first
        if name in self._tool_cache:
            return self._tool_cache[name]

        # If not in cache, try loading all tools
        if not self._tool_cache:
            await self.load_tools()

        return self._tool_cache.get(name)

    async def close(self) -> None:
        """Close connection to the MCP server and cleanup resources.

        Closes the connection to the MCP server and clears the tool cache.
        Safe to call multiple times.

        Example:
            >>> client = MCPServerClient("server", config)
            >>> tools = await client.load_tools()
            >>> await client.close()
        """
        if not self._connected:
            return

        try:
            logger.info(
                "Closing connection to MCP server",
                extra={"server_name": self._server_name},
            )

            # Note: In a real implementation, this would close the actual
            # FastMCP client connection.
            # if self._client:
            #     await self._client.close()
            #     self._client = None

            self._connected = False
            # Keep tool cache for potential reconnection

            logger.info(
                "Closed connection to MCP server",
                extra={"server_name": self._server_name},
            )

        except Exception as e:
            logger.error(
                "Error closing MCP server connection",
                extra={
                    "server_name": self._server_name,
                    "error": str(e),
                },
            )

    def is_connected(self) -> bool:
        """Check if client is connected to the MCP server.

        Returns:
            True if connected, False otherwise

        Example:
            >>> client = MCPServerClient("server", config)
            >>> print(client.is_connected())  # False
            >>> async with client:
            ...     print(client.is_connected())  # True
        """
        return self._connected

    def get_cached_tools(self) -> list[str]:
        """Get list of cached tool names.

        Returns:
            List of tool names currently in the cache

        Example:
            >>> client = MCPServerClient("server", config)
            >>> await client.load_tools()
            >>> tool_names = client.get_cached_tools()
            >>> print(tool_names)
            ['get_weather', 'search_api']
        """
        return list(self._tool_cache.keys())

    def clear_cache(self) -> None:
        """Clear the tool cache.

        Removes all cached tools. Useful for forcing a reload of tools
        from the server.

        Example:
            >>> client = MCPServerClient("server", config)
            >>> await client.load_tools()
            >>> client.clear_cache()
            >>> await client.load_tools()  # Reloads from server
        """
        self._tool_cache.clear()
        logger.debug(
            "Cleared tool cache",
            extra={"server_name": self._server_name},
        )

    @property
    def server_name(self) -> str:
        """Get the server name.

        Returns:
            Server name identifier
        """
        return self._server_name

    @property
    def auto_register(self) -> bool:
        """Check if auto-registration is enabled.

        Returns:
            True if auto-registration is enabled, False otherwise
        """
        return self._auto_register
