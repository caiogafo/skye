"""Anthropic provider implementation.

This module provides the Anthropic implementation of the ModelInterface,
supporting Claude 3.x models (Opus, Sonnet, Haiku).

Features:
- Lazy loading of Anthropic SDK
- Separate system message handling
- Tool use (Anthropic's function calling)
- Thinking/reasoning features
- Streaming support
- Async support with AsyncAnthropic

Example:
    >>> from nimbus.providers.llm.anthropic_provider import AnthropicProvider
    >>> from nimbus.completion import CompletionRequest
    >>> from nimbus.messages import UserMessage
    >>>
    >>> provider = AnthropicProvider(api_key="sk-ant-...")
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="claude-3-opus-20240229"
    ... )
    >>> response = provider.complete(request)
    >>> print(response.content)
"""

from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from nimbus.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.messages import AssistantMessage
from nimbus.providers.base import BaseModelProvider
from nimbus.providers.lazy_import import LazyImporter

# Import CapabilityCall for capability call extraction
try:
    from nimbus.capabilities.capability_models import CapabilityCall
    CAPABILITIES_AVAILABLE = True
except ImportError:
    CAPABILITIES_AVAILABLE = False


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
        super().__init__(
            api_key=api_key,
            **kwargs
        )
        self.api_key = api_key
    
    def _initialize_client(self) -> Any:
        """Initialize Anthropic client with lazy import.
        
        Returns:
            Initialized Anthropic client
        """
        anthropic = LazyImporter.import_module("anthropic", install_extra="anthropic")
        return anthropic.Anthropic(api_key=self.api_key)
    
    def _transform_messages(self, messages: list[Any]) -> tuple[str | None, list[dict[str, Any]]]:
        """Transform Nimbus messages to Anthropic format.
        
        Anthropic requires the system message to be passed separately from
        the conversation messages. Tool results are formatted as user messages
        with special content blocks.
        
        Args:
            messages: List of Nimbus message objects
            
        Returns:
            Tuple of (system_message, anthropic_messages) where system_message
            is a string or None, and anthropic_messages is a list of dicts
        """
        from nimbus.messages import AssistantMessage, CapabilityMessage, SystemMessage
        
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
        """Transform Nimbus capabilities to Anthropic tool use format.
        
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
    
    def _extract_capability_calls(self, response: Any) -> list[Any] | None:
        """Extract capability calls from Anthropic response.
        
        Parses tool use blocks from the Anthropic response format and converts them
        to Nimbus CapabilityCall objects.
        
        Args:
            response: Anthropic response object
            
        Returns:
            List of CapabilityCall objects, or None if no capability calls
        """
        if not CAPABILITIES_AVAILABLE:
            return None
        
        capability_calls = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                capability_calls.append(
                    CapabilityCall(
                        id=content_block.id,
                        name=content_block.name,
                        arguments=content_block.input
                    )
                )
        
        return capability_calls if capability_calls else None
    
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to Anthropic format.
        
        Anthropic requires system messages to be passed separately from the
        conversation messages.
        
        Args:
            request: The nimbus CompletionRequest
            
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
                raise ValueError("Capabilities module not installed. Install with: pip install nimbus[capabilities]")
            
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
            CompletionResponse in nimbus format
        """
        # Extract content
        content_text = ""
        capability_calls_metadata = []
        
        for content_block in response.content:
            if content_block.type == "text":
                content_text += content_block.text
            elif content_block.type == "tool_use":
                # Store in metadata for compatibility
                capability_calls_metadata.append({
                    "id": content_block.id,
                    "type": "function",
                    "function": {
                        "name": content_block.name,
                        "arguments": content_block.input
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
                "stop_sequence": response.stop_sequence,
                "tool_calls": capability_calls_metadata if capability_calls_metadata else None,
                "content": [
                    {
                        "type": block.type,
                        "id": getattr(block, "id", None),
                        "name": getattr(block, "name", None),
                        "input": getattr(block, "input", None),
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
            StreamChunk in nimbus format
        """
        # Anthropic streaming uses events, we need to handle different event types
        delta_content = ""
        finish_reason = None
        
        if chunk.type == "content_block_delta":
            if hasattr(chunk.delta, "text"):
                delta_content = chunk.delta.text
        elif chunk.type == "message_delta":
            if hasattr(chunk.delta, "stop_reason"):
                finish_reason = chunk.delta.stop_reason
        
        return StreamChunk(
            id=getattr(chunk, "message_id", ""),
            delta=delta_content,
            finish_reason=finish_reason,
            index=getattr(chunk, "index", 0)
        )
    
    def _call_provider(self, request: dict[str, Any]) -> Any:
        """Call Anthropic API.
        
        Args:
            request: Provider-specific request dictionary
            
        Returns:
            Anthropic response object
        """
        return self.client.messages.create(**request)
    
    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Call Anthropic streaming API.
        
        Args:
            request: Provider-specific request dictionary
            
        Yields:
            Anthropic stream events
        """
        # Anthropic uses context manager for streaming
        with self.client.messages.stream(**request) as stream:
            for event in stream:
                yield event
    
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute asynchronous completion using AsyncAnthropic.
        
        Args:
            request: The completion request
            
        Returns:
            CompletionResponse with the model's output
        """
        anthropic = LazyImporter.import_module("anthropic", install_extra="anthropic")
        async_client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        provider_request = self._transform_request(request)
        response = await async_client.messages.create(**provider_request)
        return self._transform_response(response)
    
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
