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

import json
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from nimbus.exceptions import ConfigurationError


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


class ConfigLoader:
    """Loads Nimbus configuration from multiple sources.

    ConfigLoader supports loading configuration from three sources with the
    following precedence (highest to lowest):
    1. Code overrides (passed as dict to load())
    2. Environment variables (NIMBUS_ prefix)
    3. Configuration files (YAML or JSON)

    The loader merges configuration from all sources, with higher precedence
    sources overriding lower precedence ones.

    Example:
        >>> # Load from file only
        >>> config = ConfigLoader.load(config_path=Path("nimbus.yaml"))
        >>>
        >>> # Load with environment variables
        >>> os.environ["NIMBUS_LOG_LEVEL"] = "DEBUG"
        >>> config = ConfigLoader.load()
        >>>
        >>> # Load with code overrides
        >>> config = ConfigLoader.load(overrides={"log_level": "ERROR"})
        >>>
        >>> # Load from all sources
        >>> config = ConfigLoader.load(
        ...     config_path=Path("nimbus.yaml"),
        ...     overrides={"enable_telemetry": False}
        ... )
    """

    @staticmethod
    def load(
        config_path: Path | None = None, overrides: dict[str, Any] | None = None
    ) -> NimbusConfig:
        """Load configuration from multiple sources with precedence.

        Loads configuration from file, environment variables, and code overrides,
        applying them in order of precedence: code > environment > file.

        Args:
            config_path: Optional path to YAML or JSON configuration file.
            overrides: Optional dictionary of configuration values to override.

        Returns:
            NimbusConfig: Validated configuration object.

        Raises:
            ConfigurationError: If configuration file cannot be read, parsed,
                or if configuration values fail validation.

        Example:
            >>> config = ConfigLoader.load(
            ...     config_path=Path("config.yaml"),
            ...     overrides={"log_level": "DEBUG"}
            ... )
            >>> config.log_level
            'DEBUG'
        """
        config_data: dict[str, Any] = {}

        # 1. Load from file (lowest precedence)
        if config_path:
            try:
                config_data = ConfigLoader._load_from_file(config_path)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load configuration from file: {config_path}",
                    details={"path": str(config_path), "error": str(e)},
                ) from e

        # 2. Override with environment variables (medium precedence)
        env_config = ConfigLoader._load_from_env()
        config_data.update(env_config)

        # 3. Apply code overrides (highest precedence)
        if overrides:
            config_data.update(overrides)

        # Validate and create NimbusConfig
        try:
            return NimbusConfig(**config_data)
        except PydanticValidationError as e:
            raise ConfigurationError(
                "Configuration validation failed",
                details={"validation_errors": e.errors()},
            ) from e

    @staticmethod
    def _load_from_file(config_path: Path) -> dict[str, Any]:
        """Load configuration from a YAML or JSON file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Dictionary containing configuration data.

        Raises:
            ConfigurationError: If file doesn't exist, can't be read, or has invalid format.
        """
        if not config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}",
                details={"path": str(config_path)},
            )

        try:
            with open(config_path) as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                elif config_path.suffix == ".json":
                    data = json.load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format: {config_path.suffix}",
                        details={"path": str(config_path), "suffix": config_path.suffix},
                    )

            # Handle empty files
            if data is None:
                return {}

            if not isinstance(data, dict):
                raise ConfigurationError(
                    "Configuration file must contain a dictionary/object at root level",
                    details={"path": str(config_path), "type": type(data).__name__},
                )

            return data

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(
                f"Failed to parse configuration file: {config_path}",
                details={"path": str(config_path), "error": str(e)},
            ) from e

    @staticmethod
    def _load_from_env() -> dict[str, Any]:
        """Load configuration from environment variables.

        Reads all environment variables with NIMBUS_ prefix and converts them
        to configuration keys. The prefix is removed and the key is lowercased.

        For example:
            NIMBUS_LOG_LEVEL=DEBUG -> log_level: "DEBUG"
            NIMBUS_ENABLE_TELEMETRY=false -> enable_telemetry: False

        Returns:
            Dictionary containing configuration data from environment variables.
        """
        config_data: dict[str, Any] = {}

        for key, value in os.environ.items():
            if key.startswith("NIMBUS_"):
                # Remove NIMBUS_ prefix and convert to lowercase
                config_key = key[7:].lower()

                # Try to parse boolean values
                if value.lower() in ["true", "false"]:
                    config_data[config_key] = value.lower() == "true"
                # Try to parse numeric values
                elif value.isdigit():
                    config_data[config_key] = int(value)
                elif value.replace(".", "", 1).isdigit():
                    config_data[config_key] = float(value)
                else:
                    config_data[config_key] = value

        return config_data
