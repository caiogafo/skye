"""The one primitive that runs a capability call and says how it ended.

Lives in ``base`` next to the capability Port (``skye.base.interfaces.capability``), so that ``agents``, ``teams`` and ``flows``
use it without importing ``tools``. Standard library only. Every execution path (the response methods, ``CapabilityCall.execute``,
the registry-based paths and an agent loop) delegates here, so they all return the same ``CapabilityMessage``.
The public path is ``skye.completion``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from skye.base.messages import CapabilityMessage, CapabilityStatus

__all__ = ["arun_capability_call", "find_capability", "format_capability_result", "run_capability_call"]


def format_capability_result(result: Any) -> str:
    """Render the value a capability returned as the text of a ``CapabilityMessage``.

    A string is kept as it is; a mapping, list or tuple becomes JSON, and a value JSON cannot hold (a ``datetime``, a ``Decimal``)
    is rendered with ``str`` instead of failing; anything else is ``str(result)``.
    """
    if isinstance(result, str):
        return result
    if isinstance(result, (Mapping, list, tuple)):
        return json.dumps(result, default=str)
    return str(result)


def find_capability(source: Any, name: str) -> Any | None:
    """Find a capability by the name of its schema, in a list of capabilities or in a registry (anything with ``get(name)``)."""
    if source is None:
        return None
    if hasattr(source, "get") and not isinstance(source, (list, tuple)):
        return source.get(name)
    for candidate in source:
        try:
            if candidate.get_schema().name == name:
                return candidate
        except Exception:
            if getattr(candidate, "name", None) == name:
                return candidate
    return None


def _outcome(call_id: str, name: str, content: str, status: CapabilityStatus) -> CapabilityMessage:
    return CapabilityMessage(content=content, capability_id=call_id, capability_name=name, status=status)


def run_capability_call(
    capability: Any | None, call_id: str, name: str, arguments: Mapping[str, Any] | None = None
) -> CapabilityMessage:
    """Run one capability call and say how it ended. It never raises.

    This is the one primitive every execution path uses (the response methods, ``CapabilityCall.execute`` and the agent loop), so
    they all give the same message. The status is ``ok`` when the capability returned, even if the text it returned begins with
    ``"Error:"``; it is ``error`` when the capability is missing or raised. ``registry.execute`` is the one path that raises.

    Args:
        capability: The capability to run, or ``None`` when it was not found.
        call_id: The id of the call, copied to the message.
        name: The name of the capability, copied to the message.
        arguments: The arguments the model chose.

    Returns:
        A ``CapabilityMessage`` with the result as text and the ``status``.
    """
    if capability is None:
        return _outcome(call_id, name, f"Error: Capability '{name}' not found", CapabilityStatus.ERROR)
    try:
        result = capability.execute(**dict(arguments or {}))
        return _outcome(call_id, name, format_capability_result(result), CapabilityStatus.OK)
    except Exception as error:
        return _outcome(call_id, name, f"Error: {error}", CapabilityStatus.ERROR)


async def arun_capability_call(
    capability: Any | None, call_id: str, name: str, arguments: Mapping[str, Any] | None = None
) -> CapabilityMessage:
    """The asynchronous form of ``run_capability_call``: it awaits ``capability.aexecute``. It never raises."""
    if capability is None:
        return _outcome(call_id, name, f"Error: Capability '{name}' not found", CapabilityStatus.ERROR)
    try:
        result = await capability.aexecute(**dict(arguments or {}))
        return _outcome(call_id, name, format_capability_result(result), CapabilityStatus.OK)
    except Exception as error:
        return _outcome(call_id, name, f"Error: {error}", CapabilityStatus.ERROR)
