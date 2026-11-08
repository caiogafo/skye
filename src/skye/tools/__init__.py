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

from skye.tools.capability_call_handler import CapabilityCallHandler
from skye.tools.capability_models import CapabilityCall, CapabilityResult
from skye.tools.decorator import capability
from skye.tools.exceptions import (
    CapabilityCallParsingError,
    CapabilityError,
    CapabilityExecutionError,
    CapabilityNotFoundError,
    CapabilityValidationError,
)
from skye.tools.interface import CapabilityInterface
from skye.tools.local_function import LocalFunctionCapability
from skye.tools.mcp_boundary import MCPPrompt, MCPPromptArgument
from skye.tools.mcp_client import (
    BuiltinMCPClient,
    MCPClientInterface,
    MCPToolCapability,
    create_mcp_client,
)
from skye.tools.mcp_resource import Resource, ResourceProviderInterface
from skye.tools.registry import CapabilityRegistry
from skye.tools.remote_api import RemoteAPICapability
from skye.tools.schema import CapabilitySchema

__all__ = [
    "CapabilityInterface",
    "CapabilitySchema",
    "LocalFunctionCapability",
    "RemoteAPICapability",
    "MCPClientInterface",
    "BuiltinMCPClient",
    "MCPToolCapability",
    "MCPPrompt",
    "MCPPromptArgument",
    "Resource",
    "ResourceProviderInterface",
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
