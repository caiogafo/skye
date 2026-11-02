"""File system storage backend (moved from routes/storage_backends.py)."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from skye.base.interfaces import StorageBackend


class FileSystemBackend(StorageBackend):
    """File system storage backend for persistent local storage."""

    def __init__(self, base_path: str = "/tmp/skye_storage"):
        """Initialize file system backend.
        
        Args:
            base_path: Base directory for storing files
        """
        import os
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def connect(self) -> None:
        """Initialize file system storage."""
        import os
        os.makedirs(self.base_path, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        """Get file path for a key."""
        import os
        # Replace invalid filename characters
        safe_key = key.replace('/', '_').replace(':', '_')
        return os.path.join(self.base_path, f"{safe_key}.json")

    def _is_expired(self, data: Dict[str, Any]) -> bool:
        """Check if data is expired."""
        import time
        expiry = data.get('_ttl')
        return expiry is not None and time.time() > expiry

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from file system."""
        import json
        import os
        
        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if self._is_expired(data):
                os.remove(file_path)
                return None
            
            # Remove TTL metadata before returning
            result = {k: v for k, v in data.items() if k != '_ttl'}
            return result
        except (json.JSONDecodeError, IOError):
            return None

    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in file system."""
        import json
        import time
        
        file_path = self._get_file_path(key)
        
        # Add TTL metadata if specified
        storage_data = dict(data)
        if ttl:
            storage_data['_ttl'] = time.time() + ttl
        
        try:
            with open(file_path, 'w') as f:
                json.dump(storage_data, f)
        except IOError:
            pass  # Ignore write errors

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment counter in file system."""
        current_data = await self.get(key) or {}
        new_value = current_data.get('count', 0) + amount
        await self.set(key, {'count': new_value}, ttl)
        return new_value

    async def get_multiple(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple keys from file system."""
        result = {}
        for key in keys:
            result[key] = await self.get(key)
        return result

    async def set_multiple(self, data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Set multiple keys in file system."""
        for key, value in data.items():
            await self.set(key, value, ttl)
