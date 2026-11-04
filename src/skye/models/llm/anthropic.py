"""Anthropic provider implementation.

This module provides the Anthropic implementation of the ModelInterface,
supporting Claude 3.x models (Opus, Sonnet, Haiku).

Features:
- Standard-library REST adapter (no vendor SDK), POST /v1/messages
- Separate system message handling
- Tool use (Anthropic's function calling)
- Thinking/reasoning features
- Streaming support
- Async support via run_in_executor

Example:
    >>> from skye.models.llm.anthropic import AnthropicProvider
    >>> from skye.base.completion import CompletionRequest
    >>> from skye.base.messages import UserMessage
    >>>
    >>> provider = AnthropicProvider(api_key="sk-ant-...")
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="claude-3-opus-20240229"
    ... )
    >>> response = provider.complete(request)
    >>> print(response.content)
"""

import asyncio
from collections.abc import Iterator
import json
from datetime import datetime, timezone
from typing import Any

from skye.base.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from skye.base.messages import AssistantMessage
from skye.models.base import BaseModelProvider
from skye.models.transport.structured import STRUCTURED_TOOL, schema_of
from skye.models.transport import rest

# Import CapabilityCall for capability call extraction
try:
    from skye.base.completion import CapabilityCall
    CAPABILITIES_AVAILABLE = True
except ImportError:
    CAPABILITIES_AVAILABLE = False


DEFAULT_API_BASE = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(BaseModelProvider):
    """Anthropic provider implementation.
    
    Implements the ModelInterface for Anthropic's API, supporting all Claude 3.x
    models including Opus, Sonnet, and Haiku.
    
    Args:
        api_key: Anthropic API key
        **kwargs: Additional configuration parameters
    
    Example:
        >>> provider = AnthropicProvider(api_key="sk-ant-...")
        >>> response = provider.complete(request)
    """

    
    def __init__(
        self,
        api_key: str,
        **kwargs: Any
    ) -> None:
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            **kwargs: Additional configuration parameters
        """
        self.api_base = str(kwargs.pop("api_base", DEFAULT_API_BASE)).rstrip("/")
        self.timeout = float(kwargs.pop("timeout", 60.0))
        super().__init__(
            api_key=api_key,
            **kwargs
        )
        self.api_key = api_key

    @property
    def _url(self) -> str:
        return f"{self.api_base}/v1/messages"

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key, "anthropic-version": ANTHROPIC_VERSION}
    
    def _initialize_client(self) -> Any:
        """No SDK client: requests go through the stdlib REST transport."""
        return None

    def _transform_messages(self, messages: list[Any]) -> tuple[str | None, list[dict[str, Any]]]:
        """Transform Skye messages to Anthropic format.
        
        Anthropic requires the system message to be passed separately from
        the conversation messages. Tool results are formatted as user messages
        with special content blocks.
        
        Args:
            messages: List of Skye message objects
            
        Returns:
            Tuple of (system_message, anthropic_messages) where system_message
            is a string or None, and anthropic_messages is a list of dicts
        """
        from skye.base.messages import AssistantMessage, CapabilityMessage, SystemMessage
        
        system = None
        anthropic_messages = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system = msg.content
            elif isinstance(msg, CapabilityMessage):
                anthropic_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.capability_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )
            else:
                content: str | list[dict[str, Any]] = msg.content
                images = getattr(msg, "images", None)
                if images:
                    from skye.models.transport.multimodal import ImageHandler

                    content = [
                        *(ImageHandler.to_anthropic_format(image) for image in images),
                        {"type": "text", "text": msg.content},
                    ]
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    content = [
                        {
                            "type": "tool_use",
                            "id": call["id"],
                            "name": call["function"]["name"],
                            "input": call["function"]["arguments"],
                        }
                        for call in msg.capability_calls
                    ]
                anthropic_messages.append({"role": msg.role, "content": content})

        return system, anthropic_messages
    
    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        """Transform Skye capabilities to Anthropic tool use format.
        
        Anthropic uses a flat structure with "name", "description", and
        "input_schema" fields.
        
        Args:
            capabilities: List of CapabilityInterface objects or dicts
            
        Returns:
            List of tool definitions in Anthropic format
        """
        tools = []
        for capability in capabilities:
            # Handle both CapabilityInterface objects and dict format
            if isinstance(capability, dict):
                # Check if already in Anthropic format
                if "input_schema" in capability:
                    tools.append(capability)
                else:
                    # Convert from OpenAI format to Anthropic format
                    func = capability.get("function", {})
                    tool = {
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {
                            "type": "object",
                            "properties": {},
                        }),
                    }
                    tools.append(tool)
            else:
                # CapabilityInterface object, convert to Anthropic format
                schema = capability.get_schema()
                tool = {
                    "name": schema.name,
                    "description": schema.description,
                    "input_schema": schema.parameters or {
                        "type": "object",
                        "properties": {},
                    },
                }
                tools.append(tool)
        return tools
    
    @staticmethod
    def _plain(value: Any) -> Any:
        """Unwrap a JsonObject (tool ``input``) back to a plain dict."""
        return value.to_dict() if isinstance(value, rest.JsonObject) else value

    def _extract_capability_calls(self, response: Any) -> list[Any] | None:
        """Extract capability calls from Anthropic response.
        
        Parses tool use blocks from the Anthropic response format and converts them
        to Skye CapabilityCall objects.
        
        Args:
            response: Anthropic response object
            
        Returns:
            List of CapabilityCall objects, or None if no capability calls
        """
        if not CAPABILITIES_AVAILABLE:
            return None
        
        capability_calls = []
        for content_block in response.content:
            if content_block.type == "tool_use" and content_block.name != STRUCTURED_TOOL:
                capability_calls.append(
                    CapabilityCall(
                        id=content_block.id,
                        name=content_block.name,
                        arguments=self._plain(content_block.input)
                    )
                )
        
        return capability_calls if capability_calls else None
    
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to Anthropic format.
        
        Anthropic requires system messages to be passed separately from the
        conversation messages.
        
        Args:
            request: The skye CompletionRequest
            
        Returns:
            Dictionary in Anthropic API format
        """
        # Ensure messages are available
        if not request.messages:
            raise ValueError("messages must be provided for Anthropic provider")
        
        # Transform messages and extract system message using internal method
        system, anthropic_messages = self._transform_messages(request.messages)
        
        anthropic_request: dict[str, Any] = {
            "model": request.model,
            "messages": anthropic_messages,
            "temperature": request.temperature,
            "stream": request.stream
        }
        
        # Add system message if present
        if system:
            anthropic_request["system"] = system
        
        if request.max_tokens:
            anthropic_request["max_tokens"] = request.max_tokens
        else:
            # Anthropic requires max_tokens, set a default
            anthropic_request["max_tokens"] = 4096
        
        if request.top_p:
            anthropic_request["top_p"] = request.top_p
        
        if request.stop:
            anthropic_request["stop_sequences"] = request.stop
        
        # Handle tool use (Anthropic's function calling)
        if request.capabilities:
            # Check if capabilities are CapabilityInterface objects or dicts
            if request.capabilities and isinstance(request.capabilities[0], dict):
                # Legacy support: capabilities are already in dict format
                anthropic_tools = []
                for cap in request.capabilities:
                    if cap.get("type") == "function":
                        func = cap["function"]
                        anthropic_tools.append({
                            "name": func["name"],
                            "description": func.get("description", ""),
                            "input_schema": func.get("parameters", {})
                        })
                anthropic_request["tools"] = anthropic_tools
            elif CAPABILITIES_AVAILABLE:
                # Use internal method to convert capabilities to Anthropic format
                anthropic_request["tools"] = self._transform_capabilities(request.capabilities)
            else:
                # Capabilities module not available
                raise ValueError("Capabilities module not installed. Install with: pip install skyeai[capabilities]")
            
            # Handle capability choice
            if request.capability_choice:
                if request.capability_choice == "auto":
                    anthropic_request["tool_choice"] = {"type": "auto"}
                elif request.capability_choice == "required":
                    anthropic_request["tool_choice"] = {"type": "any"}
                elif isinstance(request.capability_choice, str):
                    # Specific capability name
                    anthropic_request["tool_choice"] = {
                        "type": "tool",
                        "name": request.capability_choice
                    }
                elif isinstance(request.capability_choice, dict):
                    # Already formatted tool choice
                    anthropic_request["tool_choice"] = request.capability_choice
        
        # Structured output: no native mode, so the answer is forced through one tool (function calling)
        if request.response_schema and not request.capabilities:
            anthropic_request["tools"] = [
                {
                    "name": STRUCTURED_TOOL,
                    "description": f"Return the answer as a {request.response_schema.__name__}.",
                    "input_schema": schema_of(request.response_schema),
                }
            ]
            anthropic_request["tool_choice"] = {"type": "tool", "name": STRUCTURED_TOOL}

        # Provider-specific metadata
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith("anthropic_"):
                    anthropic_request[key[10:]] = value
        
        return anthropic_request
    
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform Anthropic response to CompletionResponse.
        
        Args:
            response: The Anthropic response object
            
        Returns:
            CompletionResponse in skye format
        """
        # Extract content
        content_text = ""
        capability_calls_metadata = []
        
        for content_block in response.content:
            if content_block.type == "text":
                content_text += content_block.text
            elif content_block.type == "tool_use" and content_block.name == STRUCTURED_TOOL:
                # The structured answer: its input is the JSON the declared schema describes
                content_text = json.dumps(self._plain(content_block.input))
            elif content_block.type == "tool_use":
                # Store in metadata for compatibility
                capability_calls_metadata.append({
                    "id": content_block.id,
                    "type": "function",
                    "function": {
                        "name": content_block.name,
                        "arguments": self._plain(content_block.input)
                    }
                })
        
        # Extract capability calls using internal method
        capability_calls_list = self._extract_capability_calls(response)
        
        # Create timestamp from current time (Anthropic doesn't provide created timestamp)
        created_at = datetime.now(timezone.utc)
        
        return CompletionResponse(
            id=response.id,
            model=response.model,
            provider="anthropic",
            content=content_text,
            structured_output=None,  # Anthropic doesn't have native structured output
            role="assistant",
            finish_reason=response.stop_reason,
            usage=TokenUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            ),
            created_at=created_at,
            capability_calls=capability_calls_list if capability_calls_list else None,
            metadata={
                "stop_sequence": getattr(response, "stop_sequence", None),
                "tool_calls": capability_calls_metadata if capability_calls_metadata else None,
                "content": [
                    {
                        "type": block.type,
                        "id": getattr(block, "id", None),
                        "name": getattr(block, "name", None),
                        "input": self._plain(getattr(block, "input", None)),
                    }
                    for block in response.content
                    if block.type == "tool_use"
                ]
            }
        )
    
    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform Anthropic stream chunk to StreamChunk.
        
        Args:
            chunk: The Anthropic stream event
            
        Returns:
            StreamChunk in skye format
        """
        delta_content = ""
        finish_reason = None
        etype = getattr(chunk, "type", None)
        delta = getattr(chunk, "delta", None)

        if etype == "content_block_delta":
            if delta is not None and hasattr(delta, "text"):
                delta_content = delta.text
        elif etype == "message_delta":
            if delta is not None and hasattr(delta, "stop_reason"):
                finish_reason = delta.stop_reason

        return StreamChunk(
            id=getattr(chunk, "message_id", ""),
            delta=delta_content,
            finish_reason=finish_reason,
            index=getattr(chunk, "index", 0)
        )

    def _call_provider(self, request: dict[str, Any]) -> Any:
        """POST the request to ``/v1/messages``; return the JSON as a JsonObject."""
        return rest.post_json(
            self._url, request, headers=self._headers(),
            timeout=self.timeout, provider="anthropic",
        )

    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Stream SSE events from ``/v1/messages`` (``stream: true``)."""
        yield from rest.stream_sse_json(
            self._url, {**request, "stream": True}, headers=self._headers(),
            timeout=self.timeout, provider="anthropic",
        )

    async def acomplete(self, *args: Any, **kwargs: Any) -> CompletionResponse:  # type: ignore[override]
        """Run :meth:`complete` in an executor so the event loop is not blocked.

        Takes the same arguments as :meth:`complete`: ``messages=..., model=...`` or a ``CompletionRequest``.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.complete(*args, **kwargs))

    def format_capability_results(self, results: list[Any]) -> list[dict[str, Any]]:
        """Format capability results for Anthropic.
        
        Anthropic expects tool results in this format:
        {
            "type": "tool_result",
            "tool_use_id": "toolu_123",
            "content": "{\"result\": \"value\"}"
        }
        
        Args:
            results: List of CapabilityResult objects
            
        Returns:
            List of formatted result dictionaries in Anthropic format
        """
        import json
        
        formatted = []
        for result in results:
            # Convert result to JSON string
            if result.error:
                content = json.dumps({"error": result.error})
            elif isinstance(result.result, str):
                content = result.result
            else:
                content = json.dumps(result.result)

            formatted.append({
                "type": "tool_result",
                "tool_use_id": result.capability_call_id,
                "content": content,
            })

        return formatted
    
    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata and capabilities.
        
        Returns:
            Dictionary with provider information and capabilities
        """
        return {
            "provider": "anthropic",
            "supports_streaming": True,
            "supports_function_calling": True,  # Via tool use
            "supports_structured_output": False,  # No native support
            "supports_multimodal": True,  # Claude 3 supports images
            "supports_thinking": True  # Claude 3 Opus supports extended thinking
        }
