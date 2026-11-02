"""Temporary shim: the lazy-import mechanism now lives in ``skye.base``.

``missing_extra`` / ``MissingExtraError`` are the canonical helpers. The
``LazyImporter`` facade is kept here, unchanged in behavior, for call sites not
yet migrated; it delegates to ``missing_extra`` (``MissingExtraError`` is an
``ImportError`` subclass, so the old contract holds).
"""

import importlib.util
import sys
from typing import Any

from skye.base.exceptions import MissingExtraError
from skye.base.lazy_import import missing_extra


class LazyImporter:
    """Backward-compatible facade over ``skye.base.lazy_import.missing_extra``."""

    @staticmethod
    def import_module(
        module_name: str,
        package_name: str | None = None,
        install_extra: str | None = None,
    ) -> Any:
        """Import a module; raise ImportError (MissingExtraError) if absent."""
        return missing_extra(
            module_name, extra=install_extra or module_name, package=package_name
        )

    @staticmethod
    def is_available(module_name: str) -> bool:
        """Check if a module is available without importing it."""
        if module_name in sys.modules:
            return True
        return importlib.util.find_spec(module_name) is not None


__all__ = ["LazyImporter", "MissingExtraError", "missing_extra"]
