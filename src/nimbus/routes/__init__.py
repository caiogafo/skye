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
    >>> from nimbus import ModelRouter, ModelTarget, RouteConfig
    >>> from nimbus.interfaces.router import RoutingStrategy
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
    >>> response = router.route_request(
    ...     CompletionRequest(messages=[...], model="gpt-3.5-turbo")
    ... )

Example (With External Storage):
    >>> from nimbus.routes import ModelRouter
    >>> from nimbus.routes.storage_backends import RedisBackend
    >>>
    >>> # Use Redis for persistent state in serverless environments
    >>> storage = RedisBackend("redis://localhost:6379")
    >>> router = ModelRouter(
    ...     routes=[...],
    ...     storage=storage
    ... )

Example (Direct Registration):
    >>> from nimbus import ModelRouter
    >>> from nimbus.interfaces.router import RoutingStrategy
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
    >>> response = router.route_request(request)
    >>>
    >>> # Check health
    >>> health = router.get_model_health("gpt-4")
    >>> print(f"Success rate: {health['success_rate']:.1%}")
"""

from nimbus.routes.config_models import (
    AllowedFailsPolicyConfig,
    CooldownInfo,
    FallbackConfig,
    ModelHealthMetrics,
    ModelTarget,
    RetryPolicyConfig,
    RouteConfig,
    UsageStats,
)
from nimbus.routes.model_router import ModelRouter
from nimbus.routes.storage_backends import (
    StorageBackend,
    InMemoryBackend,
    RedisBackend,
    DynamoDBBackend,
    PostgreSQLBackend,
    FileSystemBackend,
    DurableFunctionBackend,
)

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
