"""Storage backend Port: the asynchronous key-value store used by ``store`` and the router.

The vector-store Port that used to live here (``StorageAdapterInterface``, decision D41) had no implementation and was removed;
it will be designed again with the first vector store of ``memory``.

Raises: ProviderError when the backend is unreachable, ValidationError for invalid data.
Missing: ``get``, ``get_by_id`` and ``query`` return ``None`` or an empty collection for an absent key, never raise for absence; an expired entry is absent.
Concurrency: backends are used from many tasks: ``increment`` must be atomic; ``connect`` is called once before use.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


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
