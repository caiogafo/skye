"""Capability support for Nimbus.

This module provides a unified interface for registering, managing, and invoking
capabilities across different LLM providers. Capabilities can be local Python
functions, remote HTTP APIs, or MCP (Model Context Protocol) server capabilities.

Example:
    >>> from nimbus.tools import capability, CapabilityInterface, CapabilitySchema
    >>> 
    >>> @capability
    ... def get_weather(location: str) -> str:
    ...     '''Get weather for a location.'''
    ...     return f"Weather for {location}"
    >>> 
    >>> schema = get_weather.get_schema()
    >>> result = get_weather.execute(location="New York")
"""

from nimbus.tools.decorator import capability
from nimbus.tools.exceptions import (
    CapabilityError,
    CapabilityExecutionError,
    CapabilityNotFoundError,
    CapabilityValidationError,
    CapabilityCallParsingError,
)
from nimbus.tools.interface import CapabilityInterface
from nimbus.tools.local_function import LocalFunctionCapability
from nimbus.tools.mcp_capability import MCPCapability
from nimbus.tools.mcp_server_client import MCPServerClient
from nimbus.tools.registry import CapabilityRegistry
from nimbus.tools.remote_api import RemoteAPICapability
from nimbus.tools.schema import CapabilitySchema
from nimbus.tools.capability_call_handler import CapabilityCallHandler
from nimbus.tools.capability_models import CapabilityCall, CapabilityResult

__all__ = [
    "CapabilityInterface",
    "CapabilitySchema",
    "LocalFunctionCapability",
    "RemoteAPICapability",
    "MCPCapability",
    "MCPServerClient",
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
