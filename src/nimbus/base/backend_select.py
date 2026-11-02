"""Import/construction-time backend selection: built-in vs vendor SDK (Req 17).

Standard library only; nothing runs at import time of this module. A backend is selected
once, at construction, via :func:`select_impl`; the caller keeps the returned
:class:`Selection` for the whole life of the instance (no per-call fallback, no switching).

Resolution order for the requested implementation (``builtin`` | ``sdk``), first hit wins:

1. env ``NIMBUS_<BACKEND>_IMPL``
2. config file (``nimbus.yaml``) ``impl: {<backend>: ...}``
3. env ``NIMBUS_IMPL`` (global default)
4. config file ``impl: {default: ...}``
5. ``builtin``

A vendor SDK is imported only when it is the chosen implementation and was requested
explicitly (levels 1-4 for a backend that has a built-in; any level for SDK-only backends is
*not* probed unless requested explicitly, so their lazy client import is unchanged).
"""

from __future__ import annotations

import importlib
import importlib.metadata
import os
import sys
import warnings
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Any

from nimbus.base.exceptions import ConfigurationError, MissingExtraError
from nimbus.base.sdk_versions import SDK_REFERENCE, SdkRef

IMPLS = ("builtin", "sdk")
ENV_GLOBAL = "NIMBUS_IMPL"
CONFIG_KEY = "impl"
_warned_versions: set[tuple[str, str]] = set()


class SDKSelectionWarning(UserWarning):
    """SDK fell back to the built-in, or installed SDK version differs from the validated one."""


@dataclass(frozen=True)
class Selection:
    """The decision for one backend instance: fixed for the instance's whole life."""

    backend: str
    requested: str  # what configuration asked for (after defaults)
    impl: str  # what is actually used: "builtin" | "sdk"
    explicit: bool  # True when the request came from env/config rather than the default
    sdk: Any = None  # the imported SDK module when impl == "sdk" and it was probed


def env_name(backend: str) -> str:
    return f"NIMBUS_{backend.upper()}_IMPL"


def _norm(value: Any, where: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text not in IMPLS:
        raise ConfigurationError(f"Invalid backend implementation {value!r} from {where}; expected one of {IMPLS}")
    return text


def _config_section(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if config is None:
        # Kept out of module scope so this module stays import-cheap. When ``nimbus.base.config``
        # is already loaded (the normal case once ``nimbus`` is imported) reuse the live module
        # object directly, which avoids issuing an import statement — robust even when a caller has
        # patched ``builtins.__import__`` during backend construction.
        config_mod = sys.modules.get("nimbus.base.config")
        if config_mod is None:
            from nimbus.base import config as _config_cold  # cold path: first touch of the loader

            config_mod = _config_cold
        config = config_mod.load_impl_config()
    section = config.get(CONFIG_KEY) or {}
    if not isinstance(section, Mapping):
        raise ConfigurationError(f"Config key {CONFIG_KEY!r} must be a mapping of backend -> builtin|sdk")
    return section


def resolve_impl(
    backend: str, *, env: Mapping[str, str] | None = None, config: Mapping[str, Any] | None = None
) -> tuple[str, bool]:
    """Return ``(requested, explicit)`` for ``backend`` without importing anything."""
    env = os.environ if env is None else env
    hit = _norm(env.get(env_name(backend)), env_name(backend))
    if hit:
        return hit, True
    section = _config_section(config)
    hit = _norm(section.get(backend), f"{CONFIG_KEY}.{backend}")
    if hit:
        return hit, True
    hit = _norm(env.get(ENV_GLOBAL), ENV_GLOBAL) or _norm(section.get("default"), f"{CONFIG_KEY}.default")
    return (hit, True) if hit else ("builtin", False)


def _check_version(backend: str, ref: SdkRef) -> None:
    """Warn once per (sdk, installed version) when it differs from the validated reference."""
    if ref.version is None:
        return
    try:
        installed = importlib.metadata.version(ref.dist)
    except importlib.metadata.PackageNotFoundError:
        return
    key = (ref.dist, installed)
    if installed != ref.version and key not in _warned_versions:
        _warned_versions.add(key)
        warnings.warn(
            f"Nimbus backend {backend!r} uses SDK {ref.dist} {installed}; the dev-validated version is "
            f"{ref.version}. Still using the installed SDK.",
            SDKSelectionWarning,
            stacklevel=3,
        )


def select_impl(
    backend: str,
    *,
    available: Collection[str] = IMPLS,
    env: Mapping[str, str] | None = None,
    config: Mapping[str, Any] | None = None,
    reference: Mapping[str, SdkRef] | None = None,
) -> Selection:
    """Decide once which implementation ``backend`` uses; see the module docstring.

    ``available`` lists the implementations that exist for the backend. SDK-only backends pass
    ``("sdk",)``: they use the SDK without being probed unless requested explicitly. When the SDK
    is requested but cannot be imported, a backend with a built-in falls back to it with one
    ``SDKSelectionWarning``; an SDK-only backend raises ``MissingExtraError``.
    """
    ref = (reference or SDK_REFERENCE)[backend]
    requested, explicit = resolve_impl(backend, env=env, config=config)
    if requested == "builtin" and "builtin" not in available:
        if env_explicit_backend(backend, env, config):
            raise ConfigurationError(f"Backend {backend!r} has no built-in implementation; only {tuple(available)}")
        return Selection(backend, "sdk", "sdk", False)  # a global default does not apply here
    if requested == "builtin":
        return Selection(backend, requested, "builtin", explicit)
    if "sdk" not in available:
        raise ConfigurationError(f"Backend {backend!r} has no SDK implementation; only {tuple(available)}")
    if not explicit:
        return Selection(backend, requested, "sdk", False)
    try:
        sdk = importlib.import_module(ref.module)
    except ImportError as exc:
        if "builtin" not in available:
            raise MissingExtraError(extra=ref.extra, missing=ref.module, package=ref.dist) from exc
        warnings.warn(
            f"Nimbus backend {backend!r}: SDK {ref.dist!r} was requested but failed to import ({exc}); "
            f"falling back to the built-in implementation for this instance.",
            SDKSelectionWarning,
            stacklevel=2,
        )
        return Selection(backend, requested, "builtin", True)
    _check_version(backend, ref)
    return Selection(backend, requested, "sdk", True, sdk)


def env_explicit_backend(backend: str, env: Mapping[str, str] | None, config: Mapping[str, Any] | None) -> bool:
    """True when ``builtin`` was asked for this backend specifically (not via a global default)."""
    env = os.environ if env is None else env
    if _norm(env.get(env_name(backend)), env_name(backend)):
        return True
    return _norm(_config_section(config).get(backend), f"{CONFIG_KEY}.{backend}") is not None


def _reset_warnings_for_tests() -> None:
    _warned_versions.clear()


__all__ = ["IMPLS", "SDKSelectionWarning", "Selection", "resolve_impl", "select_impl", "env_name"]
