"""Capability call handler for parsing and executing capability calls from provider responses.

This module provides the CapabilityCallHandler class for processing capability calls from
different LLM providers, executing capabilities, and formatting results.

**REFACTORED ARCHITECTURE:**
This module now follows the provider encapsulation principle by delegating all
provider-specific parsing and formatting to the provider classes themselves.

The CapabilityCallHandler is now a thin delegation layer that:
- Uses provider.parse_capability_calls() for parsing capability calls
- Uses provider.format_capability_results() for formatting results
- Handles capability execution and validation (provider-agnostic logic)

This aligns with the provider transformation architecture where all provider-specific
logic is contained within provider client classes.

See docs/provider-transformation-architecture.md for complete architecture documentation.
"""

import logging
from typing import Any

from nimbus.base.completion import CompletionResponse
from nimbus.tools.capability_models import CapabilityCall, CapabilityResult
from nimbus.tools.exceptions import (
    CapabilityCallParsingError,
    CapabilityNotFoundError,
    CapabilityValidationError,
)
from nimbus.tools.registry import CapabilityRegistry

logger = logging.getLogger(__name__)


class CapabilityCallHandler:
    """Handler for parsing and executing capability calls from provider responses.

    Processes capability calls from different LLM providers by delegating parsing
    and formatting to the provider classes, while handling the provider-agnostic
    capability execution logic.

    The handler now follows the provider encapsulation architecture:
    - Provider-specific parsing: Delegated to provider.parse_capability_calls()
    - Provider-agnostic execution: Handled by this class
    - Provider-specific formatting: Delegated to provider.format_capability_results()

    Attributes:
        registry: CapabilityRegistry instance for looking up capabilities

    Example:
        >>> registry = CapabilityRegistry.get_instance()
        >>> handler = CapabilityCallHandler(registry)
        >>> provider = OpenAIProvider(api_key="...")
        >>>
        >>> # Parse capability calls using provider logic
        >>> capability_calls = handler.parse_capability_calls(response, provider)
        >>>
        >>> # Execute capability calls (provider-agnostic)
        >>> results = await handler.execute_capability_calls(capability_calls)
        >>>
        >>> # Format results using provider logic
        >>> formatted = handler.format_capability_results(results, provider)
    """

    def __init__(self, registry: CapabilityRegistry) -> None:
        """Initialize CapabilityCallHandler with a capability registry.

        Args:
            registry: CapabilityRegistry instance for looking up capabilities

        Example:
            >>> registry = CapabilityRegistry.get_instance()
            >>> handler = CapabilityCallHandler(registry)
        """
        self.registry = registry

    def parse_capability_calls(
        self,
        response: CompletionResponse,
        provider: Any,
    ) -> list[CapabilityCall]:
        """Parse capability calls from a provider response using provider-specific logic.

        Delegates to the provider's parse_capability_calls method to handle
        provider-specific response formats. This ensures all provider-specific
        logic is contained within the provider classes.

        Args:
            response: CompletionResponse from the provider
            provider: Provider instance with parse_capability_calls method

        Returns:
            List of CapabilityCall objects parsed from the response

        Raises:
            CapabilityCallParsingError: If parsing fails or the provider cannot format calls

        Example:
            >>> handler = CapabilityCallHandler(registry)
            >>> provider = OpenAIProvider(api_key="...")
            >>> capability_calls = handler.parse_capability_calls(response, provider)
            >>> for call in capability_calls:
            ...     print(f"{call.name}: {call.arguments}")
        """
        try:
            if not hasattr(provider, 'parse_capability_calls'):
                raise CapabilityCallParsingError(
                    f"Provider {type(provider).__name__} does not support capability call parsing",
                    provider=type(provider).__name__,
                )

            capability_calls = provider.parse_capability_calls(response)
            return capability_calls or []

        except CapabilityCallParsingError:
            raise
        except Exception as e:
            provider_name = getattr(provider, '__class__', type(provider)).__name__
            raise CapabilityCallParsingError(
                f"Failed to parse capability calls from {provider_name}: {e}",
                provider=provider_name,
                original_error=str(e),
            ) from e

    async def execute_capability_calls(
        self,
        capability_calls: list[CapabilityCall],
    ) -> list[CapabilityResult]:
        """Execute a list of capability calls and return results.

        Executes each capability call by looking up the capability in the registry,
        validating arguments, and executing the capability. Handles errors
        gracefully by capturing them in the CapabilityResult.

        This method is provider-agnostic and handles the core capability execution logic.

        Args:
            capability_calls: List of CapabilityCall objects to execute

        Returns:
            List of CapabilityResult objects with execution results or errors

        Example:
            >>> handler = CapabilityCallHandler(registry)
            >>> capability_calls = [
            ...     CapabilityCall(id="call_1", name="get_weather", arguments={"location": "NYC"})
            ... ]
            >>> results = await handler.execute_capability_calls(capability_calls)
            >>> for result in results:
            ...     if result.error:
            ...         print(f"Error: {result.error}")
            ...     else:
            ...         print(f"Result: {result.result}")
        """
        results = []

        for capability_call in capability_calls:
            try:
                # Look up capability
                capability = self.registry.get(capability_call.name)
                if capability is None:
                    raise CapabilityNotFoundError(
                        f"Capability '{capability_call.name}' not found in registry",
                        capability_name=capability_call.name,
                    )

                # Validate arguments against schema
                schema = capability.get_schema()
                self._validate_arguments(capability_call.arguments, schema.parameters)

                # Execute capability
                logger.info(
                    "Executing capability call",
                    extra={
                        "capability_call_id": capability_call.id,
                        "capability_name": capability_call.name,
                        "arguments": capability_call.arguments,
                    },
                )

                result = await capability.aexecute(**capability_call.arguments)

                # Create successful result
                results.append(
                    CapabilityResult(
                        capability_call_id=capability_call.id,
                        name=capability_call.name,
                        result=result,
                        error=None,
                    )
                )

                logger.info(
                    "Capability call executed successfully",
                    extra={
                        "capability_call_id": capability_call.id,
                        "capability_name": capability_call.name,
                    },
                )

            except (CapabilityNotFoundError, CapabilityValidationError) as e:
                # Capability-specific errors
                logger.error(
                    "Capability call execution failed",
                    extra={
                        "capability_call_id": capability_call.id,
                        "capability_name": capability_call.name,
                        "error": str(e),
                    },
                )
                results.append(
                    CapabilityResult(
                        capability_call_id=capability_call.id,
                        name=capability_call.name,
                        result=None,
                        error=str(e),
                    )
                )

            except Exception as e:
                # Unexpected errors
                logger.error(
                    "Capability call execution failed with unexpected error",
                    extra={
                        "capability_call_id": capability_call.id,
                        "capability_name": capability_call.name,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                results.append(
                    CapabilityResult(
                        capability_call_id=capability_call.id,
                        name=capability_call.name,
                        result=None,
                        error=f"Execution failed: {e}",
                    )
                )

        return results

    def _validate_arguments(
        self,
        arguments: dict[str, Any],
        parameters_schema: dict[str, Any],
    ) -> None:
        """Validate arguments against parameter schema.

        Performs basic validation of arguments against the JSON Schema
        parameters definition. Checks for required parameters and basic
        type compatibility.

        Args:
            arguments: Arguments to validate
            parameters_schema: JSON Schema for parameters

        Raises:
            CapabilityValidationError: If validation fails
        """
        # Check required parameters
        required = parameters_schema.get("required", [])
        for param in required:
            if param not in arguments:
                raise CapabilityValidationError(
                    f"Missing required parameter: {param}",
                    capability_name="<unknown>",
                    missing_parameter=param,
                )

        # Basic type checking for provided arguments
        properties = parameters_schema.get("properties", {})
        for arg_name, arg_value in arguments.items():
            if arg_name in properties:
                expected_type = properties[arg_name].get("type")
                if expected_type:
                    self._check_type(arg_name, arg_value, expected_type)

    def _check_type(
        self,
        param_name: str,
        value: Any,
        expected_type: str,
    ) -> None:
        """Check if value matches expected JSON Schema type.

        Args:
            param_name: Parameter name for error messages
            value: Value to check
            expected_type: Expected JSON Schema type

        Raises:
            CapabilityValidationError: If type doesn't match
        """
        type_map: dict[str, type[Any] | tuple[type[Any], ...]] = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if expected_type in type_map:
            expected_python_type = type_map[expected_type]
            if not isinstance(value, expected_python_type):
                raise CapabilityValidationError(
                    f"Parameter '{param_name}' has wrong type: "
                    f"expected {expected_type}, got {type(value).__name__}",
                    capability_name="<unknown>",
                    parameter_name=param_name,
                    expected_type=expected_type,
                    actual_type=type(value).__name__,
                )

    def format_capability_results(
        self,
        results: list[CapabilityResult],
        provider: Any,
    ) -> list[dict[str, Any]]:
        """Format capability results for sending back to provider using provider-specific logic.

        Delegates to the provider's format_capability_results method to handle
        provider-specific result formats. This ensures all provider-specific
        logic is contained within the provider classes.

        Args:
            results: List of CapabilityResult objects to format
            provider: Provider instance with format_capability_results method

        Returns:
            List of formatted result dictionaries

        Raises:
            CapabilityCallParsingError: If formatting fails or the provider cannot format results

        Example:
            >>> handler = CapabilityCallHandler(registry)
            >>> provider = OpenAIProvider(api_key="...")
            >>> results = [
            ...     CapabilityResult(
            ...         capability_call_id="call_1",
            ...         name="get_weather",
            ...         result={"temp": 72}
            ...     )
            ... ]
            >>> formatted = handler.format_capability_results(results, provider)
        """
        try:
            if not hasattr(provider, 'format_capability_results'):
                raise CapabilityCallParsingError(
                    f"Provider {type(provider).__name__} does not support "
                    "capability result formatting",
                    provider=type(provider).__name__,
                )

            formatted: list[dict[str, Any]] = provider.format_capability_results(results)
            return formatted

        except CapabilityCallParsingError:
            raise
        except Exception as e:
            provider_name = getattr(provider, '__class__', type(provider)).__name__
            raise CapabilityCallParsingError(
                f"Failed to format capability results for {provider_name}: {e}",
                provider=provider_name,
                original_error=str(e),
            ) from e
