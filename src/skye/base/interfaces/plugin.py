"""Plugin interface for extensibility.

This module defines the abstract interface for plugins that extend Skye
functionality with lifecycle management.
"""

from abc import ABC, abstractmethod
from typing import Any


class PluginInterface(ABC):
    """Abstract interface for plugins.

    This interface defines the contract for plugin implementations with
    lifecycle management (initialize/shutdown) and metadata.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin.

        Called when the plugin is loaded. Use this to set up resources,
        connections, or perform any necessary initialization.

        Raises:
            PluginInitializationError: If initialization fails.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin.

        Called when the plugin is being unloaded. Use this to clean up
        resources, close connections, or perform any necessary cleanup.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """Return plugin metadata.

        Returns:
            Dictionary containing plugin metadata such as name, version,
            description, and capabilities.
        """
        pass
