"""Model routing for load balancing and custom model aliases.

This module provides routing capabilities for load balancing across multiple
model deployments with custom aliases.

Example:
    >>> from nimbus import routes as rt
    >>> import nimbus
    >>>
    >>> # Define routes with structured configuration
    >>> registry = rt.RouterRegistry([
    ...     rt.RouteConfig(
    ...         alias="gpt-3.5-turbo",
    ...         targets=[
    ...             rt.ModelTarget(
    ...                 model="azure/chatgpt-v-2",
    ...                 provider="azure",
    ...                 api_key="...",
    ...                 api_base="...",
    ...                 api_version="2024-02-15-preview"
    ...             ),
    ...             rt.ModelTarget(
    ...                 model="gpt-3.5-turbo",
    ...                 provider="openai",
    ...                 api_key="..."
    ...             )
    ...         ],
    ...         strategy="round-robin"
    ...     ),
    ...     rt.RouteConfig(
    ...         alias="gpt-4",
    ...         targets=[
    ...             rt.ModelTarget(model="gpt-4", provider="openai", api_key="...")
    ...         ]
    ...     )
    ... ])
    >>>
    >>> # Attach registry to client
    >>> client = nimbus.provider("openai", router=registry)
    >>>
    >>> # Use alias as model name - registry routes to appropriate target
    >>> response = client.complete(
    ...     messages=[UserMessage("Hello")],
    ...     model="gpt-3.5-turbo"
    ... )
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from nimbus.exceptions import ConfigurationError

RoutingStrategy = Literal["round-robin", "random", "least-busy", "least-latency", "weighted"]


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
        metadata: Additional metadata (optional)

    Example:
        >>> target = rt.ModelTarget(
        ...     model="azure/chatgpt-v-2",
        ...     provider="azure",
        ...     api_key="...",
        ...     api_base="https://my-resource.openai.azure.com",
        ...     api_version="2024-02-15-preview",
        ...     region="us-east-1"
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
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(extra="allow")


class RouteConfig(BaseModel):
    """Configuration for a single route with multiple targets.

    A route defines an alias that maps to one or more model targets.
    When multiple targets are defined, the routing strategy determines
    which target to use.

    Args:
        alias: Alias name for this route (e.g., "fast", "gpt-3.5-turbo")
        targets: List of model targets for this route
        strategy: Strategy for selecting between targets
        fallback_on_error: Try next target on error (optional)

    Example:
        >>> route = rt.RouteConfig(
        ...     alias="gpt-3.5-turbo",
        ...     targets=[
        ...         rt.ModelTarget(model="azure/chatgpt-v-2", provider="azure", api_key="..."),
        ...         rt.ModelTarget(model="gpt-3.5-turbo", provider="openai", api_key="...")
        ...     ],
        ...     strategy="round-robin",
        ...     fallback_on_error=True
        ... )
    """

    alias: str = Field(..., description="Alias name for this route")
    targets: list[ModelTarget] = Field(..., min_length=1, description="Model targets")
    strategy: RoutingStrategy = Field("round-robin", description="Routing strategy")
    fallback_on_error: bool = Field(True, description="Try next target on error")


class _TargetMetrics:
    """Internal metrics tracking for a model target."""

    def __init__(self, target: ModelTarget):
        self.target = target
        self.total_calls = 0
        self.failed_calls = 0
        self.total_latency_ms = 0.0
        self.min_latency_ms: float | None = None
        self.max_latency_ms: float | None = None

    def record_call(self, latency_ms: float, success: bool = True) -> None:
        """Record a call to this target for metrics tracking."""
        self.total_calls += 1
        if not success:
            self.failed_calls += 1
            return

        self.total_latency_ms += latency_ms
        if self.min_latency_ms is None or latency_ms < self.min_latency_ms:
            self.min_latency_ms = latency_ms
        if self.max_latency_ms is None or latency_ms > self.max_latency_ms:
            self.max_latency_ms = latency_ms

    @property
    def avg_latency_ms(self) -> float:
        """Average latency for successful calls."""
        successful_calls = self.total_calls - self.failed_calls
        if successful_calls == 0:
            return float("inf")
        return self.total_latency_ms / successful_calls

    @property
    def success_rate(self) -> float:
        """Success rate (0.0 to 1.0)."""
        if self.total_calls == 0:
            return 1.0
        return (self.total_calls - self.failed_calls) / self.total_calls


class RouterRegistry:
    """Registry for managing multiple routes with load balancing.

    The registry manages a collection of routes, each with one or more targets.
    When a model alias is requested, the registry selects the appropriate target
    based on the configured routing strategy.

    Args:
        routes: List of route configurations

    Example:
        >>> registry = rt.RouterRegistry([
        ...     rt.RouteConfig(
        ...         alias="gpt-3.5-turbo",
        ...         targets=[
        ...             rt.ModelTarget(model="azure/chatgpt-v-2", provider="azure", api_key="..."),
        ...             rt.ModelTarget(model="gpt-3.5-turbo", provider="openai", api_key="...")
        ...         ],
        ...         strategy="round-robin"
        ...     )
        ... ])
        >>>
        >>> # Use with client
        >>> client = nimbus.provider("openai", router=registry)
        >>> response = client.complete(messages=[...], model="gpt-3.5-turbo")
    """

    def __init__(self, routes: list[RouteConfig]):
        """Initialize registry with route configurations.

        Args:
            routes: List of route configurations
        """
        self.routes: dict[str, RouteConfig] = {}
        self._metrics: dict[str, list[_TargetMetrics]] = {}
        self._round_robin_index: dict[str, int] = {}

        for route in routes:
            if route.alias in self.routes:
                raise ConfigurationError(f"Duplicate route alias: '{route.alias}'")

            self.routes[route.alias] = route
            self._metrics[route.alias] = [_TargetMetrics(t) for t in route.targets]
            self._round_robin_index[route.alias] = 0

    def resolve_model(self, alias: str) -> str:
        """Resolve an alias to an actual model identifier.

        If the alias has multiple targets, selects one based on
        the routing strategy. Otherwise, returns the alias unchanged.

        Args:
            alias: Model alias or actual model name

        Returns:
            Actual model identifier to use

        Example:
            >>> registry = rt.RouterRegistry([...])
            >>> registry.resolve_model("gpt-3.5-turbo")
            'azure/chatgpt-v-2'
        """
        if alias not in self.routes:
            # Not a registered alias, return as-is
            return alias

        route = self.routes[alias]

        if len(route.targets) == 1:
            return route.targets[0].model

        # Select target based on strategy
        target = self._select_target(alias, route)
        return target.model

    def _select_target(self, alias: str, route: RouteConfig) -> ModelTarget:
        """Select a target based on routing strategy."""
        targets = route.targets
        metrics = self._metrics[alias]

        if route.strategy == "round-robin":
            index = self._round_robin_index[alias]
            target = targets[index]
            self._round_robin_index[alias] = (index + 1) % len(targets)
            return target

        elif route.strategy == "random":
            import random

            return random.choice(targets)

        elif route.strategy == "least-busy":
            # Select target with fewest total calls
            min_idx = min(range(len(metrics)), key=lambda i: metrics[i].total_calls)
            return targets[min_idx]

        elif route.strategy == "least-latency":
            # Select target with lowest average latency
            min_idx = min(range(len(metrics)), key=lambda i: metrics[i].avg_latency_ms)
            return targets[min_idx]

        elif route.strategy == "weighted":
            # Weighted random selection
            import random

            weights = [t.weight for t in targets]
            return random.choices(targets, weights=weights)[0]

        else:
            # Default to first target
            return targets[0]

    def get_target(self, alias: str, model: str) -> ModelTarget | None:
        """Get a specific target by alias and model identifier.

        Args:
            alias: Route alias
            model: Actual model identifier

        Returns:
            ModelTarget if found, None otherwise
        """
        if alias not in self.routes:
            return None

        route = self.routes[alias]
        for target in route.targets:
            if target.model == model:
                return target

        return None

    def is_alias(self, name: str) -> bool:
        """Check if a name is a registered alias.

        Args:
            name: Name to check

        Returns:
            True if name is a registered alias

        Example:
            >>> registry = rt.RouterRegistry([...])
            >>> registry.is_alias("gpt-3.5-turbo")
            True
        """
        return name in self.routes

    def list_aliases(self) -> list[str]:
        """List all registered aliases.

        Returns:
            List of alias names

        Example:
            >>> registry = rt.RouterRegistry([...])
            >>> registry.list_aliases()
            ['gpt-3.5-turbo', 'gpt-4']
        """
        return list(self.routes.keys())

    def get_route(self, alias: str) -> RouteConfig | None:
        """Get the route configuration for an alias.

        Args:
            alias: Alias name

        Returns:
            RouteConfig if alias exists, None otherwise

        Example:
            >>> registry = rt.RouterRegistry([...])
            >>> route = registry.get_route("gpt-3.5-turbo")
            >>> len(route.targets)
            2
        """
        return self.routes.get(alias)
