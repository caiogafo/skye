"""Unified model router with health tracking, rate limiting, and alias support.

This module provides a complete routing solution with support for:
- Model aliases with multiple targets
- Multiple routing strategies (round-robin, least-busy, rate-limit-aware, etc.)
- Health tracking and metrics per model
- Rate limiting (TPM/RPM) with sliding window
- Cooldown mechanisms for failed models
- Retry policies per error type
- Fallback chains
- Tag-based routing
- Pre-call rate limit checks
- Automatic provider instantiation from configuration
- External storage backends for serverless environments
"""

import logging
import time
from typing import Any, Optional

from nimbus.completion import CompletionRequest, CompletionResponse
from nimbus.exceptions import ConfigurationError, ProviderError
from nimbus.interfaces.model import ModelInterface
from nimbus.interfaces.router import ModelRouterInterface, RoutingStrategy

from .config_models import (
    AllowedFailsPolicyConfig,
    CooldownInfo,
    FallbackConfig,
    ModelHealthMetrics,
    ModelTarget,
    RetryPolicyConfig,
    RouteConfig,
    UsageStats,
)
from .health_tracker import ModelHealth, RateLimitTracker
from .routing_strategies import RoutingStrategySelector
from .storage_backends import StorageBackend, InMemoryBackend

logger = logging.getLogger(__name__)


class ModelRouter(ModelRouterInterface):
    """Unified model router with health tracking, rate limiting, and alias support.

    This router provides comprehensive routing capabilities including:
    - Model aliases with multiple targets
    - Multiple routing strategies
    - Health tracking per model
    - Rate limiting (TPM/RPM)
    - Cooldown for failed models
    - Retry policies
    - Fallback chains
    - Tag-based routing
    - Automatic provider instantiation

    Example (Direct Registration):
        >>> from nimbus import ModelRouter
        >>> from nimbus.interfaces.router import RoutingStrategy
        >>>
        >>> router = ModelRouter(strategy=RoutingStrategy.LEAST_BUSY)
        >>> router.register_model("gpt-4", gpt4_model)
        >>> router.register_model("gpt-3.5", gpt35_model)
        >>> router.set_rate_limits("gpt-4", tpm=100000, rpm=1000)
        >>>
        >>> response = router.route_request(request)

    Example (With Aliases and Targets):
        >>> from nimbus import ModelRouter, ModelTarget, RouteConfig
        >>> from nimbus.interfaces.router import RoutingStrategy
        >>>
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
    """

    def __init__(
        self,
        routes: list[RouteConfig] | None = None,
        strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN,
        cooldown_seconds: float = 60.0,
        enable_pre_call_checks: bool = True,
        fallbacks: list[FallbackConfig] | None = None,
        retry_policies: list[RetryPolicyConfig] | None = None,
        allowed_fails_policies: list[AllowedFailsPolicyConfig] | None = None,
        storage: Optional[StorageBackend] = None,
    ):
        """Initialize the router.

        Args:
            routes: Optional list of route configurations with aliases.
            strategy: Default routing strategy.
            cooldown_seconds: Default cooldown duration for failed models.
            enable_pre_call_checks: Whether to check rate limits before calls.
            fallbacks: Optional list of fallback configurations.
            retry_policies: Optional list of retry policy configurations.
            allowed_fails_policies: Optional list of allowed fails policy configurations.
            storage: Optional external storage backend. If None, uses in-memory storage.

        Example:
            >>> router = ModelRouter(
            ...     routes=[...],
            ...     strategy=RoutingStrategy.LEAST_BUSY,
            ...     cooldown_seconds=60.0,
            ...     fallbacks=[
            ...         FallbackConfig(primary="gpt-4", fallbacks=["gpt-3.5-turbo"])
            ...     ],
            ...     retry_policies=[
            ...         RetryPolicyConfig(error_type="RateLimitError", max_retries=3)
            ...     ],
            ...     allowed_fails_policies=[
            ...         AllowedFailsPolicyConfig(
            ...             error_type="RateLimitError",
            ...             allowed_fails_per_minute=100
            ...         )
            ...     ]
            ... )
        """
        self.strategy = strategy
        self.cooldown_seconds = cooldown_seconds
        self.pre_call_checks_enabled = enable_pre_call_checks
        self.storage_backend = storage or InMemoryBackend()

        self.models: dict[str, ModelInterface] = {}
        self.model_targets: dict[str, ModelTarget] = {}  # Store target configs
        self.aliases: dict[str, RouteConfig] = {}  # Alias -> RouteConfig mapping
        self.health: dict[str, ModelHealth] = {}
        self.rate_limits: dict[str, RateLimitTracker] = {}
        self.fallbacks: dict[str, list[str]] = {}
        self.retry_policy: dict[str, int] = {
            "RateLimitError": 3,
            "TimeoutError": 2,
            "ServerError": 2,
            "AuthenticationError": 0,
        }
        self.allowed_fails_policy: dict[str, int] = {
            "RateLimitError": 100,
            "ContentPolicyViolationError": 1000,
        }

        self._round_robin_index: dict[str, int] = {}  # Per-alias round-robin index

        # Initialize routing strategy selector
        self._strategy_selector = RoutingStrategySelector(
            health=self.health,
            rate_limits=self.rate_limits,
            model_targets=self.model_targets,
            round_robin_index=self._round_robin_index,
        )

        # Initialize routes if provided
        if routes:
            for route in routes:
                self._register_route(route)

        # Initialize fallbacks if provided
        if fallbacks:
            self.set_fallbacks(fallbacks)

        # Initialize retry policies if provided
        if retry_policies:
            self.set_retry_policy(retry_policies)

        # Initialize allowed fails policies if provided
        if allowed_fails_policies:
            self.set_allowed_fails_policy(allowed_fails_policies)

        # Initialize storage backend
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Initialize storage backend synchronously."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            asyncio.create_task(self.storage_backend.connect())
        except RuntimeError:
            # No running loop, use asyncio.run
            asyncio.run(self.storage_backend.connect())

    @classmethod
    def from_yaml(cls, yaml_path: str | Any, **kwargs) -> "ModelRouter":
        """Create a ModelRouter from a YAML configuration file.

        This class method loads router configuration from a YAML file and
        creates a ModelRouter instance with the specified configuration.
        Environment variables in the YAML file (using ${VAR_NAME} syntax)
        are automatically substituted.

        Args:
            yaml_path: Path to the YAML configuration file.
            **kwargs: Additional keyword arguments to override config values.

        Returns:
            ModelRouter instance configured from the YAML file.

        Raises:
            ConfigurationError: If the file doesn't exist, can't be parsed,
                or contains invalid configuration.

        Example:
            >>> # Create router from YAML file
            >>> router = ModelRouter.from_yaml("router_config.yaml")
            >>>
            >>> # Override specific settings
            >>> router = ModelRouter.from_yaml(
            ...     "router_config.yaml",
            ...     cooldown_seconds=120.0
            ... )
        """
        from nimbus.config import load_router_config

        # Load configuration from YAML
        config_dict = load_router_config(yaml_path)

        # Merge with kwargs (kwargs take precedence)
        config_dict.update(kwargs)

        # Create router from config dict
        return cls.from_config_dict(config_dict)

    @classmethod
    def from_config_dict(cls, config: dict[str, Any], **kwargs) -> "ModelRouter":
        """Create a ModelRouter from a configuration dictionary.

        This class method creates a ModelRouter instance from a configuration
        dictionary. The dictionary should follow the RouterConfig schema.

        Args:
            config: Configuration dictionary with router settings.
            **kwargs: Additional keyword arguments to override config values.

        Returns:
            ModelRouter instance configured from the dictionary.

        Raises:
            ConfigurationError: If the configuration is invalid.

        Example:
            >>> config = {
            ...     "routes": [
            ...         {
            ...             "alias": "gpt-3.5-turbo",
            ...             "targets": [
            ...                 {
            ...                     "model": "gpt-3.5-turbo",
            ...                     "provider": "openai",
            ...                     "api_key": "sk-...",
            ...                     "tpm": 200000,
            ...                     "rpm": 2000
            ...                 }
            ...             ],
            ...             "strategy": "rate_limit_aware"
            ...         }
            ...     ],
            ...     "strategy": "round_robin",
            ...     "cooldown_seconds": 60.0
            ... }
            >>> router = ModelRouter.from_config_dict(config)
        """
        # Extract router-level settings
        strategy_str = kwargs.get("strategy", config.get("strategy", "round_robin"))
        cooldown_seconds = kwargs.get(
            "cooldown_seconds", config.get("cooldown_seconds", 60.0)
        )
        enable_pre_call_checks = kwargs.get(
            "enable_pre_call_checks", config.get("enable_pre_call_checks", True)
        )

        # Convert strategy string to enum
        try:
            strategy = RoutingStrategy(strategy_str)
        except ValueError:
            raise ConfigurationError(
                f"Invalid routing strategy: {strategy_str}",
                details={
                    "strategy": strategy_str,
                    "valid_strategies": [s.value for s in RoutingStrategy],
                },
            )

        # Parse routes
        routes = []
        for route_dict in config.get("routes", []):
            try:
                # Parse targets
                targets = [ModelTarget(**target) for target in route_dict.get("targets", [])]

                # Parse strategy for this route
                route_strategy_str = route_dict.get("strategy", strategy_str)
                try:
                    route_strategy = RoutingStrategy(route_strategy_str)
                except ValueError:
                    raise ConfigurationError(
                        f"Invalid routing strategy for route '{route_dict.get('alias')}': {route_strategy_str}",
                        details={
                            "alias": route_dict.get("alias"),
                            "strategy": route_strategy_str,
                            "valid_strategies": [s.value for s in RoutingStrategy],
                        },
                    )

                route = RouteConfig(
                    alias=route_dict["alias"],
                    targets=targets,
                    strategy=route_strategy,
                    fallback_on_error=route_dict.get("fallback_on_error", True),
                )
                routes.append(route)
            except KeyError as e:
                raise ConfigurationError(
                    f"Missing required field in route configuration: {e}",
                    details={"route": route_dict, "missing_field": str(e)},
                ) from e
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to parse route configuration: {e}",
                    details={"route": route_dict, "error": str(e)},
                ) from e

        # Parse fallbacks
        fallbacks = []
        for fallback_dict in config.get("fallbacks", []):
            try:
                fallback = FallbackConfig(**fallback_dict)
                fallbacks.append(fallback)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to parse fallback configuration: {e}",
                    details={"fallback": fallback_dict, "error": str(e)},
                ) from e

        # Parse retry policies
        retry_policies = []
        for policy_dict in config.get("retry_policies", []):
            try:
                policy = RetryPolicyConfig(**policy_dict)
                retry_policies.append(policy)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to parse retry policy configuration: {e}",
                    details={"policy": policy_dict, "error": str(e)},
                ) from e

        # Parse allowed fails policies
        allowed_fails_policies = []
        for policy_dict in config.get("allowed_fails_policies", []):
            try:
                policy = AllowedFailsPolicyConfig(**policy_dict)
                allowed_fails_policies.append(policy)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to parse allowed fails policy configuration: {e}",
                    details={"policy": policy_dict, "error": str(e)},
                ) from e

        # Create router instance
        return cls(
            routes=routes if routes else None,
            strategy=strategy,
            cooldown_seconds=cooldown_seconds,
            enable_pre_call_checks=enable_pre_call_checks,
            fallbacks=fallbacks if fallbacks else None,
            retry_policies=retry_policies if retry_policies else None,
            allowed_fails_policies=allowed_fails_policies if allowed_fails_policies else None,
        )

    def _register_route(self, route: RouteConfig) -> None:
        """Register a route configuration with alias and targets."""
        if route.alias in self.aliases:
            raise ConfigurationError(f"Duplicate route alias: '{route.alias}'")

        self.aliases[route.alias] = route
        self._round_robin_index[route.alias] = 0

        # Register each target as a model
        for target in route.targets:
            # Create unique model ID for this target
            model_id = f"{route.alias}:{target.provider}:{target.model}"

            # Instantiate provider if not already a model instance
            from nimbus.providers.registry import ProviderRegistry

            provider_config = {
                "model": target.model,
            }
            if target.api_key:
                provider_config["api_key"] = target.api_key
            if target.api_base:
                provider_config["api_base"] = target.api_base
            if target.api_version:
                provider_config["api_version"] = target.api_version
            if target.region:
                provider_config["region_name"] = target.region
            if target.timeout:
                provider_config["timeout"] = target.timeout

            model = ProviderRegistry.get_model_provider(target.provider, **provider_config)

            # Register the model
            self.models[model_id] = model
            self.model_targets[model_id] = target
            
            # Create health and rate limit trackers with shared storage backend
            self.health[model_id] = ModelHealth(model_id=model_id, tags=target.tags, storage=self.storage_backend)
            self.rate_limits[model_id] = RateLimitTracker(
                tpm_limit=target.tpm, rpm_limit=target.rpm, model_id=model_id, storage=self.storage_backend
            )

            logger.info(f"Registered target: {model_id} (alias: {route.alias})")

    def register_model(
        self,
        model_id: str,
        model: ModelInterface,
        tpm: int | None = None,
        rpm: int | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Register a model directly with the router.

        Args:
            model_id: Unique identifier for the model.
            model: The model instance implementing ModelInterface.
            tpm: Optional tokens per minute limit.
            rpm: Optional requests per minute limit.
            tags: Optional tags for tag-based routing.
        """
        self.models[model_id] = model
        
        # Create health and rate limit trackers with shared storage backend
        self.health[model_id] = ModelHealth(model_id=model_id, tags=tags or [], storage=self.storage_backend)
        self.rate_limits[model_id] = RateLimitTracker(tpm_limit=tpm, rpm_limit=rpm, model_id=model_id, storage=self.storage_backend)
        logger.info(f"Registered model: {model_id}")

    async def select_model(self, request: CompletionRequest) -> str:
        """Select a model based on routing strategy.

        If the request specifies an alias, selects from targets for that alias.
        Otherwise, selects from all available models.
        """
        # Check if request model is an alias
        if request.model and request.model in self.aliases:
            return await self._select_from_alias(request.model, request)

        # Otherwise select from all available models
        available_models = await self._get_available_models(request)

        if not available_models:
            raise ProviderError(
                "No available models for routing",
                provider="router",
                details={"strategy": self.strategy.value},
            )

        return self._strategy_selector.apply_strategy(available_models, None, self.strategy)

    async def _select_from_alias(self, alias: str, request: CompletionRequest) -> str:
        """Select a target from an alias based on the route's strategy."""
        route = self.aliases[alias]

        # Get all model IDs for this alias
        alias_models = [
            model_id for model_id in self.models.keys() if model_id.startswith(f"{alias}:")
        ]

        # Filter by availability
        available_models = []
        for model_id in alias_models:
            if await self._is_model_available(model_id, request):
                available_models.append(model_id)

        if not available_models:
            raise ProviderError(
                f"No available targets for alias '{alias}'",
                provider="router",
                details={"alias": alias, "total_targets": len(alias_models)},
            )

        # Use route-specific strategy if different from default
        strategy = route.strategy if route.strategy else self.strategy
        return self._strategy_selector.apply_strategy(available_models, alias, strategy)

    def route_request(self, request: CompletionRequest) -> CompletionResponse:
        """Route a request to an appropriate model."""
        import asyncio
        
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, but this is a sync method
            # Create a new thread to run the async code
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.aroute_request(request))
                return future.result()
        except RuntimeError:
            # No running loop, we can use asyncio.run
            return asyncio.run(self.aroute_request(request))

    async def aroute_request(self, request: CompletionRequest) -> CompletionResponse:
        """Route a request asynchronously."""
        model_id = request.model if request.model else await self.select_model(request)
        fallback_chain = self.fallbacks.get(model_id, [])

        # Try primary model
        response = await self._try_model(model_id, request)
        if response:
            return response

        # Try fallbacks
        for fallback_id in fallback_chain:
            logger.warning(f"Primary model {model_id} failed, trying fallback: {fallback_id}")
            response = await self._try_model(fallback_id, request)
            if response:
                return response

        raise ProviderError(
            f"All models failed for request (tried: {model_id}, {fallback_chain})",
            provider="router",
        )

    async def _try_model(
        self, model_id: str, request: CompletionRequest
    ) -> CompletionResponse | None:
        """Try to execute request on a specific model."""
        if model_id not in self.models:
            logger.error(f"Model {model_id} not registered")
            return None

        health = self.health[model_id]
        rate_limit = self.rate_limits[model_id]

        # Check cooldown
        if await health.is_in_cooldown():
            logger.warning(f"Model {model_id} is in cooldown")
            return None

        # Check rate limits (pre-call check)
        if self.pre_call_checks_enabled:
            if not await rate_limit.can_accept_request(estimated_tokens=1000):
                logger.warning(f"Model {model_id} rate limit exceeded")
                return None

        # Increment active requests
        await rate_limit.increment_active_requests()

        try:
            start_time = time.time()
            model = self.models[model_id]
            response = model.complete(request)
            latency_ms = (time.time() - start_time) * 1000

            # Record success
            await health.record_success(latency_ms)
            tokens_used = response.usage.total_tokens if response.usage else 0
            await rate_limit.record_request(tokens_used)

            return response

        except Exception as e:
            # Record failure
            error_type = type(e).__name__
            await health.record_failure(error_type)

            # Check if should cooldown
            if await self._should_cooldown(model_id, error_type):
                await health.set_cooldown(self.cooldown_seconds)
                logger.warning(
                    f"Model {model_id} put in cooldown for {self.cooldown_seconds}s "
                    f"due to {error_type}"
                )

            logger.error(f"Model {model_id} failed: {e}")
            return None

        finally:
            await rate_limit.decrement_active_requests()

    async def _should_cooldown(self, model_id: str, error_type: str) -> bool:
        """Determine if model should be put in cooldown."""
        if error_type not in self.allowed_fails_policy:
            return False

        health = self.health[model_id]
        health_metrics = await health.get_health_metrics()
        allowed_fails = self.allowed_fails_policy[error_type]
        recent_fails = health_metrics.get('failure_reasons', {}).get(error_type, 0)

        return recent_fails >= allowed_fails

    async def _is_model_available(self, model_id: str, request: CompletionRequest) -> bool:
        """Check if a model is available for routing."""
        health = self.health.get(model_id)
        rate_limit = self.rate_limits.get(model_id)

        if not health or not rate_limit:
            return False

        # Skip if in cooldown
        if await health.is_in_cooldown():
            return False

        # Skip if rate limit exceeded (if pre-call checks enabled)
        if self.pre_call_checks_enabled:
            if not await rate_limit.can_accept_request():
                return False

        return True

    async def _get_available_models(self, request: CompletionRequest) -> list[str]:
        """Get list of available models (not in cooldown, within rate limits)."""
        available = []
        for model_id in self.models.keys():
            if await self._is_model_available(model_id, request):
                available.append(model_id)
        return available

    def is_alias(self, name: str) -> bool:
        """Check if a name is a registered alias.

        Args:
            name: Name to check.

        Returns:
            True if name is a registered alias.
        """
        return name in self.aliases

    def list_aliases(self) -> list[str]:
        """List all registered aliases.

        Returns:
            List of alias names.
        """
        return list(self.aliases.keys())

    def get_route(self, alias: str) -> RouteConfig | None:
        """Get the route configuration for an alias.

        Args:
            alias: Alias name.

        Returns:
            RouteConfig if alias exists, None otherwise.
        """
        return self.aliases.get(alias)

    def mark_model_failed(self, model_id: str) -> None:
        """Mark a model as failed for cooldown."""
        if model_id in self.health:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create a task
                asyncio.create_task(self.health[model_id].set_cooldown(self.cooldown_seconds))
            except RuntimeError:
                # No running loop, use asyncio.run
                asyncio.run(self.health[model_id].set_cooldown(self.cooldown_seconds))
            logger.warning(f"Model {model_id} manually marked as failed")

    async def aget_model_health(self, model_id: str) -> ModelHealthMetrics:
        """Get health status of a model asynchronously.

        Args:
            model_id: The model identifier.

        Returns:
            ModelHealthMetrics object with comprehensive health data.
        """
        if model_id not in self.health:
            return ModelHealthMetrics(model_id=model_id)

        health = self.health[model_id]
        rate_limit = self.rate_limits[model_id]
        
        health_metrics = await health.get_health_metrics()
        usage_stats = await rate_limit.get_current_usage()

        return ModelHealthMetrics(
            model_id=model_id,
            success_count=health_metrics.get('success_count', 0),
            failure_count=health_metrics.get('failure_count', 0),
            total_requests=health_metrics.get('total_requests', 0),
            success_rate=health_metrics.get('success_rate', 1.0),
            average_latency_ms=health_metrics.get('average_latency_ms', 0.0),
            min_latency_ms=health_metrics.get('min_latency_ms'),
            max_latency_ms=health_metrics.get('max_latency_ms'),
            last_success_time=health_metrics.get('last_success_time'),
            last_failure_time=health_metrics.get('last_failure_time'),
            is_in_cooldown=health_metrics.get('is_in_cooldown', False),
            cooldown_until=health_metrics.get('cooldown_until'),
            failure_reasons=health_metrics.get('failure_reasons', {}),
            active_requests=usage_stats.get('active_requests', 0),
            tags=health.tags,
        )

    def get_model_health(self, model_id: str) -> ModelHealthMetrics:
        """Get health status of a model.

        Args:
            model_id: The model identifier.

        Returns:
            ModelHealthMetrics object with comprehensive health data.

        Example:
            >>> health = router.get_model_health("gpt-4")
            >>> print(f"Success rate: {health.success_rate:.1%}")
        """
        if model_id not in self.health:
            return ModelHealthMetrics(model_id=model_id)

        # For sync method, run async method
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, but this is a sync method
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.aget_model_health(model_id))
                return future.result()
        except RuntimeError:
            # No running loop, use asyncio.run
            return asyncio.run(self.aget_model_health(model_id))

    def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """Set the routing strategy."""
        self.strategy = strategy
        logger.info(f"Routing strategy set to: {strategy.value}")

    def set_fallbacks(self, fallbacks: list[FallbackConfig]) -> None:
        """Set fallback model chains.

        Args:
            fallbacks: List of FallbackConfig objects defining fallback chains.

        Example:
            >>> router.set_fallbacks([
            ...     FallbackConfig(
            ...         primary="gpt-4",
            ...         fallbacks=["gpt-3.5-turbo", "claude-3-sonnet"]
            ...     )
            ... ])
        """
        for config in fallbacks:
            self.fallbacks[config.primary] = config.fallbacks
            logger.info(f"Set fallbacks for {config.primary}: {config.fallbacks}")

    def set_retry_policy(self, retry_policies: list[RetryPolicyConfig]) -> None:
        """Set retry policy per error type.

        Args:
            retry_policies: List of RetryPolicyConfig objects.

        Example:
            >>> router.set_retry_policy([
            ...     RetryPolicyConfig(error_type="RateLimitError", max_retries=3),
            ...     RetryPolicyConfig(error_type="TimeoutError", max_retries=2)
            ... ])
        """
        for policy in retry_policies:
            self.retry_policy[policy.error_type] = policy.max_retries
        logger.info(f"Updated retry policy: {self.retry_policy}")

    def set_allowed_fails_policy(self, allowed_fails_policies: list[AllowedFailsPolicyConfig]) -> None:
        """Set allowed fails before cooldown per error type.

        Args:
            allowed_fails_policies: List of AllowedFailsPolicyConfig objects.

        Example:
            >>> router.set_allowed_fails_policy([
            ...     AllowedFailsPolicyConfig(
            ...         error_type="RateLimitError",
            ...         allowed_fails_per_minute=100
            ...     )
            ... ])
        """
        for policy in allowed_fails_policies:
            self.allowed_fails_policy[policy.error_type] = policy.allowed_fails_per_minute
        logger.info(f"Updated allowed fails policy: {self.allowed_fails_policy}")

    def set_cooldown_time(self, cooldown_seconds: float) -> None:
        """Set cooldown duration for failed models."""
        self.cooldown_seconds = cooldown_seconds
        logger.info(f"Cooldown time set to: {cooldown_seconds}s")

    def enable_pre_call_checks(self, enabled: bool = True) -> None:
        """Enable/disable pre-call rate limit checks."""
        self.pre_call_checks_enabled = enabled
        logger.info(f"Pre-call checks {'enabled' if enabled else 'disabled'}")

    def set_rate_limits(
        self, model_id: str, tpm: int | None = None, rpm: int | None = None
    ) -> None:
        """Set rate limits for a model deployment."""
        if model_id not in self.rate_limits:
            self.rate_limits[model_id] = RateLimitTracker()

        tracker = self.rate_limits[model_id]
        tracker.tpm_limit = tpm
        tracker.rpm_limit = rpm
        logger.info(f"Set rate limits for {model_id}: TPM={tpm}, RPM={rpm}")

    def get_usage_stats(self, model_id: str) -> UsageStats:
        """Get current usage statistics for a model.

        Args:
            model_id: The model identifier.

        Returns:
            UsageStats object with rate limit and request statistics.

        Example:
            >>> stats = router.get_usage_stats("gpt-4")
            >>> print(f"TPM used: {stats.tpm_used}/{stats.tpm_limit}")
        """
        if model_id not in self.rate_limits:
            return UsageStats(model_id=model_id)

        tracker = self.rate_limits[model_id]
        tracker.reset_if_needed()
        health = self.health.get(model_id)

        return UsageStats(
            model_id=model_id,
            tpm_used=tracker.tpm_used,
            tpm_limit=tracker.tpm_limit,
            rpm_used=tracker.rpm_used,
            rpm_limit=tracker.rpm_limit,
            active_requests=tracker.active_requests,
            total_requests=health.success_count + health.failure_count if health else 0,
            total_failures=health.failure_count if health else 0,
        )

    def get_cooldown_models(self) -> list[CooldownInfo]:
        """Get list of models currently in cooldown.

        Returns:
            List of CooldownInfo objects for models in cooldown.

        Example:
            >>> cooled_down = router.get_cooldown_models()
            >>> for info in cooled_down:
            ...     print(f"{info.model_id} cooled down until {info.cooldown_until}")
        """
        cooled_down = []

        for model_id, health in self.health.items():
            if health.is_in_cooldown():
                reason = "unknown"
                if health.failure_reasons:
                    reason = max(health.failure_reasons.items(), key=lambda x: x[1])[0]

                cooled_down.append(
                    CooldownInfo(
                        model_id=model_id,
                        cooldown_until=health.cooldown_until,  # type: ignore
                        reason=reason,
                    )
                )

        return cooled_down

    def set_model_tags(self, model_id: str, tags: list[str]) -> None:
        """Set tags for a model deployment."""
        if model_id in self.health:
            self.health[model_id].tags = tags
            logger.info(f"Set tags for {model_id}: {tags}")

    def route_with_tags(
        self, request: CompletionRequest, required_tags: list[str]
    ) -> CompletionResponse:
        """Route request to models matching required tags."""
        # Filter models by tags
        matching_models = [
            model_id
            for model_id, health in self.health.items()
            if all(tag in health.tags for tag in required_tags)
        ]

        if not matching_models:
            raise ValueError(
                f"No models found with required tags: {required_tags}"
            )

        # Temporarily override available models for selection
        original_models = self.models
        self.models = {k: v for k, v in self.models.items() if k in matching_models}

        try:
            return self.route_request(request)
        finally:
            self.models = original_models