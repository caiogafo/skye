"""Agents registry: the single extension point for agent types.

An agent type is a factory (usually a class) that produces a ``Runnable``. Types
are registered by name; user code can register its own through ``register_agent_type``.

Standard library plus ``skye.base`` only. This module does not import ``models``
or any other orchestrator; concrete agent types arrive with the future ``agents`` spec.
"""

from collections.abc import Callable
from typing import Any

from skye.base.exceptions import ConfigurationError
from skye.base.interfaces.runnable import Runnable

AgentFactory = Callable[..., Runnable[Any, Any]]

REACT = "react"

_REGISTRY: dict[str, AgentFactory] = {}


class ReActAgent:
    """Placeholder for the ReAct agent type (stub, no agent loop).

    Satisfies the ``Runnable`` Port so the boundary is in place. The real
    implementation is deferred to the future ``agents`` spec.
    """

    def __init__(self, **options: Any) -> None:
        self.options = options

    async def invoke(self, input: Any) -> Any:
        """Not implemented: the ReAct loop belongs to the future agents spec."""
        raise NotImplementedError(
            "ReActAgent is a placeholder; the agent loop is not implemented yet"
        )

    async def ainvoke(self, input: Any) -> Any:
        """A thin alias of :meth:`invoke`."""
        return await self.invoke(input)


def register_agent_type(name: str, factory: AgentFactory, *, replace: bool = False) -> None:
    """Register an agent type under ``name``.

    Raises:
        ConfigurationError: if ``name`` is already registered and ``replace`` is False.
    """
    if not name or not isinstance(name, str):
        raise ConfigurationError(
            "Agent type name must be a non-empty string", details={"name": name}
        )
    if name in _REGISTRY and not replace:
        raise ConfigurationError(f"Agent type already registered: {name!r}", details={"name": name})
    _REGISTRY[name] = factory


def get_agent_type(name: str) -> AgentFactory:
    """Return the factory registered under ``name``.

    Raises:
        ConfigurationError: if ``name`` is not registered.
    """
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ConfigurationError(
            f"Unknown agent type: {name!r}", details={"name": name, "available": sorted(_REGISTRY)}
        ) from None


def create_agent(name: str, **options: Any) -> Runnable[Any, Any]:
    """Instantiate the agent type registered under ``name``."""
    return get_agent_type(name)(**options)


def list_agent_types() -> list[str]:
    """Return the registered agent type names, sorted."""
    return sorted(_REGISTRY)


register_agent_type(REACT, ReActAgent)

__all__ = [
    "REACT",
    "AgentFactory",
    "ReActAgent",
    "create_agent",
    "get_agent_type",
    "list_agent_types",
    "register_agent_type",
]
