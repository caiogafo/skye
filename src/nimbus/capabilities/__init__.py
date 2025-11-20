"""Capability support for Nimbus.

This module provides a unified interface for registering, managing, and invoking
tools/functions across different LLM providers. Capabilities can be local Python
functions, remote HTTP APIs, or MCP (Model Context Protocol) server tools.

Example:
    >>> from nimbus.capabilities import capability, CapabilityInterface, CapabilitySchema
    >>> 
    >>> @capability
    ... def get_weather(location: str) -> str:
    ...     '''Get weather for a location.'''
    ...     return f"Weather for {location}"
    >>> 
    >>> schema = get_weather.get_schema()
    >>> result = get_weather.execute(location="New York")
"""

from nimbus.capabilities.decorator import capability
from nimbus.capabilities.exceptions import (
    CapabilityError,
    CapabilityExecutionError,
    CapabilityNotFoundError,
    CapabilityValidationError,
    ToolCallParsingError,
)
from nimbus.capabilities.interface import CapabilityInterface
from nimbus.capabilities.local_function import LocalFunctionCapability
from nimbus.capabilities.mcp_capability import MCPCapability
from nimbus.capabilities.mcp_server_client import MCPServerClient
from nimbus.capabilities.registry import CapabilityRegistry
from nimbus.capabilities.remote_api import RemoteAPICapability
from nimbus.capabilities.schema import CapabilitySchema
from nimbus.capabilities.tool_call_handler import ToolCallHandler
from nimbus.capabilities.tool_models import ToolCall, ToolResult
from nimbus.capabilities.tool_transformer import ToolTransformer

__all__ = [
    "CapabilityInterface",
    "CapabilitySchema",
    "LocalFunctionCapability",
    "RemoteAPICapability",
    "MCPCapability",
    "MCPServerClient",
    "capability",
    "CapabilityRegistry",
    "ToolTransformer",
    "ToolCallHandler",
    "ToolCall",
    "ToolResult",
    "CapabilityError",
    "CapabilityExecutionError",
    "CapabilityNotFoundError",
    "CapabilityValidationError",
    "ToolCallParsingError",
]
