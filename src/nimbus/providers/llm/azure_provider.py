"""Azure OpenAI provider implementation.

This module provides the Azure OpenAI implementation of the ModelInterface,
supporting GPT-4, GPT-3.5, and other Azure OpenAI models.

Features:
- Lazy loading of Azure SDK
- Azure-specific configuration (endpoint, deployment, API version)
- Structured outputs via response_format
- Function/tool calling
- Streaming support
- Async support with AsyncAzureOpenAI
- Multimodal inputs (images)

Example:
    >>> from nimbus.providers.llm.azure_provider import AzureOpenAIProvider
    >>> from nimbus.completion import CompletionRequest
    >>> from nimbus.messages import UserMessage
    >>>
    >>> provider = AzureOpenAIProvider(
    ...     azure_endpoint="https://myresource.openai.azure.com/",
    ...     api_key="...",
    ...     api_version="2024-02-15-preview",
    ...     deployment_name="gpt-4"
    ... )
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


class AzureOpenAIProvider(BaseModelProvider):
    """Azure OpenAI provider implementation.
    
    Implements the ModelInterface for Azure OpenAI's API, supporting all GPT models
    deployed on Azure OpenAI Service.
    
    Args:
        azure_endpoint: Azure OpenAI endpoint URL (e.g., https://myresource.openai.azure.com/)
        api_key: Azure OpenAI API key
        api_version: Azure OpenAI API version (e.g., 2024-02-15-preview)
        deployment_name: Name of the deployment (e.g., gpt-4)
        **kwargs: Additional configuration parameters
    
    Example:
        >>> provider = AzureOpenAIProvider(
        ...     azure_endpoint="https://myresource.openai.azure.com/",
        ...     api_key="...",
        ...     api_version="2024-02-15-preview",
        ...     deployment_name="gpt-4"
        ... )
        >>> response = provider.complete(request)
    """
    
    def __init__(
        self,
        azure_endpoint: str,
        api_key: str,
        api_version: str,
        deployment_name: str,
        **kwargs: Any
    ) -> None:
        """Initialize Azure OpenAI provider.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            api_version: Azure OpenAI API version
            deployment_name: Name of the deployment
            **kwargs: Additional configuration parameters
        """
        super().__init__(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment_name=deployment_name,
            **kwargs
        )
        self.azure_endpoint = azure_endpoint
        self.api_key = api_key
        self.api_version = api_version
        self.deployment_name = deployment_name
    
    def _initialize_client(self) -> Any:
        """Initialize Azure OpenAI client with lazy import.
        
        Returns:
            Initialized Azure OpenAI client
        """
        openai = LazyImporter.import_module("openai", install_extra="openai")
        return openai.AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )
    
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to Azure OpenAI format.
        
        Args:
            request: The nimbus CompletionRequest
            
        Returns:
            Dictionary in Azure OpenAI API format
        """
        # Ensure messages are available
        if not request.messages:
            raise ValueError("messages must be provided for Azure OpenAI provider")
        
        azure_request: dict[str, Any] = {
            "model": self.deployment_name,
            "messages": MessageTransformer.to_openai_format(request.messages),
            "temperature": request.temperature,
            "stream": request.stream
        }
        
        if request.max_tokens:
            azure_request["max_tokens"] = request.max_tokens
        
        if request.top_p:
            azure_request["top_p"] = request.top_p
        
        if request.stop:
            azure_request["stop"] = request.stop
        
        # Handle structured outputs
        if request.response_schema:
            schema = request.response_schema.model_json_schema()
            azure_request["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.response_schema.__name__,
                    "schema": schema,
                    "strict": True
                }
            }
        elif request.response_format:
            azure_request["response_format"] = request.response_format
        
        # Handle function calling
        if request.capabilities:
            azure_request["tools"] = request.capabilities
            if request.capability_choice:
                azure_request["tool_choice"] = request.capability_choice
        
        # Provider-specific metadata
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith("azure_"):
                    azure_request[key[6:]] = value
        
        return azure_request
    
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform Azure OpenAI response to CompletionResponse.
        
        Args:
            response: The Azure OpenAI response object
            
        Returns:
            CompletionResponse in nimbus format
        """
        choice = response.choices[0]
        message = choice.message
        
        # Parse structured output if present
        structured_output = None
        if hasattr(message, "parsed") and message.parsed:
            structured_output = message.parsed
        
        # Extract tool calls if present
        tool_calls = None
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = [
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
        
        return CompletionResponse(
            id=response.id,
            model=response.model,
            provider="azure",
            content=message.content or "",
            structured_output=structured_output,
            role="assistant",
            finish_reason=choice.finish_reason,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            ),
            created_at=datetime.fromtimestamp(response.created, tz=timezone.utc),
            metadata={
                "tool_calls": tool_calls
            }
        )
    
    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform Azure OpenAI stream chunk to StreamChunk.
        
        Args:
            chunk: The Azure OpenAI stream chunk
            
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
        """Call Azure OpenAI API.
        
        Args:
            request: Provider-specific request dictionary
            
        Returns:
            Azure OpenAI response object
        """
        return self.client.chat.completions.create(**request)
    
    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Call Azure OpenAI streaming API.
        
        Args:
            request: Provider-specific request dictionary
            
        Yields:
            Azure OpenAI stream chunks
        """
        return self.client.chat.completions.create(**request)  # type: ignore[no-any-return]
    
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute asynchronous completion using AsyncAzureOpenAI.
        
        Args:
            request: The completion request
            
        Returns:
            CompletionResponse with the model's output
        """
        openai = LazyImporter.import_module("openai", install_extra="openai")
        async_client = openai.AsyncAzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
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
            "provider": "azure",
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_structured_output": True,
            "supports_multimodal": True
        }
