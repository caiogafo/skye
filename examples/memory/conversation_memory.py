"""Conversation memory over the memory Port (proposed-interface, guarded).

No concrete memory store ships in ``src`` yet; this shows the Port-level shape a user implements today. The entry is a plain ``@dataclass``
that satisfies ``MemoryEntryLike``; the store subclasses ``MemoryInterface`` and keeps entries in process. It runs offline: it stores a
few conversation turns and retrieves them by keyword.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from skye.interfaces import MemoryEntryLike, MemoryInterface


@dataclass
class ConversationEntry:
    """A stored memory, satisfying the ``MemoryEntryLike`` Protocol."""

    id: str
    content: str
    memory_type: str = "conversation"
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InProcessMemory(MemoryInterface):
    """A ``MemoryInterface`` backed by a dict (keyword retrieval)."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntryLike] = {}

    def store(self, entry: MemoryEntryLike) -> str:
        self._entries[entry.id] = entry
        return entry.id

    def retrieve(self, query: str, limit: int = 10, filters: dict[str, Any] | None = None) -> list[MemoryEntryLike]:
        hits = [e for e in self._entries.values() if query.lower() in e.content.lower()]
        if filters:
            hits = [e for e in hits if all(e.metadata.get(k) == v for k, v in filters.items())]
        return hits[:limit]

    def get_by_id(self, entry_id: str) -> MemoryEntryLike | None:
        return self._entries.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None


def main() -> None:
    memory = InProcessMemory()
    for id, text, role in [("t1", "User asked about the Paris office", "user"), ("t2", "Assistant shared the Paris address", "assistant"),
                           ("t3", "User asked about the Tokyo office", "user")]:
        memory.store(ConversationEntry(id=id, content=text, metadata={"role": role}))

    print("retrieve 'Paris':")
    for entry in memory.retrieve("Paris"):
        print(f"  - [{entry.metadata['role']}] {entry.content}")
    print("retrieve 'office' with role=user:", [e.id for e in memory.retrieve("office", filters={"role": "user"})])
    print("get_by_id('t2'):", memory.get_by_id("t2").content)
    print("delete('t1'):", memory.delete("t1"))


if __name__ == "__main__":
    main()
