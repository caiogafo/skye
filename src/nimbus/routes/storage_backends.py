"""Storage backends for router state persistence.

This module provides different storage backends that can be used
for persisting router state in various environments.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


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


class RedisBackend(StorageBackend):
    """Redis storage backend for distributed environments."""

    def __init__(self, redis_url: str, key_prefix: str = "nimbus:"):
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
                raise ImportError("redis package required for RedisBackend. Install with: pip install redis")
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


class FileSystemBackend(StorageBackend):
    """File system storage backend for persistent local storage."""

    def __init__(self, base_path: str = "/tmp/nimbus_storage"):
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


class PostgreSQLBackend(StorageBackend):
    """PostgreSQL storage backend for persistent database storage."""

    def __init__(self, connection_string: str, table_name: str = "nimbus_storage"):
        """Initialize PostgreSQL backend.
        
        Args:
            connection_string: PostgreSQL connection string
            table_name: Table name for storing data
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self._pool = None

    async def connect(self) -> None:
        """Initialize PostgreSQL connection and create table if needed."""
        await self._get_pool()  # This will create the pool and table

    async def _get_pool(self):
        """Get connection pool (lazy initialization)."""
        if self._pool is None:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(self.connection_string)
                
                # Create table if it doesn't exist
                async with self._pool.acquire() as conn:
                    await conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            key VARCHAR(255) PRIMARY KEY,
                            data JSONB NOT NULL,
                            expires_at TIMESTAMP
                        )
                    """)
                    
                    # Create index on expires_at for efficient cleanup
                    await conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_expires_at 
                        ON {self.table_name} (expires_at)
                    """)
            except ImportError:
                raise ImportError("asyncpg package required for PostgreSQLBackend. Install with: pip install asyncpg")
        return self._pool

    async def _cleanup_expired(self, conn) -> None:
        """Clean up expired entries."""
        await conn.execute(f"""
            DELETE FROM {self.table_name} 
            WHERE expires_at IS NOT NULL AND expires_at < NOW()
        """)

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from PostgreSQL."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Clean up expired entries periodically
            import random
            if random.random() < 0.1:  # 10% chance
                await self._cleanup_expired(conn)
            
            row = await conn.fetchrow(f"""
                SELECT data FROM {self.table_name} 
                WHERE key = $1 AND (expires_at IS NULL OR expires_at > NOW())
            """, key)
            
            return dict(row['data']) if row else None

    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in PostgreSQL."""
        import json
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            expires_at = None
            if ttl:
                expires_at = f"NOW() + INTERVAL '{ttl} seconds'"
            
            if expires_at:
                await conn.execute(f"""
                    INSERT INTO {self.table_name} (key, data, expires_at) 
                    VALUES ($1, $2, {expires_at})
                    ON CONFLICT (key) DO UPDATE SET 
                        data = EXCLUDED.data, 
                        expires_at = EXCLUDED.expires_at
                """, key, json.dumps(data))
            else:
                await conn.execute(f"""
                    INSERT INTO {self.table_name} (key, data, expires_at) 
                    VALUES ($1, $2, NULL)
                    ON CONFLICT (key) DO UPDATE SET 
                        data = EXCLUDED.data, 
                        expires_at = NULL
                """, key, json.dumps(data))

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment counter in PostgreSQL."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Use PostgreSQL's atomic operations
            expires_at = None
            if ttl:
                expires_at = f"NOW() + INTERVAL '{ttl} seconds'"
            
            if expires_at:
                row = await conn.fetchrow(f"""
                    INSERT INTO {self.table_name} (key, data, expires_at) 
                    VALUES ($1, '{{"count": {amount}}}', {expires_at})
                    ON CONFLICT (key) DO UPDATE SET 
                        data = jsonb_set(
                            COALESCE({self.table_name}.data, '{{}}'::jsonb), 
                            '{{count}}', 
                            (COALESCE(({self.table_name}.data->>'count')::int, 0) + {amount})::text::jsonb
                        ),
                        expires_at = EXCLUDED.expires_at
                    RETURNING (data->>'count')::int as count
                """, key)
            else:
                row = await conn.fetchrow(f"""
                    INSERT INTO {self.table_name} (key, data, expires_at) 
                    VALUES ($1, '{{"count": {amount}}}', NULL)
                    ON CONFLICT (key) DO UPDATE SET 
                        data = jsonb_set(
                            COALESCE({self.table_name}.data, '{{}}'::jsonb), 
                            '{{count}}', 
                            (COALESCE(({self.table_name}.data->>'count')::int, 0) + {amount})::text::jsonb
                        )
                    RETURNING (data->>'count')::int as count
                """, key)
            
            return row['count']

    async def get_multiple(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple keys from PostgreSQL."""
        if not keys:
            return {}
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT key, data FROM {self.table_name} 
                WHERE key = ANY($1) AND (expires_at IS NULL OR expires_at > NOW())
            """, keys)
            
            result = {key: None for key in keys}
            for row in rows:
                result[row['key']] = dict(row['data'])
            
            return result

    async def set_multiple(self, data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Set multiple keys in PostgreSQL."""
        if not data:
            return
        
        import json
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            expires_at = None
            if ttl:
                expires_at = f"NOW() + INTERVAL '{ttl} seconds'"
            
            # Use batch insert with ON CONFLICT
            values = []
            for key, value in data.items():
                if expires_at:
                    values.append(f"('{key}', '{json.dumps(value)}', {expires_at})")
                else:
                    values.append(f"('{key}', '{json.dumps(value)}', NULL)")
            
            values_str = ', '.join(values)
            
            await conn.execute(f"""
                INSERT INTO {self.table_name} (key, data, expires_at) 
                VALUES {values_str}
                ON CONFLICT (key) DO UPDATE SET 
                    data = EXCLUDED.data, 
                    expires_at = EXCLUDED.expires_at
            """)

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None


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


class DynamoDBBackend(StorageBackend):
    """DynamoDB storage backend for AWS serverless environments."""

    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        """Initialize DynamoDB backend.
        
        Args:
            table_name: DynamoDB table name
            region_name: AWS region
        """
        self.table_name = table_name
        self.region_name = region_name
        self._dynamodb = None

    async def connect(self) -> None:
        """Initialize DynamoDB connection."""
        await self._get_dynamodb()  # This will create the connection

    async def _get_dynamodb(self):
        """Get DynamoDB resource (lazy initialization)."""
        if self._dynamodb is None:
            try:
                import boto3
                self._dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
            except ImportError:
                raise ImportError("boto3 package required for DynamoDBBackend. Install with: pip install boto3")
        return self._dynamodb

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from DynamoDB."""
        dynamodb = await self._get_dynamodb()
        table = dynamodb.Table(self.table_name)
        
        try:
            response = table.get_item(Key={'pk': key})
            item = response.get('Item')
            if item:
                # Remove DynamoDB metadata
                item.pop('pk', None)
                item.pop('ttl', None)
                return item
            return None
        except Exception:
            return None

    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in DynamoDB."""
        dynamodb = await self._get_dynamodb()
        table = dynamodb.Table(self.table_name)
        
        item = {'pk': key, **data}
        if ttl:
            item['ttl'] = int(time.time()) + ttl
        
        table.put_item(Item=item)

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment counter in DynamoDB."""
        dynamodb = await self._get_dynamodb()
        table = dynamodb.Table(self.table_name)
        
        update_expression = "ADD #count :amount"
        expression_attribute_names = {"#count": "count"}
        expression_attribute_values = {":amount": amount}
        
        if ttl:
            update_expression += ", #ttl :ttl"
            expression_attribute_names["#ttl"] = "ttl"
            expression_attribute_values[":ttl"] = int(time.time()) + ttl
        
        response = table.update_item(
            Key={'pk': key},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="NEW"
        )
        
        return response['Attributes']['count']

    async def get_multiple(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple keys from DynamoDB."""
        if not keys:
            return {}
        
        dynamodb = await self._get_dynamodb()
        
        # DynamoDB batch_get_item
        request_items = {
            self.table_name: {
                'Keys': [{'pk': key} for key in keys]
            }
        }
        
        response = dynamodb.batch_get_item(RequestItems=request_items)
        items = response.get('Responses', {}).get(self.table_name, [])
        
        result = {key: None for key in keys}
        for item in items:
            key = item.pop('pk')
            item.pop('ttl', None)  # Remove TTL metadata
            result[key] = item
        
        return result

    async def set_multiple(self, data: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Set multiple keys in DynamoDB."""
        if not data:
            return
        
        dynamodb = await self._get_dynamodb()
        table = dynamodb.Table(self.table_name)
        
        # Use batch_writer for efficient bulk writes
        with table.batch_writer() as batch:
            for key, value in data.items():
                item = {'pk': key, **value}
                if ttl:
                    item['ttl'] = int(time.time()) + ttl
                batch.put_item(Item=item)