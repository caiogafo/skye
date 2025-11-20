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
"""

import logging
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from nimbus.completion import CompletionRequest, CompletionResponse
from nimbus.exceptions import ConfigurationError, ProviderError
from nimbus.interfaces.model import ModelInterface
from nimbus.interfaces.router import ModelRouterInterface, RoutingStrategy

logger = logging.getLogger(__name__)


class ModelTarget(BaseModel):
    """A single model target/endpoint configuration.

    Args:
        model: Actual model identifier (e.g., "gpt-4", "azure/chatgpt-v-2")
        provider: Provider name (e.g., "openai", "azure", "bedrock")
        api_key: API key for authentication (optional)
        api_base: Base URL for API calls (optional)
        api_version: API version (optional, for Azure)
        region: Region for the deployment (optional)
        timeout: Request timeout in seconds (optional)
        max_retries: Maximum retry attempts (optional)
        weight: Weight for weighted routing (optional)
        tpm: Tokens per minute limit (optional)
        rpm: Requests per minute limit (optional)
        tags: Tags for tag-based routing (optional)
        metadata: Additional metadata (optional)

    Example:
        >>> target = ModelTarget(
        ...     model="azure/chatgpt-v-2",
        ...     provider="azure",
        ...     api_key="...",
        ...     api_base="https://my-resource.openai.azure.com",
        ...     api_version="2024-02-15-preview",
        ...     region="us-east-1",
        ...     tpm=100000,
        ...     rpm=1000,
        ...     tags=["premium", "paid"]
        ... )
    """

    model: str = Field(..., description="Actual model identifier")
    provider: str = Field(..., description="Provider name")
    api_key: str | None = Field(None, description="API key for authentication")
    api_base: str | None = Field(None, description="Base URL for API calls")
    api_version: str | None = Field(None, description="API version")
    region: str | None = Field(None, description="Deployment region")
    timeout: float | None = Field(None, description="Request timeout in seconds")
    max_retries: int | None = Field(None, description="Maximum retry attempts")
    weight: float = Field(1.0, description="Weight for weighted routing")
    tpm: int | None = Field(None, description="Tokens per minute limit")
    rpm: int | None = Field(None, description="Requests per minute limit")
    tags: list[str] = Field(default_factory=list, description="Tags for routing")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(extra="allow")


class RouteConfig(BaseModel):
    """Configuration for a route with one or more targets.

    A route defines an alias that maps to one or more model targets.
    When multiple targets are defined, the routing strategy determines
    which target to use.

    Args:
        alias: Alias name for this route (e.g., "fast", "gpt-3.5-turbo")
        targets: List of model targets for this route
        strategy: Strategy for selecting between targets
        fallback_on_error: Try next target on error (optional)

    Example:
        >>> route = RouteConfig(
        ...     alias="gpt-3.5-turbo",
        ...     targets=[
        ...         ModelTarget(model="azure/chatgpt-v-2", provider="azure", api_key="..."),
        ...         ModelTarget(model="gpt-3.5-turbo", provider="openai", api_key="...")
        ...     ],
        ...     strategy=RoutingStrategy.ROUND_ROBIN,
        ...     fallback_on_error=True
        ... )
    """

    alias: str = Field(..., description="Alias name for this route")
    targets: list[ModelTarget] = Field(..., min_length=1, description="Model targets")
    strategy: RoutingStrategy = Field(
        RoutingStrategy.ROUND_ROBIN, description="Routing strategy"
    )
    fallback_on_error: bool = Field(True, description="Try next target on error")


class FallbackConfig(BaseModel):
    """Configuration for fallback chains.

    Defines which models to try if the primary model fails.

    Args:
        primary: Primary model ID
        fallbacks: List of fallback model IDs to try in order

    Example:
        >>> fallback = FallbackConfig(
        ...     primary="gpt-4",
        ...     fallbacks=["gpt-3.5-turbo", "claude-3-sonnet"]
        ... )
    """

    primary: str = Field(..., description="Primary model ID")
    fallbacks: list[str] = Field(..., min_length=1, description="Fallback model IDs")


class RetryPolicyConfig(BaseModel):
    """Configuration for retry policies per error type.

    Defines how many times to retry for different error types.

    Args:
        error_type: Type of error (e.g., "RateLimitError", "TimeoutError")
        max_retries: Maximum number of retry attempts

    Example:
        >>> policy = RetryPolicyConfig(
        ...     error_type="RateLimitError",
        ...     max_retries=3
        ... )
    """

    error_type: str = Field(..., description="Error type")
    max_retries: int = Field(..., ge=0, description="Maximum retry attempts")


class AllowedFailsPolicyConfig(BaseModel):
    """Configuration for allowed fails before cooldown.

    Defines how many failures of each type are allowed per minute
    before cooling down a deployment.

    Args:
        error_type: Type of error
        allowed_fails_per_minute: Number of failures allowed per minute

    Example:
        >>> policy = AllowedFailsPolicyConfig(
        ...     error_type="RateLimitError",
        ...     allowed_fails_per_minute=100
        ... )
    """

    error_type: str = Field(..., description="Error type")
    allowed_fails_per_minute: int = Field(
        ..., ge=0, description="Allowed failures per minute"
    )


class ModelHealthMetrics(BaseModel):
    """Health metrics for a model.

    Contains comprehensive health and performance metrics.

    Example:
        >>> metrics = ModelHealthMetrics(
        ...     model_id="gpt-4",
        ...     success_count=100,
        ...     failure_count=5,
        ...     total_requests=105,
        ...     success_rate=0.952,
        ...     average_latency_ms=250.5
        ... )
    """

    model_id: str = Field(..., description="Model identifier")
    success_count: int = Field(0, ge=0, description="Number of successful requests")
    failure_count: int = Field(0, ge=0, description="Number of failed requests")
    total_requests: int = Field(0, ge=0, description="Total requests")
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="Success rate (0.0-1.0)")
    average_latency_ms: float = Field(0.0, ge=0.0, description="Average latency in ms")
    min_latency_ms: float | None = Field(None, description="Minimum latency in ms")
    max_latency_ms: float | None = Field(None, description="Maximum latency in ms")
    last_success_time: float | None = Field(None, description="Last success timestamp")
    last_failure_time: float | None = Field(None, description="Last failure timestamp")
    is_in_cooldown: bool = Field(False, description="Whether model is in cooldown")
    cooldown_until: float | None = Field(None, description="Cooldown end timestamp")
    failure_reasons: dict[str, int] = Field(
        default_factory=dict, description="Failure counts by reason"
    )
    active_requests: int = Field(0, ge=0, description="Currently active requests")
    tags: list[str] = Field(default_factory=list, description="Model tags")

    model_config = ConfigDict(extra="forbid")


class UsageStats(BaseModel):
    """Usage statistics for a model.

    Contains rate limit usage and request statistics.

    Example:
        >>> stats = UsageStats(
        ...     model_id="gpt-4",
        ...     tpm_used=50000,
        ...     tpm_limit=100000,
        ...     rpm_used=250,
        ...     rpm_limit=1000
        ... )
    """

    model_id: str = Field(..., description="Model identifier")
    tpm_used: int = Field(0, ge=0, description="Tokens used this minute")
    tpm_limit: int | None = Field(None, description="Tokens per minute limit")
    rpm_used: int = Field(0, ge=0, description="Requests made this minute")
    rpm_limit: int | None = Field(None, description="Requests per minute limit")
    active_requests: int = Field(0, ge=0, description="Currently active requests")
    total_requests: int = Field(0, ge=0, description="Total requests made")
    total_failures: int = Field(0, ge=0, description="Total failures")

    model_config = ConfigDict(extra="forbid")


class CooldownInfo(BaseModel):
    """Information about a model in cooldown.

    Example:
        >>> info = CooldownInfo(
        ...     model_id="gpt-4",
        ...     cooldown_until=1234567890.0,
        ...     reason="RateLimitError"
        ... )
    """

    model_id: str = Field(..., description="Model identifier")
    cooldown_until: float = Field(..., description="Cooldown end timestamp")
    reason: str = Field(..., description="Reason for cooldown")

    model_config = ConfigDict(extra="forbid")


logger = logging.getLogger(__name__)


@dataclass
class RateLimitTracker:
    """Track rate limits for a model deployment."""

    tpm_limit: int | None = None  # Tokens per minute
    rpm_limit: int | None = None  # Requests per minute
    tpm_used: int = 0
    rpm_used: int = 0
    active_requests: int = 0
    last_reset: float = field(default_factory=time.time)
    token_history: list[tuple[float, int]] = field(default_factory=list)  # (timestamp, tokens)
    request_history: list[float] = field(default_factory=list)  # timestamps

    def reset_if_needed(self) -> None:
        """Reset counters if a minute has passed."""
        current_time = time.time()
        if current_time - self.last_reset >= 60:
            self.tpm_used = 0
            self.rpm_used = 0
            self.last_reset = current_time
            # Clean old history
            cutoff = current_time - 60
            self.token_history = [(t, tokens) for t, tokens in self.token_history if t > cutoff]
            self.request_history = [t for t in self.request_history if t > cutoff]

    def can_accept_request(self, estimated_tokens: int = 0) -> bool:
        """Check if request can be accepted within rate limits."""
        self.reset_if_needed()

        if self.rpm_limit and self.rpm_used >= self.rpm_limit:
            return False

        if self.tpm_limit and estimated_tokens > 0:
            if self.tpm_used + estimated_tokens > self.tpm_limit:
                return False

        return True

    def record_request(self, tokens_used: int) -> None:
        """Record a completed request."""
        current_time = time.time()
        self.rpm_used += 1
        self.tpm_used += tokens_used
        self.request_history.append(current_time)
        self.token_history.append((current_time, tokens_used))


@dataclass
class ModelHealth:
    """Health tracking for a model deployment."""

    model_id: str
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0
    last_success_time: float | None = None
    last_failure_time: float | None = None
    cooldown_until: float | None = None
    failure_reasons: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    tags: list[str] = field(default_factory=list)

    def record_success(self, latency_ms: float) -> None:
        """Record a successful request."""
        self.success_count += 1
        self.total_latency_ms += latency_ms
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)
        self.last_success_time = time.time()

    def record_failure(self, reason: str = "unknown") -> None:
        """Record a failed request."""
        self.failure_count += 1
        self.failure_reasons[reason] += 1
        self.last_failure_time = time.time()

    def set_cooldown(self, duration_seconds: float) -> None:
        """Set cooldown period."""
        self.cooldown_until = time.time() + duration_seconds

    def is_in_cooldown(self) -> bool:
        """Check if model is in cooldown."""
        if self.cooldown_until is None:
            return False
        return time.time() < self.cooldown_until

    def get_avg_latency_ms(self) -> float:
        """Get average latency."""
        if self.success_count == 0:
            return float("inf")
        return self.total_latency_ms / self.success_count

    def get_success_rate(self) -> float:
        """Get success rate (0.0-1.0)."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total


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
            self.health[model_id] = ModelHealth(model_id=model_id, tags=target.tags)
            self.rate_limits[model_id] = RateLimitTracker(
                tpm_limit=target.tpm, rpm_limit=target.rpm
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
        self.health[model_id] = ModelHealth(model_id=model_id, tags=tags or [])
        self.rate_limits[model_id] = RateLimitTracker(tpm_limit=tpm, rpm_limit=rpm)
        logger.info(f"Registered model: {model_id}")

    def select_model(self, request: CompletionRequest) -> str:
        """Select a model based on routing strategy.

        If the request specifies an alias, selects from targets for that alias.
        Otherwise, selects from all available models.
        """
        # Check if request model is an alias
        if request.model and request.model in self.aliases:
            return self._select_from_alias(request.model, request)

        # Otherwise select from all available models
        available_models = self._get_available_models(request)

        if not available_models:
            raise ProviderError(
                "No available models for routing",
                provider="router",
                details={"strategy": self.strategy.value},
            )

        return self._apply_strategy(available_models, None)

    def _select_from_alias(self, alias: str, request: CompletionRequest) -> str:
        """Select a target from an alias based on the route's strategy."""
        route = self.aliases[alias]

        # Get all model IDs for this alias
        alias_models = [
            model_id for model_id in self.models.keys() if model_id.startswith(f"{alias}:")
        ]

        # Filter by availability
        available_models = [
            m for m in alias_models if self._is_model_available(m, request)
        ]

        if not available_models:
            raise ProviderError(
                f"No available targets for alias '{alias}'",
                provider="router",
                details={"alias": alias, "total_targets": len(alias_models)},
            )

        # Use route-specific strategy if different from default
        strategy = route.strategy if route.strategy else self.strategy
        return self._apply_strategy(available_models, alias, strategy)

    def _apply_strategy(
        self,
        available_models: list[str],
        alias: str | None = None,
        strategy: RoutingStrategy | None = None,
    ) -> str:
        """Apply routing strategy to select a model."""
        if strategy is None:
            strategy = self.strategy

        if strategy == RoutingStrategy.ROUND_ROBIN:
            if alias:
                index = self._round_robin_index.get(alias, 0)
                model_id = available_models[index % len(available_models)]
                self._round_robin_index[alias] = index + 1
            else:
                index = self._round_robin_index.get("_default", 0)
                model_id = available_models[index % len(available_models)]
                self._round_robin_index["_default"] = index + 1
            return model_id

        elif strategy == RoutingStrategy.SIMPLE_SHUFFLE:
            return random.choice(available_models)

        elif strategy == RoutingStrategy.LEAST_BUSY:
            return min(
                available_models,
                key=lambda m: self.rate_limits[m].active_requests,
            )

        elif strategy == RoutingStrategy.LATENCY_BASED:
            return min(
                available_models,
                key=lambda m: self.health[m].get_avg_latency_ms(),
            )

        elif strategy == RoutingStrategy.RATE_LIMIT_AWARE:
            # Select model with most available capacity
            def get_capacity_score(model_id: str) -> float:
                tracker = self.rate_limits[model_id]
                if tracker.rpm_limit is None and tracker.tpm_limit is None:
                    return 1.0

                rpm_capacity = 1.0
                if tracker.rpm_limit:
                    rpm_capacity = 1.0 - (tracker.rpm_used / tracker.rpm_limit)

                tpm_capacity = 1.0
                if tracker.tpm_limit:
                    tpm_capacity = 1.0 - (tracker.tpm_used / tracker.tpm_limit)

                return min(rpm_capacity, tpm_capacity)

            return max(available_models, key=get_capacity_score)

        elif strategy == RoutingStrategy.WEIGHTED:
            # Use target weight if available, otherwise success rate
            weights = []
            for m in available_models:
                if m in self.model_targets:
                    weights.append(self.model_targets[m].weight)
                else:
                    weights.append(self.health[m].get_success_rate())
            return random.choices(available_models, weights=weights)[0]

        elif strategy == RoutingStrategy.PRIORITY_BASED:
            # Use success rate as priority
            return max(
                available_models,
                key=lambda m: self.health[m].get_success_rate(),
            )

        else:
            return available_models[0]

    def route_request(self, request: CompletionRequest) -> CompletionResponse:
        """Route a request to an appropriate model."""
        model_id = request.model if request.model else self.select_model(request)
        fallback_chain = self.fallbacks.get(model_id, [])

        # Try primary model
        response = self._try_model(model_id, request)
        if response:
            return response

        # Try fallbacks
        for fallback_id in fallback_chain:
            logger.warning(f"Primary model {model_id} failed, trying fallback: {fallback_id}")
            response = self._try_model(fallback_id, request)
            if response:
                return response

        raise ProviderError(
            f"All models failed for request (tried: {model_id}, {fallback_chain})",
            provider="router",
        )

    async def aroute_request(self, request: CompletionRequest) -> CompletionResponse:
        """Route a request asynchronously."""
        # For now, use sync version
        # TODO: Implement true async routing
        return self.route_request(request)

    def _try_model(
        self, model_id: str, request: CompletionRequest
    ) -> CompletionResponse | None:
        """Try to execute request on a specific model."""
        if model_id not in self.models:
            logger.error(f"Model {model_id} not registered")
            return None

        health = self.health[model_id]
        rate_limit = self.rate_limits[model_id]

        # Check cooldown
        if health.is_in_cooldown():
            logger.warning(f"Model {model_id} is in cooldown")
            return None

        # Check rate limits (pre-call check)
        if self.pre_call_checks_enabled:
            if not rate_limit.can_accept_request(estimated_tokens=1000):
                logger.warning(f"Model {model_id} rate limit exceeded")
                return None

        # Increment active requests
        rate_limit.active_requests += 1

        try:
            start_time = time.time()
            model = self.models[model_id]
            response = model.complete(request)
            latency_ms = (time.time() - start_time) * 1000

            # Record success
            health.record_success(latency_ms)
            tokens_used = response.usage.total_tokens if response.usage else 0
            rate_limit.record_request(tokens_used)

            return response

        except Exception as e:
            # Record failure
            error_type = type(e).__name__
            health.record_failure(error_type)

            # Check if should cooldown
            if self._should_cooldown(model_id, error_type):
                health.set_cooldown(self.cooldown_seconds)
                logger.warning(
                    f"Model {model_id} put in cooldown for {self.cooldown_seconds}s "
                    f"due to {error_type}"
                )

            logger.error(f"Model {model_id} failed: {e}")
            return None

        finally:
            rate_limit.active_requests -= 1

    def _should_cooldown(self, model_id: str, error_type: str) -> bool:
        """Determine if model should be put in cooldown."""
        if error_type not in self.allowed_fails_policy:
            return False

        health = self.health[model_id]
        allowed_fails = self.allowed_fails_policy[error_type]
        recent_fails = health.failure_reasons.get(error_type, 0)

        return recent_fails >= allowed_fails

    def _is_model_available(self, model_id: str, request: CompletionRequest) -> bool:
        """Check if a model is available for routing."""
        health = self.health.get(model_id)
        rate_limit = self.rate_limits.get(model_id)

        if not health or not rate_limit:
            return False

        # Skip if in cooldown
        if health.is_in_cooldown():
            return False

        # Skip if rate limit exceeded (if pre-call checks enabled)
        if self.pre_call_checks_enabled:
            if not rate_limit.can_accept_request():
                return False

        return True

    def _get_available_models(self, request: CompletionRequest) -> list[str]:
        """Get list of available models (not in cooldown, within rate limits)."""
        return [
            model_id
            for model_id in self.models.keys()
            if self._is_model_available(model_id, request)
        ]

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
            self.health[model_id].set_cooldown(self.cooldown_seconds)
            logger.warning(f"Model {model_id} manually marked as failed")

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

        health = self.health[model_id]
        rate_limit = self.rate_limits[model_id]

        return ModelHealthMetrics(
            model_id=model_id,
            success_count=health.success_count,
            failure_count=health.failure_count,
            total_requests=health.success_count + health.failure_count,
            success_rate=health.get_success_rate(),
            average_latency_ms=health.get_avg_latency_ms(),
            min_latency_ms=health.min_latency_ms if health.min_latency_ms != float("inf") else None,
            max_latency_ms=health.max_latency_ms if health.max_latency_ms > 0 else None,
            last_success_time=health.last_success_time,
            last_failure_time=health.last_failure_time,
            is_in_cooldown=health.is_in_cooldown(),
            cooldown_until=health.cooldown_until,
            failure_reasons=dict(health.failure_reasons),
            active_requests=rate_limit.active_requests,
            tags=health.tags,
        )

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
