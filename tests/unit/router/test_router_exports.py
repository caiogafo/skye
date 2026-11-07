"""`skye.router` does not re-export the storage backends: they have one home, `skye.store` (decision D40, Requirement 22.4)."""

import skye.router
import skye.store

BACKENDS = ["StorageBackend", "InMemoryBackend", "RedisBackend", "DynamoDBBackend", "PostgreSQLBackend", "FileSystemBackend", "DurableFunctionBackend"]


def test_router_does_not_export_storage_backends():
    for name in BACKENDS:
        assert name not in skye.router.__all__
        assert not hasattr(skye.router, name)


def test_storage_backends_live_in_store():
    for name in BACKENDS:
        assert hasattr(skye.store, name)
