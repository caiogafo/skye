"""Decorator for creating capabilities from functions.

This module provides the @capability decorator that allows developers to
easily create capabilities from Python functions.
"""

from collections.abc import Callable
from typing import Any, TypeVar, overload

F = TypeVar("F", bound=Callable[..., Any])


@overload
def capability(func: F) -> F: ...


@overload
def capability(
    *,
    name: str | None = None,
    description: str | None = None,
) -> Callable[[F], F]: ...


def capability(
    func: F | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> F | Callable[[F], F]:
    """Decorator to create a capability from a function.

    Can be used with or without arguments:

    @capability
    def get_weather(location: str) -> str:
        '''Get weather for a location'''
        return f"Weather for {location}"

    @capability(name="custom_name", description="Custom description")
    def get_weather(location: str) -> str:
        return f"Weather for {location}"

    Args:
        func: The function to decorate (when used without arguments)
        name: Optional override for capability name
        description: Optional override for capability description

    Returns:
        The decorated function (which is now a LocalFunctionCapability)
    """
    # Import here to avoid circular imports
    from skye.tools.local_function import LocalFunctionCapability

    def decorator(f: F) -> F:
        # Create the capability wrapper using LocalFunctionCapability
        capability_instance = LocalFunctionCapability(f, name=name, description=description)
        # Return the capability instance, typed as F for compatibility
        return capability_instance  # type: ignore

    # Called with arguments: @capability(name="...", description="...")
    if func is None:
        return decorator

    # Called without arguments: @capability
    return decorator(func)
