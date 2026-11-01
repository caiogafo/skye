"""AWS Durable Function storage backend (moved from routes/storage_backends.py)."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from nimbus.base.interfaces import StorageBackend


class DurableFunctionBackend(StorageBackend):
    """AWS Durable Function storage backend for serverless workflows."""

    def __init__(self, context: Any, key_prefix: str = "nimbus:"):
        """Initialize Durable Function backend.
        
        Args:
            context: DurableContext from aws_durable_execution_sdk
            key_prefix: Prefix for all keys
        """
        self.context = context
        self.key_prefix = key_prefix

    async def connect(self) -> None:
        """Initialize durable function storage (no-op)."""
        pass

    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from durable function context."""
        try:
            # Use durable context to get persistent data
            data = self.context.get_state(self._make_key(key))
            
            if data is None:
                return None
            
            # Check TTL if present
            import time
            if '_ttl' in data and time.time() > data['_ttl']:
                await self.set(key, None)  # Remove expired data
                return None
            
            # Remove TTL metadata before returning
            result = {k: v for k, v in data.items() if k != '_ttl'}
            return result
        except Exception:
            return None

    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in durable function context."""
        try:
            if data is None:
                # Remove the key
                self.context.set_state(self._make_key(key), None)
                return
            
            # Add TTL metadata if specified
            storage_data = dict(data)
            if ttl:
                import time
                storage_data['_ttl'] = time.time() + ttl
            
            self.context.set_state(self._make_key(key), storage_data)
        except Exception:
            pass  # Ignore errors in durable context

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment counter in durable function context."""
        current_data = await self.get(key) or {}
        new_value = current_data.get('count', 0) + amount
        await self.set(key, {'count': new_value}, ttl)
        return new_value

    async def get_multiple(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple keys from durable function context."""
        result = {}
        for key in keys:
            result[key] = await self.get(key)
        return result

    async def set_multiple(self, data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Set multiple keys in durable function context."""
        for key, value in data.items():
            await self.set(key, value, ttl)
