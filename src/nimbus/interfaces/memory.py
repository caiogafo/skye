"""Memory interface for persistent storage.

This module defines the abstract interface for memory storage and retrieval.
It enables agents to store and recall information across sessions.

Example:
    >>> from nimbus.interfaces.memory import MemoryInterface
    >>> from nimbus.memory import MemoryEntry
    >>>
    >>> class MyMemory(MemoryInterface):
    ...     def store(self, entry: MemoryEntry) -> str:
    ...         # Implementation here
    ...         pass
"""

from abc import ABC, abstractmethod
from typing import Any

from nimbus.memory import MemoryEntry


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
        ...     def store(self, entry: MemoryEntry) -> str:
        ...         self.memories[entry.id] = entry
        ...         return entry.id
        ...
        ...     def retrieve(
        self, query: str, limit: int = 10, filters: dict | None = None
    ) -> list[MemoryEntry]:
        ...         # Simple keyword search
        ...         results = [
        ...             m for m in self.memories.values() if query.lower() in m.content.lower()
        ...         ]
        ...         return results[:limit]
        ...
        ...     def get_by_id(self, entry_id: str) -> MemoryEntry | None:
        ...         return self.memories.get(entry_id)
        ...
        ...     def delete(self, entry_id: str) -> bool:
        ...         if entry_id in self.memories:
        ...             del self.memories[entry_id]
        ...             return True
        ...         return False
    """

    @abstractmethod
    def store(self, entry: MemoryEntry) -> str:
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
    ) -> list[MemoryEntry]:
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
    def get_by_id(self, entry_id: str) -> MemoryEntry | None:
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
