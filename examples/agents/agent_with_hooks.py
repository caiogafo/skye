"""Inject optional services into an agent (proposed-interface, guarded).

Classification: proposed-interface, guarded. This shows the intended shape for
giving an agent its optional services -- memory, guard (safety) and observe
(telemetry) -- through the real Ports, never by import of a concrete component.
The services below are small local classes that satisfy the real Port contracts
(``MemoryInterface``, ``SafetyFilterInterface``, ``ObserverInterface``).

The agent loop that would consume these services ships with the future agents
spec, so we build and show the wiring, then guard-return before invoking any loop.
"""

import asyncio
from datetime import datetime
from typing import Any

from skye.agents import REACT, create_agent
from skye.base.interfaces.memory import MemoryEntryLike, MemoryInterface
from skye.base.interfaces.observer import EventType, ObserverInterface
from skye.base.interfaces.runnable import Runnable
from skye.base.interfaces.safety import SafetyFilterInterface, SafetyResult


class InMemoryStore(MemoryInterface):
    """Minimal in-process memory satisfying the ``MemoryInterface`` Port."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntryLike] = {}

    def store(self, entry: MemoryEntryLike) -> str:
        self._entries[entry.id] = entry
        return entry.id

    def retrieve(
        self, query: str, limit: int = 10, filters: dict[str, Any] | None = None
    ) -> list[MemoryEntryLike]:
        hits = [e for e in self._entries.values() if query.lower() in e.content.lower()]
        return hits[:limit]

    def get_by_id(self, entry_id: str) -> MemoryEntryLike | None:
        return self._entries.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None


class AllowAllFilter(SafetyFilterInterface):
    """Minimal safety filter satisfying the ``SafetyFilterInterface`` Port."""

    def validate_input(self, content: str) -> SafetyResult:
        return SafetyResult(is_safe=True)

    def validate_output(self, content: str) -> SafetyResult:
        return SafetyResult(is_safe=True)

    def get_policies(self) -> list[str]:
        return ["none"]


class PrintObserver(ObserverInterface):
    """Minimal observer satisfying the ``ObserverInterface`` Port."""

    def log_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        print(f"event: {event_type.value} {data}")

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        print(f"metric: {name}={value}")

    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        return f"trace-{name}"

    def end_trace(self, trace_id: str, metadata: dict[str, Any] | None = None) -> None:
        print(f"trace end: {trace_id}")


async def main() -> None:
    # Build the optional services from the real Ports. A real agent receives these
    # as factory options and talks to each only through its Port.
    memory = InMemoryStore()
    guard = AllowAllFilter()
    observe = PrintObserver()

    # Show the services behave as their Ports promise (no agent loop needed).
    observe.log_event(EventType.AGENT_STEP, {"step": 1})
    print("guard policies:", guard.get_policies())
    print("memory hits for 'x':", memory.retrieve("x"))
    print("built at", datetime.now().year, "- services ready to inject")

    # The intended injection shape: services flow in through factory options.
    agent = create_agent(REACT, memory=memory, guard=guard, observe=observe)
    assert isinstance(agent, Runnable)

    print("Agent constructed with memory/guard/observe wiring.")
    print("The agent loop that consumes these services ships with the future agents spec.")
    # Guard-return before any agent loop: the placeholder's invoke is not implemented.
    return


if __name__ == "__main__":
    asyncio.run(main())
