"""Registry Port: route registry and provider registry contracts.

Single home for the registry contracts (structure task 4.6, Overlap A,
Requirement 10.1). The route registry manages model aliases and load balancing;
the provider registry discovers and instantiates providers. Consumers (e.g. the
router) reach the implementation in ``models`` only through this Port.
"""

import importlib
from abc import ABC, abstractmethod
from typing import Any

_provider_registry: Any = None


def set_provider_registry(registry: Any) -> None:
    """Install the provider registry used by consumers of the Port."""
    global _provider_registry
    _provider_registry = registry


def get_provider_registry() -> Any:
    """Return the installed provider registry (a ProviderRegistryInterface).

    Falls back to lazily loading the default implementation in ``models`` by
    dotted name, so ``base`` and consumers carry no static dependency on it.
    """
    if _provider_registry is None:
        mod = importlib.import_module("skye.models.registry")
        return mod.ProviderRegistry
    return _provider_registry


class ProviderRegistryInterface(ABC):
    """Abstract contract for registering and instantiating providers."""

    @classmethod
    @abstractmethod
    def register_model_provider(cls, name: str, provider_class: type) -> None:
        """Register a model provider class under ``name``."""

    @classmethod
    @abstractmethod
    def register_embedding_provider(cls, name: str, provider_class: type) -> None:
        """Register an embedding provider class under ``name``."""

    @classmethod
    @abstractmethod
    def get_model_provider(cls, name: str, **config: Any) -> Any:
        """Instantiate a model provider by name."""

    @classmethod
    @abstractmethod
    def get_embedding_provider(cls, name: str, **config: Any) -> Any:
        """Instantiate an embedding provider by name."""

    @classmethod
    @abstractmethod
    def list_model_providers(cls) -> list[str]:
        """List registered model provider names."""

    @classmethod
    @abstractmethod
    def list_embedding_providers(cls) -> list[str]:
        """List registered embedding provider names."""


class RouteRegistryInterface(ABC):
    """Abstract interface for route registry.

    This interface defines the contract for managing route configurations
    that map aliases to one or more model targets with load balancing.

    Example:
        >>> class MyRouteRegistry(RouteRegistryInterface):
        ...     def resolve_model(self, alias):
        ...         return "gpt-4"
        ...
        ...     def is_alias(self, name):
        ...         return name in self.routes
        ...
        ...     def list_aliases(self):
        ...         return ["gpt-3.5-turbo", "gpt-4"]
    """

    @abstractmethod
    def resolve_model(self, alias: str) -> str:
        """Resolve an alias to an actual model identifier.

        If the alias has multiple targets, selects one based on
        the routing strategy. Otherwise, returns the alias unchanged.

        Args:
            alias: Model alias or actual model name.

        Returns:
            Actual model identifier to use.

        Example:
            >>> model = registry.resolve_model("gpt-3.5-turbo")
            >>> print(model)
            'azure/chatgpt-v-2'
        """
        pass

    @abstractmethod
    def is_alias(self, name: str) -> bool:
        """Check if a name is a registered alias.

        Args:
            name: Name to check.

        Returns:
            True if name is a registered alias.

        Example:
            >>> if registry.is_alias("gpt-3.5-turbo"):
            ...     model = registry.resolve_model("gpt-3.5-turbo")
        """
        pass

    @abstractmethod
    def list_aliases(self) -> list[str]:
        """List all registered aliases.

        Returns:
            List of alias names.

        Example:
            >>> aliases = registry.list_aliases()
            >>> print(aliases)
            ['gpt-3.5-turbo', 'gpt-4']
        """
        pass

    @abstractmethod
    def get_route(self, alias: str) -> Any | None:
        """Get the route configuration for an alias.

        Args:
            alias: Alias name.

        Returns:
            Route configuration if alias exists, None otherwise.

        Example:
            >>> route = registry.get_route("gpt-3.5-turbo")
            >>> if route:
            ...     print(len(route.targets))
        """
        pass

    @abstractmethod
    def get_target(self, alias: str, model: str) -> Any | None:
        """Get a specific target by alias and model identifier.

        Args:
            alias: Route alias.
            model: Actual model identifier.

        Returns:
            Model target if found, None otherwise.

        Example:
            >>> target = registry.get_target("gpt-3.5-turbo", "azure/chatgpt-v-2")
            >>> if target:
            ...     print(target.api_key)
        """
        pass
