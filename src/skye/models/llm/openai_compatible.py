"""The OpenAI wire format, for any endpoint that speaks it (structure task 4.3).

One parametrized adapter, ``OpenAICompatibleProvider``, serves every OpenAI wire-compatible
endpoint (vLLM, Ollama, LM Studio, Together, ...), keyed by ``api_base`` + ``api_key``. What belongs to
one vendor lives beside it: ``openai.py`` (``OpenAIProvider``) and ``azure.py`` (``AzureOpenAIProvider``).

Features:
- Standard-library REST transport (no vendor SDK)
- Structured outputs via response_format
- Function calling
- Streaming support
- Async support (sync call run in an executor)
- Multimodal inputs (images)

Example:
    >>> from skye.models.llm.openai_compatible import OpenAICompatibleProvider
    >>> from skye.base.completion import CompleteRequest
    >>> from skye.base.messages import UserMessage
    >>>
    >>> provider = OpenAICompatibleProvider(api_key="sk-...", api_base="http://localhost:8000/v1")
    >>> request = CompleteRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gpt-4"
    ... )
    >>> response = provider.complete(request)
    >>> print(response.content)
"""

import asyncio
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from skye.base.completion import CompleteRequest, CompleteResponse, StreamChunk, TokenUsage
from skye.base.exceptions import ConfigurationError
from skye.base.messages import AssistantMessage
from skye.models.base import BaseModelProvider
from skye.models.transport.structured import schema_of, strict_schema
from skye.models.transport import rest


class OpenAICompatibleProvider(BaseModelProvider):
    """Provider for any endpoint that speaks the OpenAI chat-completions format.

    Args:
        api_key: Key sent as a bearer token
        api_base: Base URL of the endpoint, up to and including ``/v1``
        **kwargs: Additional configuration parameters

    Example:
        >>> provider = OpenAICompatibleProvider(api_key="none", api_base="http://localhost:8000/v1")
        >>> response = provider.complete(request)
    """

    #: Base URL used when ``api_base`` is not given; a vendor subclass sets it.
    default_api_base: str | None = None
    #: Provider label reported in responses / model info.
    provider_name = "openai_compatible"
    #: Metadata keys with this prefix are forwarded to the API as extra params.
    metadata_prefix = "openai_"
    #: Whether response metadata carries ``system_fingerprint``.
    reports_fingerprint = False

    def __init__(self, api_key: str, api_base: str | None = None, **kwargs: Any) -> None:
        """Initialize the provider.

        Args:
            api_key: Key sent as a bearer token
            api_base: Base URL of the endpoint (default: ``default_api_base``)
            **kwargs: Additional configuration parameters
        """
        super().__init__(api_key=api_key, api_base=api_base, **kwargs)
        self.api_key = api_key
        self.api_base = api_base

    def _initialize_client(self) -> Any:
        """No vendor client: requests go through the standard-library REST transport."""
        return None

    def _endpoint_url(self) -> str:
        """Chat-completions URL."""
        base = self.api_base or self.default_api_base
        if not base:
            raise ConfigurationError("api_base is required for an OpenAI-compatible endpoint")
        return f"{base.rstrip('/')}/chat/completions"

    def _auth_headers(self) -> dict[str, str]:
        """Authentication headers for the endpoint."""
        return {"Authorization": f"Bearer {self.api_key}"}

    def _model_name(self, request: CompleteRequest) -> str:
        """Model identifier sent to the endpoint."""
        return request.model
    
    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Transform Skye messages to OpenAI format.
        
        OpenAI uses a simple role-content format with capability calls as a separate field.
        System messages are included in the messages array.
        
        Args:
            messages: List of Skye message objects
            
        Returns:
            List of dictionaries in OpenAI format
        """
        from skye.base.messages import AssistantMessage, CapabilityMessage
        
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
                openai_msg: dict[str, Any] = {"role": msg.role, "content": msg.content}
                images = getattr(msg, "images", None)
                if images:
                    from skye.models.transport.multimodal import ImageHandler

                    openai_msg["content"] = [
                        {"type": "text", "text": msg.content},
                        *(ImageHandler.to_openai_format(image) for image in images),
                    ]
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    openai_msg["tool_calls"] = msg.capability_calls
                result.append(openai_msg)
        return result
    
    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        """Transform Skye capabilities to OpenAI function calling format.
        
        OpenAI uses a nested structure with "type": "function" and a "function"
        object containing the tool definition.
        
        Args:
            capabilities: List of CapabilityInterface objects or dicts
            
        Returns:
            List of tool definitions in OpenAI format
        """
        tools = []
        for capability in capabilities:
            # Handle both CapabilityInterface objects and dict format
            if isinstance(capability, dict):
                # Already in dict format, pass through
                tools.append(capability)
            else:
                # CapabilityInterface object, convert to OpenAI format
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
        """Extract capability calls from OpenAI response.
        
        Parses capability calls from the OpenAI response format and converts them
        to Skye CapabilityCall objects.
        
        Args:
            response: OpenAI response object
            
        Returns:
            List of CapabilityCall objects, or None if no capability calls
        """
        choice = response.choices[0]
        message = choice.message
        
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            return None
        
        from skye.base.completion import CapabilityCall
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
    
    def _transform_request(self, request: CompleteRequest) -> dict[str, Any]:
        """Transform CompleteRequest to OpenAI format.
        
        Args:
            request: The skye CompleteRequest
            
        Returns:
            Dictionary in OpenAI API format
        """
        # Ensure messages are available
        if not request.messages:
            raise ValueError("messages must be provided for OpenAI provider")
        
        openai_request: dict[str, Any] = {
            "model": self._model_name(request),
            "messages": self._transform_messages(request.messages),
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
            schema = schema_of(request.response_schema)
            strict = strict_schema(schema)
            openai_request["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.response_schema.__name__,
                    "schema": strict or schema,
                    "strict": strict is not None
                }
            }
        elif request.response_format:
            openai_request["response_format"] = request.response_format
        
        # Handle capabilities/tool calling
        if request.capabilities:
            # Convert capabilities to OpenAI format using internal method
            openai_request["tools"] = self._transform_capabilities(request.capabilities)
            
            # Handle capability_choice parameter
            if request.capability_choice:
                if request.capability_choice in ["auto", "required"]:
                    # Standard values
                    openai_request["tool_choice"] = request.capability_choice
                else:
                    # Specific capability name - OpenAI expects {"type": "function", "function": {"name": "capability_name"}}
                    openai_request["tool_choice"] = {
                        "type": "function",
                        "function": {"name": request.capability_choice}
                    }
        
        # Provider-specific metadata
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith(self.metadata_prefix):
                    openai_request[key[len(self.metadata_prefix):]] = value
        
        return openai_request
    
    def _transform_response(self, response: Any) -> CompleteResponse:
        """Transform OpenAI response to CompleteResponse.
        
        Args:
            response: The OpenAI response object
            
        Returns:
            CompleteResponse in skye format
        """
        choice = response.choices[0]
        message = choice.message
        
        # Parse structured output if present
        structured_output = None
        if hasattr(message, "parsed") and message.parsed:
            structured_output = message.parsed
        
        # Extract capability calls using internal method
        capability_calls_list = self._extract_capability_calls(response)
        
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
        
        return CompleteResponse(
            id=response.id,
            model=response.model,
            provider=self.provider_name,
            content=message.content or "",
            structured_output=structured_output,
            role="assistant",
            finish_reason=choice.finish_reason,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            ),
            capability_calls=capability_calls_list,
            created_at=datetime.fromtimestamp(response.created, tz=timezone.utc),
            metadata=self._response_metadata(response, tool_calls_metadata)
        )
    
    def _response_metadata(self, response: Any, tool_calls: Any) -> dict[str, Any]:
        """Response metadata; ``system_fingerprint`` only where the endpoint reports it."""
        metadata: dict[str, Any] = {}
        if self.reports_fingerprint:
            metadata["system_fingerprint"] = getattr(response, "system_fingerprint", None)
        metadata["tool_calls"] = tool_calls
        return metadata

    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform OpenAI stream chunk to StreamChunk.
        
        Args:
            chunk: The OpenAI stream chunk
            
        Returns:
            StreamChunk in skye format
        """
        # The API omits keys it has nothing to say about: the last chunk has `"delta": {}`, and a usage-only chunk has no choices.
        chunk_id = getattr(chunk, "id", "")
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            return StreamChunk(id=chunk_id, delta="", finish_reason=None, index=0)
        choice = choices[0]
        delta = getattr(choice, "delta", None)

        return StreamChunk(
            id=chunk_id,
            delta=(getattr(delta, "content", None) or "") if delta is not None else "",
            finish_reason=getattr(choice, "finish_reason", None),
            index=getattr(choice, "index", 0),
        )
    
    def _call_provider(self, request: dict[str, Any]) -> Any:
        """POST to the chat-completions endpoint and return the decoded JSON view."""
        return rest.post_json(
            self._endpoint_url(), request, headers=self._auth_headers(), provider=self.provider_name
        )

    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Stream the chat-completions endpoint (SSE), yielding decoded chunks."""
        return rest.stream_sse_json(
            self._endpoint_url(),
            {**request, "stream": True},
            headers=self._auth_headers(),
            provider=self.provider_name,
        )

    async def acomplete(
        self,
        messages: list[Any] | str | CompleteRequest | None = None,
        model: str | None = None,
        router: Any | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompleteResponse:
        """Run :meth:`complete` in an executor so the event loop is not blocked.

        Takes the same arguments as :meth:`complete`: ``messages=..., model=...`` or a ``CompleteRequest``.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.complete(messages, model, router, temperature, max_tokens, **kwargs))

    def format_capability_results(self, results: list[Any]) -> list[dict[str, Any]]:
        """Format capability results for OpenAI.
        
        OpenAI expects tool results in this format:
        {
            "tool_call_id": "call_123",
            "role": "tool",
            "content": "{\"result\": \"value\"}"
        }
        
        Args:
            results: List of CapabilityResult objects
            
        Returns:
            List of formatted result dictionaries in OpenAI format
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
            "provider": self.provider_name,
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_structured_output": True,
            "supports_multimodal": True
        }


__all__ = ["OpenAICompatibleProvider"]
