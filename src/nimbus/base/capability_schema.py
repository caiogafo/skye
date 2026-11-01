"""Pure capability schema contract (name, description, parameter schema).

Standard library only. This is the contract ``base`` shares with the tools
Component: runtime handlers, registries and Pydantic runtime models stay in
``tools``. Mirrors the shape of
``nimbus.tools.schema.CapabilitySchema``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class CapabilitySchema:
    """Immutable description of a capability.

    Attributes:
        name: Unique identifier (e.g. "weather.get_current").
        description: Human-readable description.
        parameters: JSON Schema for the input parameters.
        returns: JSON Schema for the return type.
    """

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    returns: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for attr in ("name", "description"):
            value = getattr(self, attr)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{attr} cannot be empty or whitespace")
            object.__setattr__(self, attr, value.strip())


class CapabilityRegistryLike(Protocol):
    """Structural view of a capability registry, so base need not import tools."""

    def get(self, name: str) -> Any: ...
