"""Capability schema definitions for Skye.

This module provides the CapabilitySchema model that defines the structure
of capabilities including name, description, parameters, and return type.
"""

import dataclasses
from typing import Any

from skye.base.exceptions import ValidationError
from skye.base.validated import Validated, field, validated


@validated(frozen=True)
class CapabilitySchema(Validated):
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

    name: str = field(
        min_length=1,
        description="Unique identifier for the capability",
    )
    description: str = field(
        min_length=1,
        description="Human-readable description of the capability",
    )
    parameters: dict[str, Any] = field(
        default_factory=dict,
        description="JSON Schema defining input parameters",
    )
    returns: dict[str, Any] = field(
        default_factory=dict,
        description="JSON Schema defining the return type",
    )

    def __post_init__(self) -> None:
        """Validate the fields, then strip the name and the description, which must not be blank."""
        try:
            super().__post_init__()
        except dataclasses.FrozenInstanceError as error:
            raise ValidationError(
                "parameters and returns must be dicts with string keys",
                field="parameters",
                value=None,
            ) from error
        for field_name in ("name", "description"):
            value = getattr(self, field_name)
            if not value.strip():
                raise ValidationError(
                    f"{field_name} cannot be empty or whitespace", field=field_name, value=value
                )
            object.__setattr__(self, field_name, value.strip())
