"""Thin lazy-import helper over stdlib ``importlib``.

Attempts the import at first use and maps absence of an optional dependency to
``MissingExtraError``, which names the Extra to install. Stdlib-only.
"""

import importlib
from types import ModuleType

from skye.base.exceptions import MissingExtraError


def missing_extra(module: str, extra: str, package: str | None = None) -> ModuleType:
    """Import ``module`` or raise ``MissingExtraError`` naming ``extra``."""
    try:
        return importlib.import_module(module)
    except ImportError as e:  # includes ModuleNotFoundError
        raise MissingExtraError(extra=extra, missing=module, package=package) from e


__all__ = ["missing_extra"]
