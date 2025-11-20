"""Local function capability implementation.

This module provides the LocalFunctionCapability class for wrapping Python
functions as capabilities that can be invoked by LLMs.
"""

import asyncio
import inspect
import logging
from functools import partial
from typing import Any, Callable

from nimbus.capabilities.exceptions import CapabilityValidationError
from nimbus.capabilities.interface import CapabilityInterface
from nimbus.capabilities.schema import CapabilitySchema

logger = logging.getLogger(__name__)


class LocalFunctionCapability(CapabilityInterface):
    """Capability wrapping a local Python function.

    Automatically extracts schema from function signature and type hints.
    Supports both synchronous and asynchronous functions. Validates arguments
    against the schema before execution.

    Attributes:
        func: The wrapped Python function
        name: The capability name (defaults to function name)
        description: The capability description (defaults to function docstring)

    Example:
        >>> def get_weather(location: str) -> str:
        ...     '''Get weather for a location.'''
        ...     return f"Weather for {location}"
        >>>
        >>> capability = LocalFunctionCapability(get_weather)
        >>> schema = capability.get_schema()
        >>> result = capability.execute(location="New York")
        >>> # For async functions:
        >>> async def async_get_weather(location: str) -> str:
        ...     '''Get weather asynchronously.'''
        ...     return f"Weather for {location}"
        >>>
        >>> async_capability = LocalFunctionCapability(async_get_weather)
        >>> result = await async_capability.aexecute(location="New York")
    """

    def __init__(
        self,
        func: Callable[..., Any],
        name: str | None = None,
        description: str | None = None,
        schema_override: CapabilitySchema | None = None,
    ) -> None:
        """Initialize LocalFunctionCapability.

        Args:
            func: The Python function to wrap as a capability
            name: Optional override for capability name (defaults to function name)
            description: Optional override for capability description
                (defaults to first line of function docstring)
            schema_override: Optional complete schema override. If provided,
                this schema will be used instead of extracting from the function.

        Raises:
            CapabilityValidationError: If func is not callable
        """
        if not callable(func):
            raise CapabilityValidationError(
                f"func must be callable, got {type(func).__name__}",
                capability_name=name or "<unknown>",
            )

        self.func = func
        self._name = name or func.__name__
        self._description = description or self._extract_docstring(func)
        self._schema_override = schema_override
        self._is_async = inspect.iscoroutinefunction(func)

    def get_schema(self) -> CapabilitySchema:
        """Get the schema for this capability.

        If schema_override was provided during initialization, returns that.
        Otherwise, automatically extracts schema from the function signature
        and type hints.

        Returns:
            CapabilitySchema: The schema definition for this capability

        Raises:
            CapabilityValidationError: If schema extraction fails
        """
        if self._schema_override:
            return self._schema_override

        try:
            sig = inspect.signature(self.func)
            parameters = self._extract_parameters(sig)
            returns = self._extract_return_type(sig)

            return CapabilitySchema(
                name=self._name,
                description=self._description or "No description provided",
                parameters=parameters,
                returns=returns,
            )
        except Exception as e:
            raise CapabilityValidationError(
                f"Failed to extract schema from function '{self._name}': {e}",
                capability_name=self._name,
                original_error=str(e),
            ) from e

    def execute(self, **kwargs: Any) -> Any:
        """Execute the function synchronously.

        Validates arguments against the schema before execution.

        Args:
            **kwargs: Arguments to pass to the function. Must match the
                parameters defined in the capability schema.

        Returns:
            The function's return value

        Raises:
            CapabilityValidationError: If arguments don't match schema
            CapabilityValidationError: If the function is async
            Exception: Any exception raised by the wrapped function
        """
        if self._is_async:
            raise CapabilityValidationError(
                f"Cannot call async function '{self._name}' synchronously. "
                "Use aexecute() instead.",
                capability_name=self._name,
            )

        # Validate arguments against schema
        self._validate_arguments(kwargs)

        try:
            result = self.func(**kwargs)
            logger.debug(
                "Local function executed successfully",
                extra={
                    "capability_name": self._name,
                    "arguments": kwargs,
                },
            )
            return result
        except Exception as e:
            logger.error(
                "Local function execution failed",
                extra={
                    "capability_name": self._name,
                    "arguments": kwargs,
                    "error": str(e),
                },
            )
            raise

    async def aexecute(self, **kwargs: Any) -> Any:
        """Execute the function asynchronously.

        Validates arguments against the schema before execution. Works with
        both async and sync functions (sync functions are run in a thread pool).

        Args:
            **kwargs: Arguments to pass to the function. Must match the
                parameters defined in the capability schema.

        Returns:
            The function's return value

        Raises:
            CapabilityValidationError: If arguments don't match schema
            Exception: Any exception raised by the wrapped function
        """
        # Validate arguments against schema
        self._validate_arguments(kwargs)

        try:
            if self._is_async:
                result = await self.func(**kwargs)
            else:
                # Run sync function in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                func_with_args = partial(self.func, **kwargs)
                result = await loop.run_in_executor(None, func_with_args)

            logger.debug(
                "Local function executed successfully (async)",
                extra={
                    "capability_name": self._name,
                    "arguments": kwargs,
                },
            )
            return result
        except Exception as e:
            logger.error(
                "Local function execution failed (async)",
                extra={
                    "capability_name": self._name,
                    "arguments": kwargs,
                    "error": str(e),
                },
            )
            raise

    def _validate_arguments(self, kwargs: dict[str, Any]) -> None:
        """Validate arguments against the capability schema.

        Args:
            kwargs: Arguments to validate

        Raises:
            CapabilityValidationError: If arguments don't match schema
        """
        schema = self.get_schema()
        required_params = schema.parameters.get("required", [])
        properties = schema.parameters.get("properties", {})

        # Check for missing required parameters
        for param in required_params:
            if param not in kwargs:
                raise CapabilityValidationError(
                    f"Missing required parameter '{param}' for capability '{self._name}'",
                    capability_name=self._name,
                    missing_parameter=param,
                )

        # Check for unexpected parameters
        for param in kwargs:
            if param not in properties:
                raise CapabilityValidationError(
                    f"Unexpected parameter '{param}' for capability '{self._name}'",
                    capability_name=self._name,
                    unexpected_parameter=param,
                )

    @staticmethod
    def _extract_docstring(func: Callable[..., Any]) -> str:
        """Extract first line of docstring from function.

        Args:
            func: The function to extract docstring from

        Returns:
            First line of docstring, or empty string if no docstring
        """
        if func.__doc__:
            return func.__doc__.split("\n")[0].strip()
        return ""

    @staticmethod
    def _extract_parameters(sig: inspect.Signature) -> dict[str, Any]:
        """Extract parameters from function signature.

        Converts function parameters to JSON Schema format, handling type hints
        and default values.

        Args:
            sig: The function signature

        Returns:
            JSON Schema for parameters
        """
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, param in sig.parameters.items():
            # Skip self and cls parameters
            if param_name in ("self", "cls"):
                continue

            prop: dict[str, Any] = {}

            # Extract type hint
            if param.annotation != inspect.Parameter.empty:
                prop = _type_to_json_schema(param.annotation)
            else:
                prop = {"type": "string"}

            properties[param_name] = prop

            # Track required parameters (those without defaults)
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    @staticmethod
    def _extract_return_type(sig: inspect.Signature) -> dict[str, Any]:
        """Extract return type from function signature.

        Converts return type annotation to JSON Schema format.

        Args:
            sig: The function signature

        Returns:
            JSON Schema for return type
        """
        if sig.return_annotation == inspect.Signature.empty:
            return {"type": "string"}

        return _type_to_json_schema(sig.return_annotation)


def _type_to_json_schema(python_type: Any) -> dict[str, Any]:
    """Convert Python type to JSON Schema.

    Handles basic types, generic types, and Union types. Falls back to
    string type for unknown types.

    Args:
        python_type: The Python type to convert

    Returns:
        JSON Schema representation of the type
    """
    # Handle None/NoneType
    if python_type is type(None):
        return {"type": "null"}

    # Handle basic types
    if python_type is str:
        return {"type": "string"}
    if python_type is int:
        return {"type": "integer"}
    if python_type is float:
        return {"type": "number"}
    if python_type is bool:
        return {"type": "boolean"}

    # Handle list
    if python_type is list or (
        hasattr(python_type, "__origin__") and python_type.__origin__ is list
    ):
        return {"type": "array", "items": {"type": "string"}}

    # Handle dict
    if python_type is dict or (
        hasattr(python_type, "__origin__") and python_type.__origin__ is dict
    ):
        return {"type": "object"}

    # Default to string for unknown types
    return {"type": "string"}
