"""Storage adapter interface for data persistence.

This module defines the abstract interface for storage adapters that handle
data persistence, querying, and vector search.
"""

from abc import ABC, abstractmethod
from typing import Any


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
