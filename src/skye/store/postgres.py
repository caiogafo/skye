"""PostgreSQL storage backend (moved from routes/storage_backends.py)."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from skye.base.interfaces import StorageBackend


class PostgreSQLBackend(StorageBackend):
    """PostgreSQL storage backend for persistent database storage."""

    def __init__(self, connection_string: str, table_name: str = "skye_storage"):
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
