"""Routes package for unified model routing and load balancing.

This package provides a comprehensive routing solution with support for:
- Model aliases with multiple targets
- Health tracking and metrics
- Rate limiting (TPM/RPM)
- Multiple routing strategies
- Fallback chains
- Tag-based routing
- Cooldown mechanisms
- Multiple storage backends (in-memory, Redis, DynamoDB, PostgreSQL, FileSystem, DurableFunction)

Example (With Aliases):
    >>> from skye.router import ModelRouter, ModelTarget, RouteConfig
    >>> from skye.base.interfaces.router import RoutingStrategy
    >>>
    >>> # Define routes with aliases and multiple targets
    >>> router = ModelRouter(routes=[
    ...     RouteConfig(
    ...         alias="gpt-3.5-turbo",
    ...         targets=[
    ...             ModelTarget(
    ...                 model="azure/chatgpt-v-2",
    ...                 provider="azure",
    ...                 api_key="...",
    ...                 tpm=100000,
    ...                 rpm=1000
    ...             ),
    ...             ModelTarget(
    ...                 model="gpt-3.5-turbo",
    ...                 provider="openai",
    ...                 api_key="...",
    ...                 tpm=200000,
    ...                 rpm=2000
    ...             )
    ...         ],
    ...         strategy=RoutingStrategy.RATE_LIMIT_AWARE
    ...     )
    ... ])
    >>>
    >>> # Use alias in requests
    >>> response = router.complete(
    ...     messages=[UserMessage("Hello!")],
    ...     model="gpt-3.5-turbo"
    ... )

Example (With External Storage):
    >>> from skye.router import ModelRouter
    >>> from skye.store import RedisBackend
    >>>
    >>> # Use Redis for persistent state in serverless environments
    >>> storage = RedisBackend("redis://localhost:6379")
    >>> router = ModelRouter(
    ...     routes=[...],
    ...     storage=storage
    ... )

Example (Direct Registration):
    >>> from skye.router import ModelRouter
    >>> from skye.base.interfaces.router import RoutingStrategy
    >>>
    >>> # Create router and register models directly
    >>> router = ModelRouter(strategy=RoutingStrategy.LEAST_BUSY)
    >>> router.register_model("gpt-4", gpt4_model, tpm=100000, rpm=1000)
    >>> router.register_model("gpt-3.5", gpt35_model, tpm=200000, rpm=2000)
    >>>
    >>> # Set fallbacks
    >>> router.set_fallbacks([
    ...     {"primary": "gpt-4", "fallbacks": ["gpt-3.5"]}
    ... ])
    >>>
    >>> # Route requests
    >>> response = router.complete(
    ...     messages=[UserMessage("Hello!")],
    ...     model="gpt-4"
    ... )
    >>>
    >>> # Check health
    >>> health = router.get_model_health("gpt-4")
    >>> print(f"Success rate: {health['success_rate']:.1%}")

Codename: jet.
"""

from skye.router.config_models import (
    AllowedFailsPolicyConfig,
    CooldownInfo,
    FallbackConfig,
    ModelHealthMetrics,
    ModelTarget,
    RetryPolicyConfig,
    RouteConfig,
    UsageStats,
)
from skye.router.model_router import ModelRouter
from skye.base.interfaces import StorageBackend
from skye.store.durable_function import DurableFunctionBackend
from skye.store.dynamodb import DynamoDBBackend
from skye.store.file import FileSystemBackend
from skye.store.memory import InMemoryBackend
from skye.store.postgres import PostgreSQLBackend
from skye.store.redis import RedisBackend

__all__ = [
    # Router
    "ModelRouter",
    # Configuration models
    "ModelTarget",
    "RouteConfig",
    "FallbackConfig",
    "RetryPolicyConfig",
    "AllowedFailsPolicyConfig",
    # Metrics and stats models
    "ModelHealthMetrics",
    "UsageStats",
    "CooldownInfo",
    # Storage backends
    "StorageBackend",
    "InMemoryBackend",
    "RedisBackend",
    "DynamoDBBackend",
    "PostgreSQLBackend",
    "FileSystemBackend",
    "DurableFunctionBackend",
]
