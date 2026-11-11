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


def test_the_default_backend_is_in_memory_and_the_store_picks_no_durable_one():
    """Requirement 12.2, decision D97: the router and its trackers default to memory; no helper picks a durable backend."""
    from skye.router import ModelRouter
    from skye.router.health_tracker import ModelHealth, RateLimitTracker
    from skye.store import InMemoryBackend

    assert type(ModelRouter().storage_backend) is InMemoryBackend
    assert type(ModelHealth(model_id="m").storage) is InMemoryBackend
    assert type(RateLimitTracker(model_id="m").storage) is InMemoryBackend
    assert not hasattr(skye.store, "default_durable_backend")
