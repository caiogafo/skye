"""Configuration loader interface for loading Skye configuration.

This module defines the abstract interface for loading configuration from
multiple sources with precedence handling.

Raises: ConfigurationError when a file is absent, malformed or the merged values do not validate.
Missing: an absent environment variable falls back to the next source and to the default; an absent file raises.
Concurrency: loading is read-only and safe to repeat; ``skye.config.ConfigLoader`` satisfies this Port structurally, with a static ``load``.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from skye.base.config import SkyeConfig


class ConfigLoaderInterface(ABC):
    """Abstract interface for configuration loading.

    This interface defines the contract for loading configuration from
    multiple sources (files, environment variables, code overrides) with
    proper precedence handling.

    Example:
        >>> class MyConfigLoader(ConfigLoaderInterface):
        ...     def load(self, config_path=None, overrides=None):
        ...         # Implementation
        ...         return SkyeConfig()
    """

    @abstractmethod
    def load(
        self, config_path: Path | None = None, overrides: dict[str, Any] | None = None
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
            ConfigurationError: If configuration cannot be loaded or validated.

        Example:
            >>> config = loader.load(
            ...     config_path=Path("config.yaml"),
            ...     overrides={"log_level": "DEBUG"}
            ... )
        """
        pass
