"""Capability support for Skye.

This module provides a unified interface for registering, managing, and invoking
capabilities across different LLM providers. Capabilities can be local Python
functions, remote HTTP APIs, or MCP (Model Context Protocol) server capabilities.

Example:
    >>> from skye.tools import capability, CapabilityInterface, CapabilitySchema
    >>> 
    >>> @capability
    ... def get_weather(location: str) -> str:
    ...     '''Get weather for a location.'''
    ...     return f"Weather for {location}"
    >>> 
    >>> schema = get_weather.get_schema()
    >>> result = get_weather.execute(location="New York")

Codename: updraft.
"""

from skye.tools.decorator import capability
from skye.tools.exceptions import (
    CapabilityError,
    CapabilityExecutionError,
    CapabilityNotFoundError,
    CapabilityValidationError,
    CapabilityCallParsingError,
)
from skye.tools.interface import CapabilityInterface
from skye.tools.local_function import LocalFunctionCapability
from skye.tools.mcp_capability import MCPCapability
from skye.tools.mcp_boundary import MCPPrompt, MCPPromptArgument
from skye.tools.mcp_client import (
    BuiltinMCPClient,
    MCPClientInterface,
    MCPToolCapability,
    create_mcp_client,
)
from skye.tools.mcp_resource import Resource
from skye.tools.mcp_server_client import MCPServerClient
from skye.tools.registry import CapabilityRegistry
from skye.tools.remote_api import RemoteAPICapability
from skye.tools.schema import CapabilitySchema
from skye.tools.capability_call_handler import CapabilityCallHandler
from skye.tools.capability_models import CapabilityCall, CapabilityResult

__all__ = [
    "CapabilityInterface",
    "CapabilitySchema",
    "LocalFunctionCapability",
    "RemoteAPICapability",
    "MCPCapability",
    "MCPServerClient",
    "MCPClientInterface",
    "BuiltinMCPClient",
    "MCPToolCapability",
    "MCPPrompt",
    "MCPPromptArgument",
    "Resource",
    "create_mcp_client",
    "capability",
    "CapabilityRegistry",
    "CapabilityCallHandler",
    "CapabilityCall",
    "CapabilityResult",
    "CapabilityError",
    "CapabilityExecutionError",
    "CapabilityNotFoundError",
    "CapabilityValidationError",
    "CapabilityCallParsingError",
]
