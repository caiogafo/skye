"""Conversation memory over the memory Port (proposed-interface, guarded).

No concrete memory store ships in ``src`` yet; this example shows the intended Port-level
shape a user implements today. The user-facing entry is a plain ``@dataclass`` that
satisfies ``skye.base.interfaces.memory.MemoryEntryLike`` (NOT pydantic, and the concrete
``MemoryEntry`` model is deliberately not imported). The store subclasses
``MemoryInterface`` and keeps entries in process.

Running this is self-contained and offline: it stores a few conversation turns and
retrieves them by keyword.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from skye.interfaces import MemoryEntryLike, MemoryInterface


@dataclass
class ConversationEntry:
    """A single stored memory, satisfying the ``MemoryEntryLike`` Protocol.

    Attributes:
        id: Unique identifier of the entry.
        content: The text content of the memory.
        memory_type: A free label such as ``"conversation"`` or ``"semantic"``.
        embedding: Optional dense vector, or ``None`` when not embedded.
        metadata: Arbitrary tags (e.g. the speaker's role).
        created_at: When the entry was created.
    """

    id: str
    content: str
    memory_type: str = "conversation"
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InProcessMemory(MemoryInterface):
    """A minimal ``MemoryInterface`` backed by an in-process dict (keyword retrieval)."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntryLike] = {}

    def store(self, entry: MemoryEntryLike) -> str:
        self._entries[entry.id] = entry
        return entry.id

    def retrieve(
        self, query: str, limit: int = 10, filters: dict[str, Any] | None = None
    ) -> list[MemoryEntryLike]:
        needle = query.lower()
        hits = [e for e in self._entries.values() if needle in e.content.lower()]
        if filters:
            hits = [e for e in hits if all(e.metadata.get(k) == v for k, v in filters.items())]
        return hits[:limit]

    def get_by_id(self, entry_id: str) -> MemoryEntryLike | None:
        return self._entries.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None


def main() -> None:
    memory = InProcessMemory()

    turns = [
        ConversationEntry(
            id="t1", content="User asked about the Paris office", metadata={"role": "user"}
        ),
        ConversationEntry(
            id="t2", content="Assistant shared the Paris address", metadata={"role": "assistant"}
        ),
        ConversationEntry(
            id="t3", content="User asked about the Tokyo office", metadata={"role": "user"}
        ),
    ]
    for turn in turns:
        memory.store(turn)
    print(f"stored {len(turns)} conversation turns")

    print("\nretrieve 'Paris':")
    for entry in memory.retrieve("Paris"):
        print(f"  - [{entry.metadata.get('role')}] {entry.content}")

    print("\nretrieve 'office' filtered to role=user:")
    for entry in memory.retrieve("office", filters={"role": "user"}):
        print(f"  - {entry.id}: {entry.content}")

    print("\nget_by_id('t2'):")
    found = memory.get_by_id("t2")
    print(f"  {found.content if found else 'missing'}")

    print(f"\ndelete('t1') -> {memory.delete('t1')}")

    print("\nNote: a concrete memory store is not in src yet; this shows the intended Port shape.")


if __name__ == "__main__":
    main()
