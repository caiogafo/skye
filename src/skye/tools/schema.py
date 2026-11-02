"""Capability schema definitions for Skye.

This module provides the CapabilitySchema model that defines the structure
of capabilities including name, description, parameters, and return type.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CapabilitySchema(BaseModel):
    """Schema definition for a capability.

    Defines the structure of a capability including its name, description,
    parameters, and return type. Uses JSON Schema format for parameters
    and return types to ensure compatibility with LLM function calling.

    Attributes:
        name: Unique identifier for the capability (e.g., "weather.get_current")
        description: Human-readable description of what the capability does
        parameters: JSON Schema defining the input parameters
        returns: JSON Schema defining the return type

    Example:
        >>> schema = CapabilitySchema(
        ...     name="weather.get_current",
        ...     description="Get current weather for a location",
        ...     parameters={
        ...         "type": "object",
        ...         "properties": {
        ...             "location": {"type": "string"}
        ...         },
        ...         "required": ["location"]
        ...     },
        ...     returns={"type": "string"}
        ... )
    """

    model_config = {"frozen": True}

    name: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the capability",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable description of the capability",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema defining input parameters",
    )
    returns: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema defining the return type",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty and contains valid characters."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate that description is not empty."""
        if not v or not v.strip():
            raise ValueError("description cannot be empty or whitespace")
        return v.strip()
