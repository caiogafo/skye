"""Capability call and result models for capability execution.

This module provides Pydantic models for representing capability calls from LLMs
and the results of executing those capability calls.
"""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from nimbus.base.completion import (
    CapabilityCall,
    ExecutableCapabilityCall,
)

if TYPE_CHECKING:
    from nimbus.base.messages import CapabilityMessage

__all__ = [
    "CapabilityCall",
    "ExecutableCapabilityCall",
    "CapabilityResult",
]


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

    def to_message(self) -> "CapabilityMessage":
        """Convert the capability result to a CapabilityMessage for conversation continuation.

        Returns:
            CapabilityMessage containing the result or error.

        Example:
            >>> result = CapabilityResult(
            ...     capability_call_id="call_123",
            ...     name="get_weather",
            ...     result={"temperature": 72, "condition": "sunny"}
            ... )
            >>> msg = result.to_message()
            >>> msg.role
            'capability'
            >>> msg.capability_name
            'get_weather'
        """
        import json

        from nimbus.base.messages import CapabilityMessage

        # Format the content based on whether there's an error
        if self.error:
            content = f"Error: {self.error}"
        else:
            # Convert result to string, handling various types
            if isinstance(self.result, str):
                content = self.result
            elif isinstance(self.result, (dict, list)):
                content = json.dumps(self.result)
            else:
                content = str(self.result)

        return CapabilityMessage(
            content=content, capability_id=self.capability_call_id, capability_name=self.name
        )
