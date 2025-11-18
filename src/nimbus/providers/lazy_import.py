"""Lazy import utility for optional provider dependencies.

This module provides utilities for lazily importing provider SDKs only when they are
actually needed. This allows Nimbus to support multiple providers without requiring
all their dependencies to be installed.

The LazyImporter also detects pre-installed libraries (e.g., boto3 in AWS Lambda)
and uses them without requiring them as explicit dependencies.
"""

import importlib
import importlib.util
import sys
from typing import Any


class LazyImporter:
    """Lazy import utility for optional dependencies.

    This class provides methods to import modules only when needed and to check
    if modules are available without actually importing them.

    Example:
        >>> # Import a module with helpful error message
        >>> openai = LazyImporter.import_module("openai", install_extra="openai")
        >>>
        >>> # Check if a module is available
        >>> if LazyImporter.is_available("boto3"):
        ...     boto3 = LazyImporter.import_module("boto3")
    """

    @staticmethod
    def import_module(
        module_name: str,
        package_name: str | None = None,
        install_extra: str | None = None
    ) -> Any:
        """Lazily import a module, providing helpful error if not installed.

        This method attempts to import a module and provides clear installation
        instructions if the module is not available.

        Args:
            module_name: The module to import (e.g., 'openai', 'boto3')
            package_name: The package name for pip (e.g., 'openai').
                         Defaults to module_name if not provided.
            install_extra: The nimbus extra to install (e.g., 'openai').
                          Defaults to module_name if not provided.

        Returns:
            The imported module.

        Raises:
            ImportError: If the module is not installed, with installation instructions.

        Example:
            >>> openai = LazyImporter.import_module("openai", install_extra="openai")
            >>> client = openai.OpenAI(api_key="...")
        """
        try:
            return importlib.import_module(module_name)
        except ImportError as e:
            pkg = package_name or module_name
            extra = install_extra or module_name

            error_message = (
                f"The '{module_name}' package is required but not installed.\n"
                f"Install it with: pip install {pkg}\n"
                f"Or install the nimbus extra: pip install nimbus[{extra}]"
            )

            raise ImportError(error_message) from e

    @staticmethod
    def is_available(module_name: str) -> bool:
        """Check if a module is available without importing it.

        This method checks if a module can be imported without actually importing it.
        It first checks if the module is already loaded in sys.modules, then uses
        importlib.util.find_spec to check if it can be found.

        Args:
            module_name: The module to check (e.g., 'openai', 'boto3')

        Returns:
            True if the module is available, False otherwise.

        Example:
            >>> if LazyImporter.is_available("boto3"):
            ...     print("boto3 is available")
            ... else:
            ...     print("boto3 is not installed")
        """
        # Check if already loaded
        if module_name in sys.modules:
            return True

        # Check if can be found
        spec = importlib.util.find_spec(module_name)
        return spec is not None


__all__ = ["LazyImporter"]
