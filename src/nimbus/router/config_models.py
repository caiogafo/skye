"""Configuration models for the model router.

This module contains all Pydantic models used for router configuration,
including targets, routes, fallbacks, and policies.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from nimbus.base.interfaces.router import RoutingStrategy


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
        ...     api_key="${AZURE_API_KEY}",  # Env var substitution
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

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to substitute environment variables in string fields.

        This method is called automatically after model initialization and
        substitutes ${VAR_NAME} patterns with environment variable values
        in all string fields.
        """
        self._substitute_env_vars()

    def _substitute_env_vars(self) -> None:
        """Substitute ${VAR_NAME} patterns with environment variables in string fields.

        This method processes all string fields in the model and replaces
        environment variable references with their actual values. It uses
        the substitute_env_vars function from nimbus.base.config.

        Raises:
            ConfigurationError: If a referenced environment variable is not found.
        """
        from nimbus.base.config import substitute_env_vars

        # Substitute in all string fields (access model_fields from class, not instance)
        for field_name in self.__class__.model_fields:
            value = getattr(self, field_name)
            if isinstance(value, str):
                substituted = substitute_env_vars(value)
                setattr(self, field_name, substituted)


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