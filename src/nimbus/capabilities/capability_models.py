"""Capability call and result models for capability execution.

This module provides Pydantic models for representing capability calls from LLMs
and the results of executing those capability calls.
"""

from typing import Any

from pydantic import BaseModel, Field


class CapabilityCall(BaseModel):
    """Represents a capability call request from an LLM.

    When an LLM decides to invoke a capability, it generates a capability call
    containing the capability name and arguments. This model represents
    that request in a provider-agnostic format.

    Attributes:
        id: Unique identifier for this capability call (from the provider)
        name: Name of the capability to invoke
        arguments: Dictionary of arguments to pass to the capability

    Example:
        >>> capability_call = CapabilityCall(
        ...     id="call_123",
        ...     name="weather.get_current",
        ...     arguments={"location": "San Francisco"}
        ... )
    """

    id: str = Field(
        ...,
        description="Unique identifier for this capability call from the provider",
    )
    name: str = Field(
        ...,
        description="Name of the capability to invoke",
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the capability",
    )


class CapabilityResult(BaseModel):
    """Represents the result of executing a capability call.

    After a capability is executed, the result is wrapped in this model
    to be returned to the LLM. It includes the original capability call ID,
    the execution result, and any error information if execution failed.

    Attributes:
        capability_call_id: ID of the capability call this result corresponds to
        name: Name of the capability that was executed
        result: The return value from executing the capability
        error: Error message if execution failed, None if successful

    Example:
        >>> result = CapabilityResult(
        ...     capability_call_id="call_123",
        ...     name="weather.get_current",
        ...     result={"temperature": 72, "condition": "sunny"}
        ... )
        
        >>> error_result = CapabilityResult(
        ...     capability_call_id="call_124",
        ...     name="weather.get_current",
        ...     result=None,
        ...     error="Location not found"
        ... )
    """

    capability_call_id: str = Field(
        ...,
        description="ID of the capability call this result corresponds to",
    )
    name: str = Field(
        ...,
        description="Name of the capability that was executed",
    )
    result: Any = Field(
        default=None,
        description="The return value from executing the capability",
    )
    error: str | None = Field(
        default=None,
        description="Error message if execution failed, None if successful",
    )
