"""OpenAI provider implementation.

This module provides the OpenAI implementation of the ModelInterface,
supporting GPT-4, GPT-3.5, o1, o3, and other OpenAI models.

Features:
- Lazy loading of OpenAI SDK
- Structured outputs via response_format
- Function/tool calling
- Streaming support
- Async support with AsyncOpenAI
- Multimodal inputs (images)

Example:
    >>> from nimbus.providers.llm.openai_provider import OpenAIProvider
    >>> from nimbus.completion import CompletionRequest
    >>> from nimbus.messages import UserMessage
    >>>
    >>> provider = OpenAIProvider(api_key="sk-...")
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gpt-4"
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


class OpenAIProvider(BaseModelProvider):
    """OpenAI provider implementation.
    
    Implements the ModelInterface for OpenAI's API, supporting all GPT models
    including GPT-4, GPT-3.5-turbo, o1, and o3 series.
    
    Args:
        api_key: OpenAI API key
        api_base: Optional custom API base URL
        organization: Optional organization ID
        **kwargs: Additional configuration parameters
    
    Example:
        >>> provider = OpenAIProvider(api_key="sk-...")
        >>> response = provider.complete(request)
    """
    
    def __init__(
        self,
        api_key: str,
        api_base: str | None = None,
        organization: str | None = None,
        **kwargs: Any
    ) -> None:
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            api_base: Optional custom API base URL
            organization: Optional organization ID
            **kwargs: Additional configuration parameters
        """
        super().__init__(
            api_key=api_key,
            api_base=api_base,
            organization=organization,
            **kwargs
        )
        self.api_key = api_key
        self.api_base = api_base
        self.organization = organization
    
    def _initialize_client(self) -> Any:
        """Initialize OpenAI client with lazy import.
        
        Returns:
            Initialized OpenAI client
        """
        openai = LazyImporter.import_module("openai", install_extra="openai")
        return openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            organization=self.organization
        )
    
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to OpenAI format.
        
        Args:
            request: The nimbus CompletionRequest
            
        Returns:
            Dictionary in OpenAI API format
        """
        # Ensure messages are available
        if not request.messages:
            raise ValueError("messages must be provided for OpenAI provider")
        
        openai_request: dict[str, Any] = {
            "model": request.model,
            "messages": MessageTransformer.to_openai_format(request.messages),
            "temperature": request.temperature,
            "stream": request.stream
        }
        
        if request.max_tokens:
            openai_request["max_tokens"] = request.max_tokens
        
        if request.top_p:
            openai_request["top_p"] = request.top_p
        
        if request.stop:
            openai_request["stop"] = request.stop
        
        # Handle structured outputs
        if request.response_schema:
            schema = request.response_schema.model_json_schema()
            openai_request["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.response_schema.__name__,
                    "schema": schema,
                    "strict": True
                }
            }
        elif request.response_format:
            openai_request["response_format"] = request.response_format
        
        # Handle capabilities/tool calling
        if request.capabilities:
            # Import ToolTransformer here to avoid circular dependency
            try:
                from nimbus.capabilities.tool_transformer import ToolTransformer
                
                # Convert capabilities to OpenAI format
                openai_request["tools"] = ToolTransformer.to_openai_format(request.capabilities)
                
                # Handle tool_choice parameter
                if request.tool_choice:
                    if request.tool_choice in ["auto", "required"]:
                        # Standard values
                        openai_request["tool_choice"] = request.tool_choice
                    else:
                        # Specific tool name - OpenAI expects {"type": "function", "function": {"name": "tool_name"}}
                        openai_request["tool_choice"] = {
                            "type": "function",
                            "function": {"name": request.tool_choice}
                        }
            except ImportError:
                # If capabilities package not installed, skip tool conversion
                pass
        
        # Provider-specific metadata
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith("openai_"):
                    openai_request[key[7:]] = value
        
        return openai_request
    
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform OpenAI response to CompletionResponse.
        
        Args:
            response: The OpenAI response object
            
        Returns:
            CompletionResponse in nimbus format
        """
        choice = response.choices[0]
        message = choice.message
        
        # Parse structured output if present
        structured_output = None
        if hasattr(message, "parsed") and message.parsed:
            structured_output = message.parsed
        
        # Extract tool calls if present and convert to ToolCall objects
        tool_calls_list = None
        tool_calls_metadata = None
        
        if hasattr(message, "tool_calls") and message.tool_calls:
            # Store raw tool calls in metadata for ToolCallHandler
            tool_calls_metadata = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
            
            # Try to convert to ToolCall objects if capabilities package is available
            try:
                from nimbus.capabilities.tool_models import ToolCall
                import json
                
                tool_calls_list = []
                for tc in message.tool_calls:
                    # Parse arguments JSON string
                    try:
                        arguments = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        # If parsing fails, use empty dict
                        arguments = {}
                    
                    tool_calls_list.append(
                        ToolCall(
                            id=tc.id,
                            name=tc.function.name,
                            arguments=arguments
                        )
                    )
            except ImportError:
                # If capabilities package not installed, tool_calls_list stays None
                pass
        
        return CompletionResponse(
            id=response.id,
            model=response.model,
            provider="openai",
            content=message.content or "",
            structured_output=structured_output,
            role="assistant",
            finish_reason=choice.finish_reason,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            ),
            tool_calls=tool_calls_list,
            created_at=datetime.fromtimestamp(response.created, tz=timezone.utc),
            metadata={
                "system_fingerprint": getattr(response, "system_fingerprint", None),
                "tool_calls": tool_calls_metadata
            }
        )
    
    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform OpenAI stream chunk to StreamChunk.
        
        Args:
            chunk: The OpenAI stream chunk
            
        Returns:
            StreamChunk in nimbus format
        """
        choice = chunk.choices[0]
        delta = choice.delta
        
        return StreamChunk(
            id=chunk.id,
            delta=delta.content or "",
            finish_reason=choice.finish_reason,
            index=choice.index
        )
    
    def _call_provider(self, request: dict[str, Any]) -> Any:
        """Call OpenAI API.
        
        Args:
            request: Provider-specific request dictionary
            
        Returns:
            OpenAI response object
        """
        return self.client.chat.completions.create(**request)
    
    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Call OpenAI streaming API.
        
        Args:
            request: Provider-specific request dictionary
            
        Yields:
            OpenAI stream chunks
        """
        return self.client.chat.completions.create(**request)  # type: ignore[no-any-return]
    
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute asynchronous completion using AsyncOpenAI.
        
        Args:
            request: The completion request
            
        Returns:
            CompletionResponse with the model's output
        """
        openai = LazyImporter.import_module("openai", install_extra="openai")
        async_client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            organization=self.organization
        )
        
        provider_request = self._transform_request(request)
        response = await async_client.chat.completions.create(**provider_request)
        return self._transform_response(response)
    
    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata and capabilities.
        
        Returns:
            Dictionary with provider information and capabilities
        """
        return {
            "provider": "openai",
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_structured_output": True,
            "supports_multimodal": True
        }
