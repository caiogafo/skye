"""Capability interface definitions for Skye.

This module provides the CapabilityInterface abstract base class that all
capability implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any

from skye.tools.schema import CapabilitySchema


class CapabilityInterface(ABC):
    """Abstract base class for all capabilities.

    A capability is a callable function or API that an agent can use to
    perform actions. All capability implementations must inherit from this
    class and implement the required methods.

    Capabilities can be:
    - Local Python functions (LocalFunctionCapability)
    - Remote HTTP APIs (RemoteAPICapability)
    - MCP (Model Context Protocol) server tools (MCPToolCapability)
    - Custom implementations

    Example:
        >>> class MyCapability(CapabilityInterface):
        ...     def get_schema(self) -> CapabilitySchema:
        ...         return CapabilitySchema(
        ...             name="my_capability",
        ...             description="Does something useful",
        ...             parameters={"type": "object", "properties": {}},
        ...             returns={"type": "string"}
        ...         )
        ...
        ...     def execute(self, **kwargs: Any) -> Any:
        ...         return "result"
        ...
        ...     async def aexecute(self, **kwargs: Any) -> Any:
        ...         return "result"
    """

    @abstractmethod
    def get_schema(self) -> CapabilitySchema:
        """Get the schema for this capability.

        Returns the CapabilitySchema that defines the capability's name,
        description, parameters, and return type. This schema is used by
        LLMs to understand how to invoke the capability.

        Returns:
            CapabilitySchema: The schema definition for this capability

        Example:
            >>> capability = MyCapability()
            >>> schema = capability.get_schema()
            >>> print(schema.name)
            "my_capability"
        """
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the capability synchronously.

        Executes the capability with the provided arguments. Arguments
        should match the schema defined in get_schema().

        Args:
            **kwargs: Arguments matching the capability's schema parameters

        Returns:
            The result of executing the capability

        Raises:
            CapabilityExecutionError: If execution fails
            CapabilityValidationError: If arguments don't match schema

        Example:
            >>> capability = MyCapability()
            >>> result = capability.execute(param1="value1")
            >>> print(result)
        """
        pass

    @abstractmethod
    async def aexecute(self, **kwargs: Any) -> Any:
        """Execute the capability asynchronously.

        Asynchronous version of execute(). Executes the capability with
        the provided arguments. Arguments should match the schema defined
        in get_schema().

        Args:
            **kwargs: Arguments matching the capability's schema parameters

        Returns:
            The result of executing the capability

        Raises:
            CapabilityExecutionError: If execution fails
            CapabilityValidationError: If arguments don't match schema

        Example:
            >>> capability = MyCapability()
            >>> result = await capability.aexecute(param1="value1")
            >>> print(result)
        """
        pass
