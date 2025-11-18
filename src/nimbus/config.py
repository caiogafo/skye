"""Configuration models and loading system for Nimbus.

This module provides Pydantic models for configuring Nimbus components including
rate limiting, retries, cooldowns, model configurations, and global settings.
It also includes the ConfigLoader for loading configuration from multiple sources.

Example:
    >>> from nimbus.config import ModelConfig, RateLimitConfig
    >>>
    >>> # Create a model configuration with rate limits
    >>> config = ModelConfig(
    ...     model_id="gpt-4",
    ...     provider="openai",
    ...     rate_limits=RateLimitConfig(
    ...         requests_per_minute=60,
    ...         tokens_per_minute=90000
    ...     )
    ... )
    >>> config.model_id
    'gpt-4'
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RateLimitConfig(BaseModel):
    """Rate limit configuration for a model.

    Defines rate limiting constraints for API requests to prevent exceeding
    provider quotas. Supports both request-based and token-based limits
    at minute and day granularity.

    Attributes:
        requests_per_minute: Maximum number of requests allowed per minute.
        tokens_per_minute: Maximum number of tokens allowed per minute.
        requests_per_day: Maximum number of requests allowed per day.
        tokens_per_day: Maximum number of tokens allowed per day.

    Example:
        >>> rate_limits = RateLimitConfig(
        ...     requests_per_minute=60,
        ...     tokens_per_minute=90000,
        ...     requests_per_day=10000,
        ...     tokens_per_day=2000000
        ... )
        >>> rate_limits.requests_per_minute
        60
    """

    requests_per_minute: int | None = None
    tokens_per_minute: int | None = None
    requests_per_day: int | None = None
    tokens_per_day: int | None = None


class RetryConfig(BaseModel):
    """Retry configuration for a model.

    Defines retry behavior for failed API requests including maximum retry
    attempts, delay between retries, exponential backoff, and which error
    types should trigger retries.

    Attributes:
        max_retries: Maximum number of retry attempts.
        retry_after_seconds: Base delay in seconds between retry attempts.
        exponential_backoff: Whether to use exponential backoff for retries.
        retry_on_errors: List of error types that should trigger retries.

    Example:
        >>> retry_config = RetryConfig(
        ...     max_retries=3,
        ...     retry_after_seconds=5,
        ...     exponential_backoff=True,
        ...     retry_on_errors=["rate_limit", "timeout", "server_error"]
        ... )
        >>> retry_config.max_retries
        3
    """

    max_retries: int = 3
    retry_after_seconds: int = 5
    exponential_backoff: bool = True
    retry_on_errors: list[str] = Field(
        default_factory=lambda: ["rate_limit", "timeout", "server_error"]
    )


class CooldownConfig(BaseModel):
    """Cooldown configuration for failed models.

    Defines cooldown behavior to temporarily disable models that experience
    repeated failures, preventing cascading failures and allowing time for
    recovery.

    Attributes:
        enabled: Whether cooldown is enabled.
        allowed_fails_per_minute: Number of failures allowed per minute before cooldown.
        cooldown_duration_seconds: Duration in seconds to keep model in cooldown.

    Example:
        >>> cooldown_config = CooldownConfig(
        ...     enabled=True,
        ...     allowed_fails_per_minute=3,
        ...     cooldown_duration_seconds=60
        ... )
        >>> cooldown_config.enabled
        True
    """

    enabled: bool = True
    allowed_fails_per_minute: int = 3
    cooldown_duration_seconds: int = 60


class ModelConfig(BaseModel):
    """Configuration for a model.

    Comprehensive configuration for an LLM model including provider details,
    API credentials, generation parameters, routing configuration, and cost tracking.

    Attributes:
        model_id: Unique identifier for the model (e.g., 'gpt-4', 'claude-3-sonnet').
        provider: Provider name (e.g., 'openai', 'anthropic', 'bedrock').
        api_key: API key for authentication (optional, can use environment variable).
        api_base: Base URL for API endpoint (optional, uses provider default).
        temperature: Default sampling temperature (0.0-2.0).
        max_tokens: Default maximum tokens to generate.
        timeout: Request timeout in seconds.
        rate_limits: Rate limiting configuration.
        retry_config: Retry configuration for failed requests.
        cooldown_config: Cooldown configuration for repeated failures.
        fallback_models: List of fallback model IDs to try if this model fails.
        weight: Weight for weighted routing strategies (higher = more traffic).
        priority: Priority for priority-based routing (higher = preferred).
        tags: Tags for tag-based routing and filtering.
        cost_per_1k_prompt_tokens: Cost per 1000 prompt tokens in USD.
        cost_per_1k_completion_tokens: Cost per 1000 completion tokens in USD.

    Example:
        >>> config = ModelConfig(
        ...     model_id="gpt-4",
        ...     provider="openai",
        ...     temperature=0.7,
        ...     max_tokens=2000,
        ...     rate_limits=RateLimitConfig(requests_per_minute=60),
        ...     fallback_models=["gpt-3.5-turbo"],
        ...     cost_per_1k_prompt_tokens=0.03,
        ...     cost_per_1k_completion_tokens=0.06
        ... )
        >>> config.model_id
        'gpt-4'
    """

    model_id: str
    provider: str
    api_key: str | None = None
    api_base: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    timeout: int = 60

    # Advanced routing features
    rate_limits: RateLimitConfig | None = None
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    cooldown_config: CooldownConfig = Field(default_factory=CooldownConfig)
    fallback_models: list[str] = Field(default_factory=list)

    # Load balancing
    weight: float = 1.0
    priority: int = 0
    tags: list[str] = Field(default_factory=list)

    # Cost tracking
    cost_per_1k_prompt_tokens: float | None = None
    cost_per_1k_completion_tokens: float | None = None


class NimbusConfig(BaseModel):
    """Global Nimbus configuration.

    Top-level configuration for the entire Nimbus platform including logging,
    telemetry, model configurations, plugin settings, and router configuration.

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        enable_telemetry: Whether to enable telemetry collection.
        correlation_id_header: HTTP header name for correlation IDs.
        models: Dictionary of model configurations keyed by model name.
        plugins: Dictionary of plugin configurations keyed by plugin name.
        default_routing_strategy: Default strategy for model routing.
        enable_fallbacks: Whether to enable fallback models.
        enable_rate_limiting: Whether to enable rate limiting.

    Example:
        >>> config = NimbusConfig(
        ...     log_level="INFO",
        ...     enable_telemetry=True,
        ...     models={
        ...         "gpt-4": ModelConfig(
        ...             model_id="gpt-4",
        ...             provider="openai"
        ...         )
        ...     },
        ...     default_routing_strategy="round_robin"
        ... )
        >>> config.log_level
        'INFO'
    """

    log_level: str = "INFO"
    enable_telemetry: bool = True
    correlation_id_header: str = "X-Correlation-ID"
    models: dict[str, ModelConfig] = Field(default_factory=dict)
    plugins: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # Router configuration
    default_routing_strategy: str = "round_robin"
    enable_fallbacks: bool = True
    enable_rate_limiting: bool = True
