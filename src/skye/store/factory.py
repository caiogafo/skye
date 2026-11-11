"""Create a backend by name and add backends from outside Skye (Requirement 12.6, decision D98).

``backend(name, **config)`` builds one of the registered backends, in the style of ``provider(name,
**config)``. The six of Skye are
registered by module path, so naming one imports only its module, and its driver only on first use.
``register_backend`` adds any
other backend (a class or a function that returns one) without changing Skye; check it with
``skye.store.conformance``.

Example:
    >>> from skye.store import backend, register_backend, InMemoryBackend
    >>> type(backend("memory")).__name__
    'InMemoryBackend'
    >>> register_backend("scratch", lambda **config: InMemoryBackend())
    >>> type(backend("scratch")).__name__
    'InMemoryBackend'

Raises: ``ConfigurationError`` for an unknown name (listing the known ones) or a name registered
    twice without ``replace=True``.
Missing: not applicable.
Concurrency: register backends at start-up; the registry is a plain ``dict`` of this process.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from skye.base.exceptions import ConfigurationError
from skye.base.interfaces.storage import StorageBackend

Factory = Callable[..., StorageBackend]

_BUILTIN: dict[str, str] = {
    "memory": "skye.store.memory:InMemoryBackend",
    "file": "skye.store.file:FileSystemBackend",
    "dynamodb": "skye.store.dynamodb:DynamoDBBackend",
    "redis": "skye.store.redis:RedisBackend",
    "valkey": "skye.store.redis:RedisBackend",  # the same backend (D102)
    "postgres": "skye.store.postgres:PostgreSQLBackend",
    "durable_function": "skye.store.durable_function:DurableFunctionBackend",
}
_REGISTERED: dict[str, Factory] = {}


def register_backend(name: str, factory: Factory, *, replace: bool = False) -> None:
    """Register ``factory`` under ``name``; ``factory(**config)`` returns the backend.

    Args:
        name: The name passed to ``backend``.
        factory: A backend class, or a function taking the configuration as keyword arguments.
        replace: Allow replacing a name already registered (a built-in one included).
    """
    if not isinstance(name, str) or not name:
        raise ConfigurationError("a backend name must be a non-empty string")
    if not callable(factory):
        raise ConfigurationError(f"the factory of backend {name!r} is not callable")
    if not replace and (name in _REGISTERED or name in _BUILTIN):
        raise ConfigurationError(
            f"a backend named {name!r} is already registered; pass replace=True to replace it"
        )
    _REGISTERED[name] = factory


def available_backends() -> list[str]:
    """The names ``backend`` accepts, sorted."""
    return sorted(set(_BUILTIN) | set(_REGISTERED))


def _resolve(name: str) -> Factory:
    if name in _REGISTERED:
        return _REGISTERED[name]
    if name in _BUILTIN:
        module_name, attribute = _BUILTIN[name].split(":")
        factory: Factory = getattr(importlib.import_module(module_name), attribute)
        return factory
    raise ConfigurationError(
        f"unknown store backend {name!r}; known: {', '.join(available_backends())}"
    )


def backend(name: str, **config: Any) -> StorageBackend:
    """Build the backend registered as ``name`` with ``config`` as keyword arguments.

    Built-in names: ``memory``, ``file``, ``dynamodb``, ``redis``, ``postgres``,
    ``durable_function``.
    """
    return _resolve(name)(**config)


__all__ = ["available_backends", "backend", "register_backend"]
