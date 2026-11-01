"""Configuration loader interface for loading Nimbus configuration.

This module defines the abstract interface for loading configuration from
multiple sources with precedence handling.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from nimbus.base.config import NimbusConfig


class ConfigLoaderInterface(ABC):
    """Abstract interface for configuration loading.

    This interface defines the contract for loading configuration from
    multiple sources (files, environment variables, code overrides) with
    proper precedence handling.

    Example:
        >>> class MyConfigLoader(ConfigLoaderInterface):
        ...     def load(self, config_path=None, overrides=None):
        ...         # Implementation
        ...         return NimbusConfig()
        ...
        ...     def load_from_file(self, config_path):
        ...         return {}
        ...
        ...     def load_from_env(self):
        ...         return {}
    """

    @abstractmethod
    def load(
        self, config_path: Path | None = None, overrides: dict[str, Any] | None = None
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
            ConfigurationError: If configuration cannot be loaded or validated.

        Example:
            >>> config = loader.load(
            ...     config_path=Path("config.yaml"),
            ...     overrides={"log_level": "DEBUG"}
            ... )
        """
        pass

    @abstractmethod
    def load_from_file(self, config_path: Path) -> dict[str, Any]:
        """Load configuration from a YAML or JSON file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Dictionary containing configuration data.

        Raises:
            ConfigurationError: If file doesn't exist or has invalid format.

        Example:
            >>> data = loader.load_from_file(Path("config.yaml"))
        """
        pass

    @abstractmethod
    def load_from_env(self) -> dict[str, Any]:
        """Load configuration from environment variables.

        Reads all environment variables with NIMBUS_ prefix and converts them
        to configuration keys.

        Returns:
            Dictionary containing configuration data from environment variables.

        Example:
            >>> data = loader.load_from_env()
        """
        pass
