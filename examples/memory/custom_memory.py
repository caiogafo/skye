"""Custom memory store: the extension point of the memory Port (proposed-interface, guarded).

The planned memory API is a Port, ``skye.base.interfaces.memory.MemoryInterface``; no
concrete store ships in ``src`` yet. This example focuses on the extension point: a user
subclass of ``MemoryInterface`` with its own retrieval strategy, exercised end to end. The
user-facing entry shape is a plain ``@dataclass`` satisfying ``MemoryEntryLike`` (NOT
pydantic; the concrete ``MemoryEntry`` model is not imported).

Everything here runs offline with no provider.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from skye.interfaces import MemoryEntryLike, MemoryInterface


@dataclass
class Note:
    """A user-defined memory entry satisfying the ``MemoryEntryLike`` Protocol."""

    id: str
    content: str
    memory_type: str = "semantic"
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class KeywordMemory(MemoryInterface):
    """A custom store that ranks entries by how many query keywords they contain."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntryLike] = {}

    def store(self, entry: MemoryEntryLike) -> str:
        self._entries[entry.id] = entry
        return entry.id

    def retrieve(
        self, query: str, limit: int = 10, filters: dict[str, Any] | None = None
    ) -> list[MemoryEntryLike]:
        keywords = {w.lower() for w in query.split()}

        def score(entry: MemoryEntryLike) -> int:
            words = {w.lower() for w in entry.content.split()}
            return len(keywords & words)

        ranked = sorted(self._entries.values(), key=score, reverse=True)
        return [e for e in ranked if score(e) > 0][:limit]

    def get_by_id(self, entry_id: str) -> MemoryEntryLike | None:
        return self._entries.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None


def main() -> None:
    memory = KeywordMemory()
    memory.store(Note(id="n1", content="The Paris office opens at nine"))
    memory.store(Note(id="n2", content="The Tokyo office closes at six"))
    memory.store(Note(id="n3", content="Paris and Tokyo share a calendar"))

    print("retrieve 'Paris office' ranked by keyword overlap:")
    for entry in memory.retrieve("Paris office"):
        print(f"  - {entry.id}: {entry.content}")

    print(f"\nget_by_id('n2') -> {memory.get_by_id('n2').content}")
    print(f"delete('n3') -> {memory.delete('n3')}")

    print("\nNote: the concrete memory API ships with a future spec; this is the Port shape.")


if __name__ == "__main__":
    main()
