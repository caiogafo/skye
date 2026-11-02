"""Agent runtime and execution engine (optional extra).

This module provides the agent runtime and execution engine for orchestrating
model calls, capabilities, and memory. Available with skyeai[agents].

Component: agents. Layer: runtime (3). Declared-but-minimal; content belongs to the agents spec.
Only the agent-type registry and a ReAct placeholder live here.

Codename: cyclone.
"""

from skye.agents.registry import (
    REACT,
    ReActAgent,
    create_agent,
    get_agent_type,
    list_agent_types,
    register_agent_type,
)

__all__ = [
    "REACT",
    "ReActAgent",
    "create_agent",
    "get_agent_type",
    "list_agent_types",
    "register_agent_type",
]
