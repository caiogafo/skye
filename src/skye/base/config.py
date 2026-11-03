"""Configuration models and loading system for Skye.

This module provides dataclass models for configuring Skye components including
rate limiting, retries, cooldowns, model configurations, and global settings.
It also includes the ConfigLoader for loading configuration from multiple sources.

Example:
    >>> from skye.base.config import ModelConfig, RateLimitConfig
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
import logging
import os
import re
from pathlib import Path
from typing import Any

from skye.base.exceptions import ConfigurationError, MissingExtraError, ValidationError
from skye.base.lazy_import import missing_extra
from skye.base.validated import Validated, dump, field, validated

# Set up module logger
logger = logging.getLogger(__name__)

# Cache for environment variable substitutions to avoid repeated os.getenv() calls
_env_var_cache: dict[str, str] = {}


def _yaml() -> Any:
    """The PyYAML module, imported when a YAML file is read: it is in the extra `yaml`, not in the core."""
    return missing_extra("yaml", extra="yaml")


def substitute_env_vars(config: dict[str, Any] | list[Any] | str | Any) -> Any:
    """Recursively substitute environment variables in configuration.

    Substitutes ${VAR_NAME} patterns with environment variable values throughout
    the configuration structure. Supports nested dictionaries, lists, and strings.
    Uses caching to avoid repeated os.getenv() calls for the same variable.

    Args:
        config: Configuration data (dict, list, str, or other type).

    Returns:
        Configuration data with environment variables substituted.

    Raises:
        ConfigurationError: If a referenced environment variable is not found.

    Example:
        >>> os.environ["API_KEY"] = "secret-key-123"
        >>> config = {"api_key": "${API_KEY}", "timeout": 30}
        >>> result = substitute_env_vars(config)
        >>> result["api_key"]
        'secret-key-123'
        >>> result["timeout"]
        30
    """
    if isinstance(config, dict):
        # Recursively substitute in dictionary values
        return {key: substitute_env_vars(value) for key, value in config.items()}
    elif isinstance(config, list):
        # Recursively substitute in list items
        return [substitute_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Pattern to match ${VAR_NAME}
        pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1)

            # Check cache first
            if var_name in _env_var_cache:
                logger.debug(f"Using cached value for environment variable: {var_name}")
                return _env_var_cache[var_name]

            # Get from environment
            value = os.getenv(var_name)
            if value is None:
                raise ConfigurationError(
                    f"Environment variable '${{{var_name}}}' not found",
                    details={"variable_name": var_name},
                )

            # Cache the value
            _env_var_cache[var_name] = value
            logger.debug(f"Substituted environment variable: {var_name}")
            return value

        return pattern.sub(replace_var, config)
    else:
        # Return non-string, non-dict, non-list values as-is
        return config


@validated
class RateLimitConfig(Validated):
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


@validated
class RetryConfig(Validated):
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
    retry_on_errors: list[str] = field(
        default_factory=lambda: ["rate_limit", "timeout", "server_error"]
    )


@validated
class CooldownConfig(Validated):
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


@validated
class ModelConfig(Validated):
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
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    cooldown_config: CooldownConfig = field(default_factory=CooldownConfig)
    fallback_models: list[str] = field(default_factory=list)

    # Load balancing
    weight: float = 1.0
    priority: int = 0
    tags: list[str] = field(default_factory=list)

    # Cost tracking
    cost_per_1k_prompt_tokens: float | None = None
    cost_per_1k_completion_tokens: float | None = None


@validated
class SkyeConfig(Validated):
    """Global Skye configuration.

    Top-level configuration for the entire Skye platform including logging,
    telemetry, model configurations, plugin settings, and router configuration.

    Attributes:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        enable_telemetry: Whether to enable telemetry collection.
        correlation_id_header: HTTP header name for correlation IDs.
        component_log_levels: Log level per component, keyed by the component name (for example
            ``{"router": "DEBUG", "models": "WARNING"}``); a component not listed uses ``log_level``.
        models: Dictionary of model configurations keyed by model name.
        plugins: Dictionary of plugin configurations keyed by plugin name.
        default_routing_strategy: Default strategy for model routing.
        enable_fallbacks: Whether to enable fallback models.
        enable_rate_limiting: Whether to enable rate limiting.

    Example:
        >>> config = SkyeConfig(
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
    component_log_levels: dict[str, str] = field(default_factory=dict)
    models: dict[str, ModelConfig] = field(default_factory=dict)
    plugins: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Router configuration
    default_routing_strategy: str = "round_robin"
    enable_fallbacks: bool = True
    enable_rate_limiting: bool = True

    def __post_init__(self) -> None:
        """Validate the fields, then that every component log level is a standard level name."""
        super().__post_init__()
        for component, level in self.component_log_levels.items():
            if not isinstance(logging.getLevelName(level.upper()), int):
                raise ValidationError(
                    f"Unknown log level {level!r} for component {component!r}",
                    field="component_log_levels",
                    value={component: level},
                )

    def level_for(self, component: str) -> str:
        """The log level of a component: its own if set, else the global ``log_level``.

        Args:
            component: The component name (``models``, ``router``, ``tools``, ...).
        """
        return self.component_log_levels.get(component, self.log_level).upper()

    def apply_log_levels(self) -> None:
        """Set the level of the ``skye`` logger and of each listed component logger (``skye.<component>``)."""
        logging.getLogger("skye").setLevel(self.log_level.upper())
        for component in self.component_log_levels:
            logging.getLogger(f"skye.{component}").setLevel(self.level_for(component))


@validated
class RouterConfig(Validated):
    """Complete router configuration from YAML.

    This model represents a complete router configuration that can be loaded
    from YAML files. It includes routes, fallbacks, retry policies, and other
    router settings.

    Attributes:
        routes: List of route configurations with aliases and targets.
        fallbacks: List of fallback configurations defining fallback chains.
        retry_policies: List of retry policy configurations per error type.
        allowed_fails_policies: List of allowed fails policies before cooldown.
        strategy: Default routing strategy for the router.
        cooldown_seconds: Default cooldown duration for failed models.
        enable_pre_call_checks: Whether to enable pre-call rate limit checks.

    Example:
        >>> config = RouterConfig(
        ...     routes=[
        ...         {
        ...             "alias": "gpt-3.5-turbo",
        ...             "targets": [
        ...                 {
        ...                     "model": "gpt-3.5-turbo",
        ...                     "provider": "openai",
        ...                     "api_key": "${OPENAI_API_KEY}",
        ...                     "tpm": 200000,
        ...                     "rpm": 2000
        ...                 }
        ...             ],
        ...             "strategy": "rate_limit_aware"
        ...         }
        ...     ],
        ...     fallbacks=[
        ...         {
        ...             "primary": "gpt-4",
        ...             "fallbacks": ["gpt-3.5-turbo"]
        ...         }
        ...     ]
        ... )
    """

    routes: list[dict[str, Any]] = field(default_factory=list, description="Route configurations")
    fallbacks: list[dict[str, Any]] = field(
        default_factory=list, description="Fallback configurations"
    )
    retry_policies: list[dict[str, Any]] = field(
        default_factory=list, description="Retry policy configurations"
    )
    allowed_fails_policies: list[dict[str, Any]] = field(
        default_factory=list, description="Allowed fails policy configurations"
    )
    strategy: str = field("round_robin", description="Default routing strategy")
    cooldown_seconds: float = field(60.0, ge=0.0, description="Cooldown duration in seconds")
    enable_pre_call_checks: bool = field(
        True, description="Enable pre-call rate limit checks"
    )


def _validation_errors(error: ValidationError) -> list[dict[str, Any]]:
    """The validation failure as a list of ``{type, loc, msg, input}`` entries (``loc`` is the field path)."""
    path = str(error.details.get("path", ""))
    loc = [part.strip("'\"") for part in re.split(r"[.\[\]]+", path) if part][1:]
    return [
        {
            "type": "value_error",
            "loc": loc or [str(error.details.get("field", ""))],
            "msg": error.message,
            "input": error.details.get("value"),
        }
    ]


def load_router_config(yaml_path: str | Path) -> dict[str, Any]:
    """Load router configuration from YAML file with environment variable substitution.

    This function loads a router configuration from a YAML file and applies
    environment variable substitution to all string values. The configuration
    is validated against the RouterConfig model.

    Args:
        yaml_path: Path to the YAML configuration file.

    Returns:
        Dictionary containing the router configuration with environment variables substituted.

    Raises:
        ConfigurationError: If the file doesn't exist, can't be parsed, or fails validation.

    Example:
        >>> # Load router config from YAML
        >>> config = load_router_config("router_config.yaml")
        >>> print(config["routes"])
        [{'alias': 'gpt-3.5-turbo', 'targets': [...]}]
    """
    yaml_path = Path(yaml_path) if isinstance(yaml_path, str) else yaml_path

    if not yaml_path.exists():
        raise ConfigurationError(
            f"Router configuration file not found: {yaml_path}",
            details={"path": str(yaml_path)},
        )

    yaml = _yaml()
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Failed to parse YAML configuration file: {yaml_path}",
            details={"path": str(yaml_path), "error": str(e)},
        ) from e
    except Exception as e:
        raise ConfigurationError(
            f"Failed to read configuration file: {yaml_path}",
            details={"path": str(yaml_path), "error": str(e)},
        ) from e

    # Handle empty files
    if data is None:
        raise ConfigurationError(
            "Router configuration file is empty",
            details={"path": str(yaml_path)},
        )

    if not isinstance(data, dict):
        raise ConfigurationError(
            "Router configuration file must contain a dictionary/object at root level",
            details={"path": str(yaml_path), "type": type(data).__name__},
        )

    # Apply environment variable substitution
    substituted_data = substitute_env_vars(data)

    # Validate against RouterConfig model
    try:
        router_config = RouterConfig.from_dict(substituted_data)
        # Return as dict for compatibility with router initialization
        dumped: dict[str, Any] = dump(router_config)
        return dumped
    except ValidationError as e:
        raise ConfigurationError(
            "Router configuration validation failed",
            details={
                "path": str(yaml_path),
                "validation_errors": _validation_errors(e),
            },
        ) from e


#: The Skye-prefixed variables that set configuration values (SKYE_CONFIG selects the file).
ENV_CONFIG_VARS = frozenset({"SKYE_LOG_LEVEL", "SKYE_ENABLE_TELEMETRY"})
#: All Skye-prefixed environment variables: exactly three.
ALL_ENV_VARS = ENV_CONFIG_VARS | {"SKYE_CONFIG"}


class ConfigLoader:
    """Loads Skye configuration from multiple sources.

    ConfigLoader supports loading configuration from three sources with the
    following precedence (highest to lowest):
    1. Code overrides (passed as dict to load())
    2. Environment variables (SKYE_ prefix)
    3. Configuration files (YAML or JSON)

    The loader merges configuration from all sources, with higher precedence
    sources overriding lower precedence ones.

    Example:
        >>> # Load from file only
        >>> config = ConfigLoader.load(config_path=Path("skye.yaml"))
        >>>
        >>> # Load with environment variables
        >>> os.environ["SKYE_LOG_LEVEL"] = "DEBUG"
        >>> config = ConfigLoader.load()
        >>>
        >>> # Load with code overrides
        >>> config = ConfigLoader.load(overrides={"log_level": "ERROR"})
        >>>
        >>> # Load from all sources
        >>> config = ConfigLoader.load(
        ...     config_path=Path("skye.yaml"),
        ...     overrides={"enable_telemetry": False}
        ... )
    """

    @staticmethod
    def load(
        config_path: Path | None = None, overrides: dict[str, Any] | None = None
    ) -> SkyeConfig:
        """Load configuration from multiple sources with precedence.

        Loads configuration from file, environment variables, and code overrides,
        applying them in order of precedence: code > environment > file.

        Args:
            config_path: Optional path to YAML or JSON configuration file.
            overrides: Optional dictionary of configuration values to override.

        Returns:
            SkyeConfig: Validated configuration object.

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

        # 1. Load from file (lowest precedence); SKYE_CONFIG names the file when no path is given
        if config_path is None and os.environ.get("SKYE_CONFIG"):
            config_path = Path(os.environ["SKYE_CONFIG"])
        if config_path:
            try:
                config_data = ConfigLoader._load_from_file(config_path)
            except MissingExtraError:
                raise  # already says what to install (the extra `yaml`)
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
            # Apply environment variable substitution to overrides
            substituted_overrides = substitute_env_vars(overrides)
            config_data.update(substituted_overrides)

        # Validate and create SkyeConfig
        try:
            config: SkyeConfig = SkyeConfig.from_dict(config_data)
            return config
        except ValidationError as e:
            raise ConfigurationError(
                "Configuration validation failed",
                details={"validation_errors": _validation_errors(e)},
            ) from e

    @staticmethod
    def _load_from_file(config_path: Path) -> dict[str, Any]:
        """Load configuration from a YAML or JSON file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Dictionary containing configuration data with environment variables substituted.

        Raises:
            ConfigurationError: If file doesn't exist, can't be read, or has invalid format.
        """
        if not config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}",
                details={"path": str(config_path)},
            )

        # YAML needs the extra `yaml`; JSON needs nothing. The parse error types are those of the format being read.
        yaml = _yaml() if config_path.suffix in [".yaml", ".yml"] else None
        yaml_error: type[Exception] = yaml.YAMLError if yaml is not None else ValueError
        try:
            with open(config_path) as f:
                if yaml is not None:
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

            # Apply environment variable substitution
            substituted: dict[str, Any] = substitute_env_vars(data)
            return substituted

        except (yaml_error, json.JSONDecodeError) as e:
            raise ConfigurationError(
                f"Failed to parse configuration file: {config_path}",
                details={"path": str(config_path), "error": str(e)},
            ) from e

    @staticmethod
    def _load_from_env() -> dict[str, Any]:
        """Load configuration from environment variables.

        Reads the Skye-prefixed variables that set configuration values and converts them
        to configuration keys. The prefix is removed and the key is lowercased. There are
        exactly three Skye-prefixed variables (Requirement 23): SKYE_LOG_LEVEL and
        SKYE_ENABLE_TELEMETRY (read here) and SKYE_CONFIG (names the config file, read in
        ``load``). Provider credentials never come from a Skye-prefixed variable.

        For example:
            SKYE_LOG_LEVEL=DEBUG -> log_level: "DEBUG"
            SKYE_ENABLE_TELEMETRY=false -> enable_telemetry: False

        Returns:
            Dictionary containing configuration data from environment variables.
        """
        config_data: dict[str, Any] = {}

        for key, value in os.environ.items():
            if key in ENV_CONFIG_VARS:
                # Remove SKYE_ prefix and convert to lowercase
                config_key = key[len("SKYE_"):].lower()

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
