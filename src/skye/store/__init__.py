"""Shared store Component: the state backends behind the storage Ports (Requirement 12).

Six backends, each in its own module, with its driver imported only on first use (decisions D96,
D99):
``InMemoryBackend`` (the default, D97), ``FileSystemBackend``, ``DynamoDBBackend`` (boto3; extra
``aws`` outside Lambda),
``RedisBackend`` (extra ``redis``), ``PostgreSQLBackend`` (RDS Data API, then pg8000 with extra
``postgres``, then asyncpg with
extra ``postgres-asyncpg``; D100) and ``DurableFunctionBackend`` (the caller's durable context).
``backend(name, **config)``
builds one by name, ``register_backend`` adds one from outside Skye, and ``check_backend`` (from
``skye.store.conformance``) checks any backend (D98).

Codename: lake.
"""

from skye.base.interfaces.storage import CounterStore, KeyValueStore, ScanStore, StorageBackend
from skye.store.conformance import FakeClock, check_backend
from skye.store.durable_function import DurableFunctionBackend
from skye.store.dynamodb import DynamoDBBackend
from skye.store.factory import available_backends, backend, register_backend
from skye.store.file import FileSystemBackend
from skye.store.memory import InMemoryBackend
from skye.store.postgres import PostgreSQLBackend
from skye.store.redis import RedisBackend

__all__ = [
    "StorageBackend",
    "KeyValueStore",
    "CounterStore",
    "ScanStore",
    "InMemoryBackend",
    "FileSystemBackend",
    "DynamoDBBackend",
    "RedisBackend",
    "PostgreSQLBackend",
    "DurableFunctionBackend",
    "backend",
    "register_backend",
    "available_backends",
    "check_backend",
    "FakeClock",
]
