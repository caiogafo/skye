"""Capability interface for capabilities and functions.

This module defines the abstract interface for capabilities (functions)
that agents can invoke. It includes schema definition for LLM function calling.

Example:
    >>> from nimbus.interfaces.capability import CapabilityInterface, CapabilitySchema
    >>>
    >>> class WeatherCapability(CapabilityInterface):
    ...     def get_schema(self) -> CapabilitySchema:
    ...         return CapabilitySchema(
    ...             name="get_weather",
    ...             description="Get current weather for a city",
    ...             parameters={"city": {"type": "string"}},
    ...             returns={"type": "object"}
    ...         )
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class CapabilitySchema(BaseModel):
    """Schema defining a capability's signature.

    This model describes the capability's interface for LLM function calling,
    including its name, description, parameters, and return type.

    Attributes:
        name: Unique name of the capability.
        description: Human-readable description of what the capability does.
        parameters: JSON Schema describing the capability's parameters.
        returns: JSON Schema describing the capability's return value.

    Example:
        >>> schema = CapabilitySchema(
        ...     name="calculate",
        ...     description="Perform arithmetic calculation",
        ...     parameters={
        ...         "type": "object",
        ...         "properties": {
        ...             "operation": {"type": "string", "enum": ["add", "subtract"]},
        ...             "a": {"type": "number"},
        ...             "b": {"type": "number"}
        ...         },
        ...         "required": ["operation", "a", "b"]
        ...     },
        ...     returns={"type": "number"}
        ... )
        >>> schema.name
        'calculate'
    """

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    returns: dict[str, Any] = Field(default_factory=dict)


class CapabilityInterface(ABC):
    """Abstract interface for agent capabilities.

    This interface defines the contract for executable capabilities that extend
    agent functionality. Capabilities can be synchronous or asynchronous and
    provide schema information for LLM function calling.

    Example:
        >>> class CalculatorCapability(CapabilityInterface):
        ...     def get_schema(self) -> CapabilitySchema:
        ...         return CapabilitySchema(
        ...             name="calculator",
        ...             description="Perform calculations",
        ...             parameters={"expression": {"type": "string"}},
        ...             returns={"type": "number"}
        ...         )
        ...
        ...     def execute(self, **kwargs) -> Any:
        ...         expression = kwargs.get("expression", "")
        ...         return eval(expression)  # Note: eval is unsafe, just for example
        ...
        ...     async def aexecute(self, **kwargs) -> Any:
        ...         return self.execute(**kwargs)
    """

    @abstractmethod
    def get_schema(self) -> CapabilitySchema:
        """Return the capability's schema for LLM function calling.

        Returns:
            CapabilitySchema describing the capability's interface.

        Example:
            >>> capability = MyCapability()
            >>> schema = capability.get_schema()
            >>> schema.name
            'my_capability'
        """
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the capability with provided arguments.

        Args:
            **kwargs: Keyword arguments matching the capability's parameter schema.

        Returns:
            The result of executing the capability.

        Raises:
            CapabilityExecutionError: If execution fails.
            ValidationError: If arguments don't match the schema.

        Example:
            >>> capability = MyCapability()
            >>> result = capability.execute(param1="value1", param2=42)
            >>> print(result)
        """
        pass

    @abstractmethod
    async def aexecute(self, **kwargs: Any) -> Any:
        """Execute the capability asynchronously.

        Args:
            **kwargs: Keyword arguments matching the capability's parameter schema.

        Returns:
            The result of executing the capability.

        Raises:
            CapabilityExecutionError: If execution fails.
            ValidationError: If arguments don't match the schema.

        Example:
            >>> capability = MyCapability()
            >>> result = await capability.aexecute(param1="value1", param2=42)
            >>> print(result)
        """
        pass
