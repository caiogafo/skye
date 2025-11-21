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


class ExecutableCapabilityCall(BaseModel):
    """A capability call that can execute itself.

    This wraps a CapabilityCall with a reference to the actual capability
    implementation, allowing direct execution.

    Attributes:
        id: Unique identifier for this capability call
        name: Name of the capability to invoke
        arguments: Dictionary of arguments to pass to the capability
        capability: The actual capability implementation (optional)

    Example:
        >>> executable_call = ExecutableCapabilityCall(
        ...     id="call_123",
        ...     name="get_weather",
        ...     arguments={"location": "San Francisco"},
        ...     capability=weather_capability
        ... )
        >>> message = executable_call.execute()
        >>> message.role
        'capability'
    """

    model_config = {"arbitrary_types_allowed": True}

    id: str = Field(
        ...,
        description="Unique identifier for this capability call",
    )
    name: str = Field(
        ...,
        description="Name of the capability to invoke",
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the capability",
    )
    capability: Any | None = Field(
        default=None,
        description="The actual capability implementation",
    )

    def execute(self, **override_arguments: Any) -> "CapabilityMessage":
        """Execute the capability and return a CapabilityMessage.

        Args:
            **override_arguments: Optional arguments to override the LLM-provided arguments.
                If provided, these will be merged with (and take precedence over) the
                arguments from the LLM.

        Returns:
            CapabilityMessage containing the execution result.

        Raises:
            ValueError: If no capability is available to execute.

        Example:
            >>> # Use LLM-provided arguments
            >>> message = executable_call.execute()
            >>> print(message.content)
            '{"temperature": 72, "condition": "sunny"}'
            >>>
            >>> # Override specific arguments
            >>> message = executable_call.execute(location="New York")
            >>> print(message.content)
            '{"temperature": 65, "condition": "cloudy"}'
        """
        from nimbus.messages import CapabilityMessage
        import json

        if self.capability is None:
            return CapabilityMessage(
                content=f"Error: Capability '{self.name}' not found",
                capability_id=self.id,
                capability_name=self.name
            )

        try:
            # Merge LLM arguments with overrides (overrides take precedence)
            final_arguments = {**self.arguments, **override_arguments}

            # Execute the capability
            result = self.capability.execute(**final_arguments)

            # Format result as string
            if isinstance(result, str):
                content = result
            elif isinstance(result, (dict, list)):
                content = json.dumps(result)
            else:
                content = str(result)

            return CapabilityMessage(
                content=content,
                capability_id=self.id,
                capability_name=self.name
            )

        except Exception as e:
            return CapabilityMessage(
                content=f"Error: {str(e)}",
                capability_id=self.id,
                capability_name=self.name
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
        from nimbus.messages import CapabilityMessage
        import json

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
            content=content,
            capability_id=self.capability_call_id,
            capability_name=self.name
        )
