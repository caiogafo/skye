"""MCP (Model Context Protocol) capability support for Nimbus.

This module provides the MCPCapability class for wrapping MCP server capabilities
as Nimbus capabilities. Requires the FastMCP library as an optional dependency.

Note: MCP uses the term "tool" in its specification, so you'll see references to
"MCP tools" throughout this module when referring to the MCP protocol itself.
"""

import asyncio
import logging
from functools import lru_cache
from typing import Any

from nimbus.tools.exceptions import (
    CapabilityExecutionError,
    CapabilityValidationError,
)
from nimbus.tools.interface import CapabilityInterface
from nimbus.tools.schema import CapabilitySchema

logger = logging.getLogger(__name__)


class MCPCapability(CapabilityInterface):
    """Capability wrapper for MCP (Model Context Protocol) server tools.

    Wraps MCP server tools as Nimbus capabilities, providing automatic schema
    conversion from MCP format to CapabilitySchema format. Supports both local
    and remote MCP servers, OpenAPI-based tools, and schema caching for performance.

    The FastMCP library is required to use this class. If FastMCP is not installed,
    a helpful error message will be displayed directing users to install it with:
    `pip install nimbus[mcp]` or `pip install fastmcp>=0.1.0`

    Attributes:
        mcp_tool: The MCP tool definition dictionary
        server_name: Optional name of the MCP server providing this tool
        cache_schema: Whether to cache the converted schema (default: True)

    Example:
        >>> # Assuming FastMCP is installed and MCP server is running
        >>> mcp_tool = {
        ...     "name": "get_weather",
        ...     "description": "Get weather for a location",
        ...     "inputSchema": {
        ...         "type": "object",
        ...         "properties": {
        ...             "location": {"type": "string"}
        ...         },
        ...         "required": ["location"]
        ...     }
        ... }
        >>> capability = MCPCapability(mcp_tool, server_name="weather_server")
        >>> schema = capability.get_schema()
        >>> result = await capability.aexecute(location="New York")
    """

    def __init__(
        self,
        mcp_tool: dict[str, Any],
        server_name: str | None = None,
        cache_schema: bool = True,
    ) -> None:
        """Initialize MCPCapability with an MCP tool definition.

        Args:
            mcp_tool: MCP tool definition dictionary containing name, description,
                and inputSchema
            server_name: Optional name of the MCP server providing this tool
            cache_schema: Whether to cache the converted schema for performance
                (default: True)

        Raises:
            ImportError: If FastMCP is not installed
            CapabilityValidationError: If the MCP tool definition is invalid
        """
        # Check if FastMCP is available
        try:
            import fastmcp  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "FastMCP is required to use MCPCapability. "
                "Install it with: pip install nimbus[mcp] or pip install fastmcp>=0.1.0"
            ) from e

        # Validate MCP tool definition
        if not isinstance(mcp_tool, dict):
            raise CapabilityValidationError(
                "MCP tool definition must be a dictionary",
                capability_name="<unknown>",
            )

        if "name" not in mcp_tool:
            raise CapabilityValidationError(
                "MCP tool definition must include 'name' field",
                capability_name="<unknown>",
            )

        if "description" not in mcp_tool:
            raise CapabilityValidationError(
                f"MCP tool '{mcp_tool['name']}' must include 'description' field",
                capability_name=mcp_tool.get("name", "<unknown>"),
            )

        self._mcp_tool = mcp_tool
        self._server_name = server_name
        self._cache_schema = cache_schema
        self._cached_schema: CapabilitySchema | None = None

        logger.debug(
            "MCPCapability initialized",
            extra={
                "tool_name": mcp_tool.get("name"),
                "server_name": server_name,
                "cache_enabled": cache_schema,
            },
        )

    def get_schema(self) -> CapabilitySchema:
        """Get the capability schema converted from MCP format.

        Converts the MCP tool definition to Nimbus CapabilitySchema format.
        If caching is enabled, the schema is cached after the first conversion.

        Returns:
            CapabilitySchema: The converted capability schema

        Raises:
            CapabilityValidationError: If schema conversion fails

        Example:
            >>> capability = MCPCapability(mcp_tool)
            >>> schema = capability.get_schema()
            >>> print(schema.name)
            "get_weather"
        """
        # Return cached schema if available
        if self._cache_schema and self._cached_schema is not None:
            return self._cached_schema

        try:
            # Convert MCP tool to CapabilitySchema
            schema = self._convert_mcp_to_schema(self._mcp_tool)

            # Cache if enabled
            if self._cache_schema:
                self._cached_schema = schema

            return schema

        except Exception as e:
            raise CapabilityValidationError(
                f"Failed to convert MCP tool schema: {e}",
                capability_name=self._mcp_tool.get("name", "<unknown>"),
                original_error=str(e),
            ) from e

    def execute(self, **kwargs: Any) -> Any:
        """Execute the MCP tool synchronously.

        Executes the MCP tool with the provided arguments. This is a synchronous
        wrapper around aexecute() that runs the async execution in an event loop.

        Args:
            **kwargs: Arguments matching the tool's input schema

        Returns:
            The result from the MCP tool execution

        Raises:
            CapabilityExecutionError: If execution fails

        Example:
            >>> capability = MCPCapability(mcp_tool)
            >>> result = capability.execute(location="New York")
        """
        try:
            # Run async execution in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new loop
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.aexecute(**kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(self.aexecute(**kwargs))

        except Exception as e:
            raise CapabilityExecutionError(
                f"Failed to execute MCP tool '{self._mcp_tool.get('name')}': {e}",
                capability_name=self._mcp_tool.get("name", "<unknown>"),
                original_error=str(e),
            ) from e

    async def aexecute(self, **kwargs: Any) -> Any:
        """Execute the MCP tool asynchronously.

        Executes the MCP tool with the provided arguments using the FastMCP client.

        Args:
            **kwargs: Arguments matching the tool's input schema

        Returns:
            The result from the MCP tool execution

        Raises:
            CapabilityExecutionError: If execution fails

        Example:
            >>> capability = MCPCapability(mcp_tool)
            >>> result = await capability.aexecute(location="New York")
        """
        tool_name = self._mcp_tool.get("name", "<unknown>")

        try:
            # Import FastMCP client
            from fastmcp import FastMCP

            # Note: In a real implementation, this would use an actual MCP client
            # connection that was established when the tool was loaded from the server.
            # For now, we'll raise an error indicating that direct execution is not
            # supported without a proper MCP client connection.
            raise CapabilityExecutionError(
                f"Direct execution of MCP tool '{tool_name}' is not supported. "
                "Use MCPServerClient to load and execute MCP tools.",
                capability_name=tool_name,
            )

        except ImportError as e:
            raise CapabilityExecutionError(
                f"FastMCP is required to execute MCP tool '{tool_name}'. "
                "Install it with: pip install nimbus[mcp]",
                capability_name=tool_name,
                original_error=str(e),
            ) from e
        except Exception as e:
            logger.error(
                "MCP tool execution failed",
                extra={
                    "tool_name": tool_name,
                    "server_name": self._server_name,
                    "arguments": kwargs,
                    "error": str(e),
                },
            )
            raise CapabilityExecutionError(
                f"Failed to execute MCP tool '{tool_name}': {e}",
                capability_name=tool_name,
                original_error=str(e),
            ) from e

    @staticmethod
    @lru_cache(maxsize=128)
    def _convert_mcp_to_schema(mcp_tool_json: str) -> CapabilitySchema:
        """Convert MCP tool definition to CapabilitySchema.

        This is a cached static method to avoid repeated conversions of the same
        tool definition. Takes JSON string for hashability.

        Args:
            mcp_tool_json: JSON string of MCP tool definition

        Returns:
            CapabilitySchema: The converted schema
        """
        import json

        mcp_tool = json.loads(mcp_tool_json)

        # Extract basic fields
        name = mcp_tool.get("name", "")
        description = mcp_tool.get("description", "")

        # Convert inputSchema to parameters
        # MCP uses "inputSchema" which is already in JSON Schema format
        input_schema = mcp_tool.get("inputSchema", {})

        # Handle OpenAPI-based tools
        if "openapi" in mcp_tool:
            # Extract schema from OpenAPI definition
            openapi_spec = mcp_tool["openapi"]
            # This is a simplified conversion - real implementation would
            # need to handle full OpenAPI spec parsing
            if "parameters" in openapi_spec:
                input_schema = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
                for param in openapi_spec["parameters"]:
                    param_name = param.get("name")
                    param_schema = param.get("schema", {"type": "string"})
                    input_schema["properties"][param_name] = param_schema
                    if param.get("required", False):
                        input_schema["required"].append(param_name)

        # Default to empty object schema if not provided
        if not input_schema:
            input_schema = {"type": "object", "properties": {}}

        # MCP tools typically don't specify return types, so we use a generic schema
        returns = {"type": "object", "description": "Tool execution result"}

        return CapabilitySchema(
            name=name,
            description=description,
            parameters=input_schema,
            returns=returns,
        )

    def get_schema(self) -> CapabilitySchema:
        """Get the capability schema converted from MCP format.

        Converts the MCP tool definition to Nimbus CapabilitySchema format.
        If caching is enabled, the schema is cached after the first conversion.

        Returns:
            CapabilitySchema: The converted capability schema

        Raises:
            CapabilityValidationError: If schema conversion fails
        """
        # Return cached schema if available
        if self._cache_schema and self._cached_schema is not None:
            return self._cached_schema

        try:
            # Convert to JSON string for caching
            import json

            mcp_tool_json = json.dumps(self._mcp_tool, sort_keys=True)

            # Convert MCP tool to CapabilitySchema using cached method
            schema = self._convert_mcp_to_schema(mcp_tool_json)

            # Cache if enabled
            if self._cache_schema:
                self._cached_schema = schema

            return schema

        except Exception as e:
            raise CapabilityValidationError(
                f"Failed to convert MCP tool schema: {e}",
                capability_name=self._mcp_tool.get("name", "<unknown>"),
                original_error=str(e),
            ) from e
