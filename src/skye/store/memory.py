"""In-memory storage backend (moved from routes/storage_backends.py)."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from skye.base.interfaces import StorageBackend


class InMemoryBackend(StorageBackend):
    """In-memory storage backend for single-instance environments."""

    def __init__(self):
        """Initialize in-memory backend."""
        self._data: Dict[str, Tuple[Dict[str, Any], Optional[float]]] = {}

    async def connect(self) -> None:
        """Initialize in-memory storage (no-op)."""
        pass

    def _is_expired(self, key: str) -> bool:
        """Check if key is expired."""
        if key not in self._data:
            return True
        _, expiry = self._data[key]
        return expiry is not None and time.time() > expiry

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from memory."""
        if self._is_expired(key):
            self._data.pop(key, None)
            return None
        
        data, _ = self._data.get(key, (None, None))
        return data

    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in memory."""
        expiry = time.time() + ttl if ttl else None
        self._data[key] = (data, expiry)

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment counter in memory."""
        current_data = await self.get(key) or {}
        new_value = current_data.get('count', 0) + amount
        await self.set(key, {'count': new_value}, ttl)
        return new_value

    async def get_multiple(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple keys from memory."""
        result = {}
        for key in keys:
            result[key] = await self.get(key)
        return result

    async def set_multiple(self, data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Set multiple keys in memory."""
        for key, value in data.items():
            await self.set(key, value, ttl)
