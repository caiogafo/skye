"""Storage adapter interface for data persistence.

This module defines the abstract interface for storage adapters that handle
data persistence, querying, and vector search.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageAdapterInterface(ABC):
    """Abstract interface for storage adapters.

    This interface defines the contract for storage implementations that
    support saving, querying, vector search, and deletion of data.
    """

    @abstractmethod
    def save(self, collection: str, data: dict[str, Any]) -> str:
        """Save data to a collection.

        Args:
            collection: Name of the collection/table.
            data: Data to save.

        Returns:
            ID of the saved record.
        """
        pass

    @abstractmethod
    def query(self, collection: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Query data from a collection.

        Args:
            collection: Name of the collection/table.
            filters: Query filters.

        Returns:
            List of matching records.
        """
        pass

    @abstractmethod
    def vector_search(
        self, collection: str, vector: list[float], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Perform vector similarity search.

        Args:
            collection: Name of the collection/table.
            vector: Query vector.
            limit: Maximum number of results.

        Returns:
            List of similar records.
        """
        pass

    @abstractmethod
    def delete(self, collection: str, record_id: str) -> bool:
        """Delete a record.

        Args:
            collection: Name of the collection/table.
            record_id: ID of the record to delete.

        Returns:
            True if deleted, False if not found.
        """
        pass


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def connect(self) -> None:
        """Initialize/connect to the storage backend."""
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from storage."""
        pass

    @abstractmethod
    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in storage with optional TTL."""
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment a counter."""
        pass

    @abstractmethod
    async def get_multiple(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple keys at once."""
        pass

    @abstractmethod
    async def set_multiple(self, data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Set multiple keys at once."""
        pass
