"""Tool call handler for parsing and executing tool calls from provider responses.

This module provides the ToolCallHandler class for processing tool calls from
different LLM providers, executing capabilities, and formatting results.
"""

import json
import logging
from typing import Any

from nimbus.capabilities.exceptions import (
    CapabilityNotFoundError,
    CapabilityValidationError,
    ToolCallParsingError,
)
from nimbus.capabilities.registry import CapabilityRegistry
from nimbus.capabilities.tool_models import ToolCall, ToolResult
from nimbus.completion import CompletionResponse

logger = logging.getLogger(__name__)


class ToolCallHandler:
    """Handler for parsing and executing tool calls from provider responses.

    Processes tool calls from different LLM providers (OpenAI, Anthropic, Bedrock,
    Azure, Vertex), executes the corresponding capabilities, and formats results
    for sending back to the provider.

    The handler supports provider-specific parsing and formatting while providing
    a unified interface for tool execution. It validates arguments against capability
    schemas and handles errors gracefully.

    Attributes:
        registry: CapabilityRegistry instance for looking up capabilities

    Example:
        >>> registry = CapabilityRegistry.get_instance()
        >>> handler = ToolCallHandler(registry)
        >>>
        >>> # Parse tool calls from provider response
        >>> tool_calls = handler.parse_tool_calls(response, "openai")
        >>>
        >>> # Execute tool calls
        >>> results = await handler.execute_tool_calls(tool_calls)
        >>>
        >>> # Format results for provider
        >>> formatted = handler.format_tool_results(results, "openai")
    """

    def __init__(self, registry: CapabilityRegistry) -> None:
        """Initialize ToolCallHandler with a capability registry.

        Args:
            registry: CapabilityRegistry instance for looking up capabilities

        Example:
            >>> registry = CapabilityRegistry.get_instance()
            >>> handler = ToolCallHandler(registry)
        """
        self.registry = registry

    def parse_tool_calls(
        self,
        response: CompletionResponse,
        provider: str,
    ) -> list[ToolCall]:
        """Parse tool calls from a provider response.

        Extracts tool calls from the provider-specific response format and
        converts them to a unified ToolCall format. Supports OpenAI, Anthropic,
        Bedrock, Azure, and Vertex AI response formats.

        Args:
            response: CompletionResponse from the provider
            provider: Provider name ('openai', 'anthropic', 'bedrock', 'azure', 'vertex')

        Returns:
            List of ToolCall objects parsed from the response

        Raises:
            ToolCallParsingError: If parsing fails or format is invalid

        Example:
            >>> handler = ToolCallHandler(registry)
            >>> tool_calls = handler.parse_tool_calls(response, "openai")
            >>> for call in tool_calls:
            ...     print(f"{call.name}: {call.arguments}")
        """
        provider_lower = provider.lower()

        try:
            if provider_lower in ("openai", "azure"):
                return self._parse_openai_tool_calls(response)
            elif provider_lower == "anthropic":
                return self._parse_anthropic_tool_calls(response)
            elif provider_lower == "bedrock":
                return self._parse_bedrock_tool_calls(response)
            elif provider_lower == "vertex":
                return self._parse_vertex_tool_calls(response)
            else:
                raise ToolCallParsingError(
                    f"Unsupported provider: {provider}",
                    provider=provider,
                )
        except ToolCallParsingError:
            raise
        except Exception as e:
            raise ToolCallParsingError(
                f"Failed to parse tool calls from {provider}: {e}",
                provider=provider,
                original_error=str(e),
            ) from e

    def _parse_openai_tool_calls(
        self,
        response: CompletionResponse,
    ) -> list[ToolCall]:
        """Parse tool calls from OpenAI/Azure response format.

        OpenAI format:
        {
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": "{\"location\": \"San Francisco\"}"
                    }
                }
            ]
        }

        Args:
            response: CompletionResponse from OpenAI/Azure

        Returns:
            List of ToolCall objects

        Raises:
            ToolCallParsingError: If parsing fails
        """
        tool_calls_data = response.metadata.get("tool_calls", [])
        if not tool_calls_data:
            return []

        tool_calls = []
        for call_data in tool_calls_data:
            try:
                call_id = call_data.get("id")
                if not call_id:
                    raise ValueError("Missing tool call id")

                function_data = call_data.get("function", {})
                name = function_data.get("name")
                if not name:
                    raise ValueError("Missing function name")

                # Parse arguments JSON string
                arguments_str = function_data.get("arguments", "{}")
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in arguments: {e}") from e

                tool_calls.append(
                    ToolCall(
                        id=call_id,
                        name=name,
                        arguments=arguments,
                    )
                )
            except Exception as e:
                logger.warning(
                    "Failed to parse OpenAI tool call",
                    extra={"error": str(e), "call_data": call_data},
                )
                raise ToolCallParsingError(
                    f"Failed to parse OpenAI tool call: {e}",
                    provider="openai",
                    call_data=call_data,
                ) from e

        return tool_calls

    def _parse_anthropic_tool_calls(
        self,
        response: CompletionResponse,
    ) -> list[ToolCall]:
        """Parse tool calls from Anthropic response format.

        Anthropic format:
        {
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "get_weather",
                    "input": {"location": "San Francisco"}
                }
            ]
        }

        Args:
            response: CompletionResponse from Anthropic

        Returns:
            List of ToolCall objects

        Raises:
            ToolCallParsingError: If parsing fails
        """
        content_blocks = response.metadata.get("content", [])
        if not content_blocks:
            return []

        tool_calls = []
        for block in content_blocks:
            try:
                if block.get("type") != "tool_use":
                    continue

                call_id = block.get("id")
                if not call_id:
                    raise ValueError("Missing tool use id")

                name = block.get("name")
                if not name:
                    raise ValueError("Missing tool name")

                # Anthropic uses "input" instead of "arguments"
                arguments = block.get("input", {})

                tool_calls.append(
                    ToolCall(
                        id=call_id,
                        name=name,
                        arguments=arguments,
                    )
                )
            except Exception as e:
                logger.warning(
                    "Failed to parse Anthropic tool call",
                    extra={"error": str(e), "block": block},
                )
                raise ToolCallParsingError(
                    f"Failed to parse Anthropic tool call: {e}",
                    provider="anthropic",
                    block=block,
                ) from e

        return tool_calls

    def _parse_bedrock_tool_calls(
        self,
        response: CompletionResponse,
    ) -> list[ToolCall]:
        """Parse tool calls from Bedrock response format.

        Bedrock format (Converse API):
        {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_123",
                                "name": "get_weather",
                                "input": {"location": "San Francisco"}
                            }
                        }
                    ]
                }
            }
        }

        Args:
            response: CompletionResponse from Bedrock

        Returns:
            List of ToolCall objects

        Raises:
            ToolCallParsingError: If parsing fails
        """
        # Bedrock stores tool calls in nested structure
        output = response.metadata.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])

        if not content_blocks:
            return []

        tool_calls = []
        for block in content_blocks:
            try:
                tool_use = block.get("toolUse")
                if not tool_use:
                    continue

                call_id = tool_use.get("toolUseId")
                if not call_id:
                    raise ValueError("Missing toolUseId")

                name = tool_use.get("name")
                if not name:
                    raise ValueError("Missing tool name")

                arguments = tool_use.get("input", {})

                tool_calls.append(
                    ToolCall(
                        id=call_id,
                        name=name,
                        arguments=arguments,
                    )
                )
            except Exception as e:
                logger.warning(
                    "Failed to parse Bedrock tool call",
                    extra={"error": str(e), "block": block},
                )
                raise ToolCallParsingError(
                    f"Failed to parse Bedrock tool call: {e}",
                    provider="bedrock",
                    block=block,
                ) from e

        return tool_calls

    def _parse_vertex_tool_calls(
        self,
        response: CompletionResponse,
    ) -> list[ToolCall]:
        """Parse tool calls from Vertex AI response format.

        Vertex format (Gemini):
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "get_weather",
                                    "args": {"location": "San Francisco"}
                                }
                            }
                        ]
                    }
                }
            ]
        }

        Args:
            response: CompletionResponse from Vertex AI

        Returns:
            List of ToolCall objects

        Raises:
            ToolCallParsingError: If parsing fails
        """
        candidates = response.metadata.get("candidates", [])
        if not candidates:
            return []

        tool_calls = []
        # Process first candidate
        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        for idx, part in enumerate(parts):
            try:
                function_call = part.get("functionCall")
                if not function_call:
                    continue

                name = function_call.get("name")
                if not name:
                    raise ValueError("Missing function name")

                # Vertex uses "args" instead of "arguments"
                arguments = function_call.get("args", {})

                # Generate ID since Vertex doesn't provide one
                call_id = f"vertex_call_{idx}"

                tool_calls.append(
                    ToolCall(
                        id=call_id,
                        name=name,
                        arguments=arguments,
                    )
                )
            except Exception as e:
                logger.warning(
                    "Failed to parse Vertex tool call",
                    extra={"error": str(e), "part": part},
                )
                raise ToolCallParsingError(
                    f"Failed to parse Vertex tool call: {e}",
                    provider="vertex",
                    part=part,
                ) from e

        return tool_calls

    async def execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
    ) -> list[ToolResult]:
        """Execute a list of tool calls and return results.

        Executes each tool call by looking up the capability in the registry,
        validating arguments, and executing the capability. Handles errors
        gracefully by capturing them in the ToolResult.

        Args:
            tool_calls: List of ToolCall objects to execute

        Returns:
            List of ToolResult objects with execution results or errors

        Example:
            >>> handler = ToolCallHandler(registry)
            >>> tool_calls = [
            ...     ToolCall(id="call_1", name="get_weather", arguments={"location": "NYC"})
            ... ]
            >>> results = await handler.execute_tool_calls(tool_calls)
            >>> for result in results:
            ...     if result.error:
            ...         print(f"Error: {result.error}")
            ...     else:
            ...         print(f"Result: {result.result}")
        """
        results = []

        for tool_call in tool_calls:
            try:
                # Look up capability
                capability = self.registry.get(tool_call.name)
                if capability is None:
                    raise CapabilityNotFoundError(
                        f"Capability '{tool_call.name}' not found in registry",
                        capability_name=tool_call.name,
                    )

                # Validate arguments against schema
                schema = capability.get_schema()
                self._validate_arguments(tool_call.arguments, schema.parameters)

                # Execute capability
                logger.info(
                    "Executing tool call",
                    extra={
                        "tool_call_id": tool_call.id,
                        "capability_name": tool_call.name,
                        "arguments": tool_call.arguments,
                    },
                )

                result = await capability.aexecute(**tool_call.arguments)

                # Create successful result
                results.append(
                    ToolResult(
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                        result=result,
                        error=None,
                    )
                )

                logger.info(
                    "Tool call executed successfully",
                    extra={
                        "tool_call_id": tool_call.id,
                        "capability_name": tool_call.name,
                    },
                )

            except (CapabilityNotFoundError, CapabilityValidationError) as e:
                # Capability-specific errors
                logger.error(
                    "Tool call execution failed",
                    extra={
                        "tool_call_id": tool_call.id,
                        "capability_name": tool_call.name,
                        "error": str(e),
                    },
                )
                results.append(
                    ToolResult(
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                        result=None,
                        error=str(e),
                    )
                )

            except Exception as e:
                # Unexpected errors
                logger.error(
                    "Tool call execution failed with unexpected error",
                    extra={
                        "tool_call_id": tool_call.id,
                        "capability_name": tool_call.name,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                results.append(
                    ToolResult(
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
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

    def format_tool_results(
        self,
        results: list[ToolResult],
        provider: str,
    ) -> list[dict[str, Any]]:
        """Format tool results for sending back to provider.

        Converts ToolResult objects to provider-specific format for sending
        back to the LLM. Each provider expects results in a different format.

        Args:
            results: List of ToolResult objects to format
            provider: Provider name ('openai', 'anthropic', 'bedrock', 'azure', 'vertex')

        Returns:
            List of formatted result dictionaries

        Raises:
            ToolCallParsingError: If formatting fails

        Example:
            >>> handler = ToolCallHandler(registry)
            >>> results = [
            ...     ToolResult(
            ...         tool_call_id="call_1",
            ...         name="get_weather",
            ...         result={"temp": 72}
            ...     )
            ... ]
            >>> formatted = handler.format_tool_results(results, "openai")
        """
        provider_lower = provider.lower()

        try:
            if provider_lower in ("openai", "azure"):
                return self._format_openai_results(results)
            elif provider_lower == "anthropic":
                return self._format_anthropic_results(results)
            elif provider_lower == "bedrock":
                return self._format_bedrock_results(results)
            elif provider_lower == "vertex":
                return self._format_vertex_results(results)
            else:
                raise ToolCallParsingError(
                    f"Unsupported provider: {provider}",
                    provider=provider,
                )
        except ToolCallParsingError:
            raise
        except Exception as e:
            raise ToolCallParsingError(
                f"Failed to format tool results for {provider}: {e}",
                provider=provider,
                original_error=str(e),
            ) from e

    def _format_openai_results(
        self,
        results: list[ToolResult],
    ) -> list[dict[str, Any]]:
        """Format results for OpenAI/Azure.

        OpenAI format:
        {
            "tool_call_id": "call_123",
            "role": "tool",
            "content": "{\"result\": \"value\"}"
        }

        Args:
            results: List of ToolResult objects

        Returns:
            List of formatted result dictionaries
        """
        formatted = []
        for result in results:
            # Convert result to JSON string
            if result.error:
                content = json.dumps({"error": result.error})
            elif isinstance(result.result, str):
                content = result.result
            else:
                content = json.dumps(result.result)

            formatted.append(
                {
                    "tool_call_id": result.tool_call_id,
                    "role": "tool",
                    "content": content,
                }
            )

        return formatted

    def _format_anthropic_results(
        self,
        results: list[ToolResult],
    ) -> list[dict[str, Any]]:
        """Format results for Anthropic.

        Anthropic format:
        {
            "type": "tool_result",
            "tool_use_id": "toolu_123",
            "content": "{\"result\": \"value\"}"
        }

        Args:
            results: List of ToolResult objects

        Returns:
            List of formatted result dictionaries
        """
        formatted = []
        for result in results:
            # Convert result to JSON string
            if result.error:
                content = json.dumps({"error": result.error})
            elif isinstance(result.result, str):
                content = result.result
            else:
                content = json.dumps(result.result)

            formatted.append(
                {
                    "type": "tool_result",
                    "tool_use_id": result.tool_call_id,
                    "content": content,
                }
            )

        return formatted

    def _format_bedrock_results(
        self,
        results: list[ToolResult],
    ) -> list[dict[str, Any]]:
        """Format results for Bedrock.

        Bedrock format:
        {
            "toolResult": {
                "toolUseId": "tooluse_123",
                "content": [
                    {
                        "json": {"result": "value"}
                    }
                ]
            }
        }

        Args:
            results: List of ToolResult objects

        Returns:
            List of formatted result dictionaries
        """
        formatted = []
        for result in results:
            # Convert result to appropriate format
            if result.error:
                result_data = {"error": result.error}
            elif isinstance(result.result, dict):
                result_data = result.result
            elif isinstance(result.result, str):
                try:
                    result_data = json.loads(result.result)
                except json.JSONDecodeError:
                    result_data = {"result": result.result}
            else:
                result_data = {"result": result.result}

            formatted.append(
                {
                    "toolResult": {
                        "toolUseId": result.tool_call_id,
                        "content": [{"json": result_data}],
                    }
                }
            )

        return formatted

    def _format_vertex_results(
        self,
        results: list[ToolResult],
    ) -> list[dict[str, Any]]:
        """Format results for Vertex AI.

        Vertex format:
        {
            "functionResponse": {
                "name": "get_weather",
                "response": {"result": "value"}
            }
        }

        Args:
            results: List of ToolResult objects

        Returns:
            List of formatted result dictionaries
        """
        formatted = []
        for result in results:
            # Convert result to appropriate format
            if result.error:
                response_data = {"error": result.error}
            elif isinstance(result.result, dict):
                response_data = result.result
            elif isinstance(result.result, str):
                try:
                    response_data = json.loads(result.result)
                except json.JSONDecodeError:
                    response_data = {"result": result.result}
            else:
                response_data = {"result": result.result}

            formatted.append(
                {
                    "functionResponse": {
                        "name": result.name,
                        "response": response_data,
                    }
                }
            )

        return formatted
