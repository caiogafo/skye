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
from nimbus.providers.transformers import MessageTransformer


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
        
        # Transform messages and extract system message
        system, anthropic_messages = MessageTransformer.to_anthropic_format(request.messages)
        
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
            # Convert OpenAI-style tools to Anthropic format
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
            
            # Handle tool choice
            if request.capability_choice:
                if request.capability_choice == "auto":
                    anthropic_request["tool_choice"] = {"type": "auto"}
                elif request.capability_choice == "required":
                    anthropic_request["tool_choice"] = {"type": "any"}
                elif isinstance(request.capability_choice, dict):
                    # Specific tool choice
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
        tool_calls = None
        
        for content_block in response.content:
            if content_block.type == "text":
                content_text += content_block.text
            elif content_block.type == "tool_use":
                # Convert tool use to OpenAI-style tool calls format
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append({
                    "id": content_block.id,
                    "type": "function",
                    "function": {
                        "name": content_block.name,
                        "arguments": content_block.input
                    }
                })
        
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
            metadata={
                "stop_sequence": response.stop_sequence,
                "tool_calls": tool_calls
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
