"""Capability registry view for ``base``; ``CapabilitySchema`` is defined once, in ``skye.base.interfaces.capability``.

Standard library only. The runtime handlers and registries stay in ``tools``.
"""

from __future__ import annotations

from typing import Any, Protocol

from skye.base.interfaces.capability import CapabilitySchema

__all__ = ["CapabilityRegistryLike", "CapabilitySchema"]


class CapabilityRegistryLike(Protocol):
    """Structural view of a capability registry, so base need not import tools."""

    def get(self, name: str) -> Any: ...
