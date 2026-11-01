"""Memory interface for persistent storage.

This module defines the abstract interface for memory storage and retrieval.
It enables agents to store and recall information across sessions.

Example:
    >>> from nimbus.base.interfaces.memory import MemoryInterface
    >>>
    >>> class MyMemory(MemoryInterface):
    ...     def store(self, entry: MemoryEntryLike) -> str:
    ...         # Implementation here
    ...         pass
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Protocol


class MemoryEntryLike(Protocol):
    """Structural shape of a memory entry, as seen by the memory Port.

    The concrete pydantic ``MemoryEntry`` model stays in the ``memory`` Component
    and satisfies this Protocol; the Port needs no import from that Component.
    """

    id: str
    content: str
    memory_type: str
    embedding: list[float] | None
    metadata: dict[str, Any]
    created_at: datetime


class MemoryInterface(ABC):
    """Abstract interface for memory storage.

    This interface defines the contract for persistent memory implementations.
    It supports storing, retrieving, and managing memory entries with optional
    filtering and semantic search capabilities.

    Example:
        >>> class SimpleMemory(MemoryInterface):
        ...     def __init__(self):
        ...         self.memories = {}
        ...
        ...     def store(self, entry: MemoryEntryLike) -> str:
        ...         self.memories[entry.id] = entry
        ...         return entry.id
        ...
        ...     def retrieve(
        self, query: str, limit: int = 10, filters: dict | None = None
    ) -> list[MemoryEntryLike]:
        ...         # Simple keyword search
        ...         results = [
        ...             m for m in self.memories.values() if query.lower() in m.content.lower()
        ...         ]
        ...         return results[:limit]
        ...
        ...     def get_by_id(self, entry_id: str) -> MemoryEntryLike | None:
        ...         return self.memories.get(entry_id)
        ...
        ...     def delete(self, entry_id: str) -> bool:
        ...         if entry_id in self.memories:
        ...             del self.memories[entry_id]
        ...             return True
        ...         return False
    """

    @abstractmethod
    def store(self, entry: MemoryEntryLike) -> str:
        """Store a memory entry and return its ID.

        Args:
            entry: The memory entry to store.

        Returns:
            The ID of the stored memory entry.

        Raises:
            ValidationError: If the entry is invalid.

        Example:
            >>> memory = MyMemory()
            >>> entry = MemoryEntry(content="Important fact", memory_type="semantic")
            >>> entry_id = memory.store(entry)
            >>> print(entry_id)
        """
        pass

    @abstractmethod
    def retrieve(
        self, query: str, limit: int = 10, filters: dict[str, Any] | None = None
    ) -> list[MemoryEntryLike]:
        """Retrieve relevant memories based on query.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            filters: Optional filters to apply (e.g., {"memory_type": "episodic"}).

        Returns:
            List of relevant memory entries, ordered by relevance.

        Example:
            >>> memory = MyMemory()
            >>> results = memory.retrieve("user preferences", limit=5)
            >>> for entry in results:
            ...     print(entry.content)
        """
        pass

    @abstractmethod
    def get_by_id(self, entry_id: str) -> MemoryEntryLike | None:
        """Retrieve a specific memory by ID.

        Args:
            entry_id: The unique identifier of the memory entry.

        Returns:
            The memory entry if found, None otherwise.

        Example:
            >>> memory = MyMemory()
            >>> entry = memory.get_by_id("entry_123")
            >>> if entry:
            ...     print(entry.content)
        """
        pass

    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry.

        Args:
            entry_id: The unique identifier of the memory entry to delete.

        Returns:
            True if the entry was deleted, False if it didn't exist.

        Example:
            >>> memory = MyMemory()
            >>> success = memory.delete("entry_123")
            >>> print(success)
        """
        pass
