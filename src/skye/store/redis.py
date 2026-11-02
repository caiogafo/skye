"""Redis storage backend (moved from routes/storage_backends.py)."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from skye.base.interfaces import StorageBackend


class RedisBackend(StorageBackend):
    """Redis storage backend for distributed environments."""

    def __init__(self, redis_url: str, key_prefix: str = "skye:"):
        """Initialize Redis backend.
        
        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all keys
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._redis = None

    async def connect(self) -> None:
        """Initialize Redis connection."""
        await self._get_redis()  # This will create the connection

    async def _get_redis(self):
        """Get Redis connection (lazy initialization)."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.redis_url)
            except ImportError:
                raise ImportError("redis package required for RedisBackend. Install with: pip install skyeai[memory]")
        return self._redis

    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis."""
        redis = await self._get_redis()
        data = await redis.get(self._make_key(key))
        return json.loads(data) if data else None

    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in Redis."""
        redis = await self._get_redis()
        await redis.set(self._make_key(key), json.dumps(data), ex=ttl)

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment counter in Redis."""
        redis = await self._get_redis()
        
        # Get current data or create new
        current_data = await self.get(key) or {}
        new_value = current_data.get('count', 0) + amount
        
        # Store as JSON object with 'count' field for consistency
        await self.set(key, {'count': new_value}, ttl)
        return new_value

    async def get_multiple(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple keys from Redis."""
        if not keys:
            return {}
        
        redis = await self._get_redis()
        prefixed_keys = [self._make_key(key) for key in keys]
        values = await redis.mget(prefixed_keys)
        
        result = {}
        for i, key in enumerate(keys):
            value = values[i]
            result[key] = json.loads(value) if value else None
        
        return result

    async def set_multiple(self, data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Set multiple keys in Redis."""
        if not data:
            return
        
        redis = await self._get_redis()
        pipe = redis.pipeline()
        
        for key, value in data.items():
            pipe.set(self._make_key(key), json.dumps(value), ex=ttl)
        
        await pipe.execute()
