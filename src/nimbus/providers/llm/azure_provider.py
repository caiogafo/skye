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
    
    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Transform Nimbus messages to Azure OpenAI format.
        
        Azure OpenAI uses the same format as OpenAI: a simple role-content format
        with tool calls as a separate field. System messages are included in the
        messages array.
        
        Args:
            messages: List of Nimbus message objects
            
        Returns:
            List of dictionaries in Azure OpenAI format
        """
        from nimbus.messages import AssistantMessage, CapabilityMessage
        
        result = []
        for msg in messages:
            if isinstance(msg, CapabilityMessage):
                result.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.capability_id,
                        "name": msg.capability_name,
                        "content": msg.content,
                    }
                )
            else:
                azure_msg: dict[str, Any] = {"role": msg.role, "content": msg.content}
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    azure_msg["tool_calls"] = msg.capability_calls
                result.append(azure_msg)
        return result
    
    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        """Transform Nimbus capabilities to Azure OpenAI function calling format.
        
        Azure OpenAI uses the same format as OpenAI: a nested structure with
        "type": "function" and a "function" object containing the tool definition.
        
        Args:
            capabilities: List of CapabilityInterface objects or dicts
            
        Returns:
            List of tool definitions in Azure OpenAI format
        """
        tools = []
        for capability in capabilities:
            # Handle both CapabilityInterface objects and dict format
            if isinstance(capability, dict):
                # Already in dict format, pass through
                tools.append(capability)
            else:
                # CapabilityInterface object, convert to Azure OpenAI format
                schema = capability.get_schema()
                tool = {
                    "type": "function",
                    "function": {
                        "name": schema.name,
                        "description": schema.description,
                        "parameters": schema.parameters or {
                            "type": "object",
                            "properties": {},
                        },
                    },
                }
                tools.append(tool)
        return tools
    
    def _extract_capability_calls(self, response: Any) -> list[Any] | None:
        """Extract capability calls from Azure OpenAI response.
        
        Azure OpenAI uses the same format as OpenAI for tool calls.
        
        Args:
            response: Azure OpenAI response object
            
        Returns:
            List of CapabilityCall objects, or None if no capability calls
        """
        choice = response.choices[0]
        message = choice.message
        
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            return None
        
        from nimbus.capabilities.capability_models import CapabilityCall
        import json
        
        capability_calls = []
        for tc in message.tool_calls:
            # Parse arguments JSON string
            try:
                arguments = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                # If parsing fails, use empty dict
                arguments = {}
            
            capability_calls.append(
                CapabilityCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=arguments
                )
            )
        
        return capability_calls
    
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
            "messages": self._transform_messages(request.messages),
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
        
        # Handle capabilities/tool calling (Azure uses OpenAI-compatible format)
        if request.capabilities:
            # Convert capabilities to Azure/OpenAI format using internal method
            azure_request["tools"] = self._transform_capabilities(request.capabilities)
            
            # Handle capability_choice parameter
            if request.capability_choice:
                if request.capability_choice in ["auto", "required"]:
                    # Standard values
                    azure_request["tool_choice"] = request.capability_choice
                else:
                    # Specific capability name - Azure expects {"type": "function", "function": {"name": "capability_name"}}
                    azure_request["tool_choice"] = {
                        "type": "function",
                        "function": {"name": request.capability_choice}
                    }
        
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
        
        # Extract capability calls using internal method
        tool_calls_list = self._extract_capability_calls(response)
        
        # Store raw tool calls in metadata for compatibility
        tool_calls_metadata = None
        if hasattr(message, "tool_calls") and message.tool_calls:
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
            capability_calls=tool_calls_list,
            created_at=datetime.fromtimestamp(response.created, tz=timezone.utc),
            metadata={
                "tool_calls": tool_calls_metadata
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
    
    def format_capability_results(self, results: list[Any]) -> list[dict[str, Any]]:
        """Format capability results for Azure OpenAI.
        
        Azure OpenAI uses the same format as OpenAI:
        {
            "tool_call_id": "call_123",
            "role": "tool",
            "content": "{\"result\": \"value\"}"
        }
        
        Args:
            results: List of CapabilityResult objects
            
        Returns:
            List of formatted result dictionaries in Azure OpenAI format
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
                "tool_call_id": result.capability_call_id,
                "role": "tool",
                "content": content,
            })

        return formatted
    
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
