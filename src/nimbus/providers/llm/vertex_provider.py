"""Vertex AI provider implementation.

This module provides the Vertex AI (Google Cloud) implementation of the ModelInterface,
supporting Gemini and other Vertex AI models.

Features:
- Lazy loading of Vertex AI SDK
- Support for Gemini models
- Safety settings configuration
- Grounding features
- Streaming support
- Async support
- Multimodal inputs (images, video)

Example:
    >>> from nimbus.providers.llm.vertex_provider import VertexAIProvider
    >>> from nimbus.completion import CompletionRequest
    >>> from nimbus.messages import UserMessage
    >>>
    >>> provider = VertexAIProvider(
    ...     project_id="my-project",
    ...     location="us-central1"
    ... )
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gemini-1.5-pro"
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


class VertexAIProvider(BaseModelProvider):
    """Vertex AI provider implementation.

    Implements the ModelInterface for Google Cloud's Vertex AI API, supporting
    Gemini models and other Vertex AI generative models.

    Args:
        project_id: Google Cloud project ID
        location: Google Cloud region (e.g., 'us-central1')
        credentials: Optional credentials object. If not provided, uses default
                    application credentials from the environment.
        **kwargs: Additional configuration parameters

    Example:
        >>> provider = VertexAIProvider(
        ...     project_id="my-project",
        ...     location="us-central1"
        ... )
        >>> response = provider.complete(request)
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        credentials: Any = None,
        **kwargs: Any
    ) -> None:
        """Initialize Vertex AI provider.

        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region (default: us-central1)
            credentials: Optional credentials object
            **kwargs: Additional configuration parameters
        """
        super().__init__(
            project_id=project_id,
            location=location,
            credentials=credentials,
            **kwargs
        )
        self.project_id = project_id
        self.location = location
        self.credentials = credentials

    def _initialize_client(self) -> Any:
        """Initialize Vertex AI client with lazy import.

        Returns:
            Initialized Vertex AI GenerativeModel client
        """
        vertexai = LazyImporter.import_module(
            "google.cloud.aiplatform",
            package_name="google-cloud-aiplatform",
            install_extra="vertex"
        )

        # Initialize Vertex AI
        vertexai.init(
            project=self.project_id,
            location=self.location,
            credentials=self.credentials
        )

        # Return the GenerativeModel class for creating model instances
        return vertexai.generative_models

    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to Vertex AI format.

        Args:
            request: The nimbus CompletionRequest

        Returns:
            Dictionary in Vertex AI API format
        """
        if not request.messages:
            raise ValueError("messages must be provided for Vertex AI provider")

        vertex_request: dict[str, Any] = {
            "model": request.model,
            "messages": MessageTransformer.to_vertex_format(request.messages),
            "generation_config": {
                "temperature": request.temperature,
            }
        }

        if request.max_tokens:
            vertex_request["generation_config"]["max_output_tokens"] = request.max_tokens

        if request.top_p:
            vertex_request["generation_config"]["top_p"] = request.top_p

        if request.stop:
            vertex_request["generation_config"]["stop_sequences"] = request.stop

        # Handle safety settings
        if request.metadata and "safety_settings" in request.metadata:
            vertex_request["safety_settings"] = request.metadata["safety_settings"]

        # Handle grounding features
        if request.metadata and "grounding" in request.metadata:
            vertex_request["grounding"] = request.metadata["grounding"]

        # Handle function calling
        if request.capabilities:
            vertex_request["tools"] = [
                {
                    "function_declarations": request.capabilities
                }
            ]

        # Provider-specific metadata
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith("vertex_"):
                    vertex_request[key[7:]] = value

        return vertex_request

    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform Vertex AI response to CompletionResponse.

        Args:
            response: The Vertex AI response object

        Returns:
            CompletionResponse in nimbus format
        """
        # Extract content from the response
        content = ""
        finish_reason = "stop"
        tool_calls = None

        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]

            # Extract finish reason
            if hasattr(candidate, "finish_reason"):
                finish_reason_str = str(candidate.finish_reason).lower()
                # Only set finish_reason if it's not "none"
                if finish_reason_str != "none":
                    finish_reason = finish_reason_str

            # Extract content from parts
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text is not None:
                        content = part.text
                    elif hasattr(part, "function_call"):
                        # Handle function calls
                        func_call = part.function_call
                        tool_calls = [
                            {
                                "id": getattr(func_call, "name", ""),
                                "type": "function",
                                "function": {
                                    "name": getattr(func_call, "name", ""),
                                    "arguments": getattr(func_call, "args", {})
                                }
                            }
                        ]

        # Extract usage information
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", 0)
            completion_tokens = getattr(usage, "candidates_token_count", 0)
            total_tokens = getattr(usage, "total_token_count", 0)

        return CompletionResponse(
            id=getattr(response, "name", ""),
            model=getattr(response, "model", ""),
            provider="vertex",
            content=content,
            structured_output=None,
            role="assistant",
            finish_reason=finish_reason,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            ),
            created_at=datetime.now(tz=timezone.utc),
            metadata={
                "tool_calls": tool_calls
            }
        )

    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform Vertex AI stream chunk to StreamChunk.

        Args:
            chunk: The Vertex AI stream chunk

        Returns:
            StreamChunk in nimbus format
        """
        content = ""
        finish_reason: str | None = None

        if hasattr(chunk, "candidates") and chunk.candidates:
            candidate = chunk.candidates[0]

            # Extract finish reason
            if hasattr(candidate, "finish_reason"):
                finish_reason_str = str(candidate.finish_reason).lower()
                # Only set finish_reason if it's not "none"
                if finish_reason_str != "none":
                    finish_reason = finish_reason_str

            # Extract content from parts
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text is not None:
                        content = part.text

        return StreamChunk(
            id="",
            delta=content,
            finish_reason=finish_reason,
            index=0
        )

    def _call_provider(self, request: dict[str, Any]) -> Any:
        """Call Vertex AI API.

        Args:
            request: Provider-specific request dictionary

        Returns:
            Vertex AI response object
        """
        generative_models = self.client
        model_name = request.pop("model")

        # Create the model instance
        model = generative_models.GenerativeModel(model_name)

        # Extract generation config and other parameters
        generation_config = request.pop("generation_config", {})
        safety_settings = request.pop("safety_settings", None)
        grounding = request.pop("grounding", None)
        tools = request.pop("tools", None)
        messages = request.pop("messages", [])

        # Build the generate_content call
        call_kwargs: dict[str, Any] = {
            "contents": messages,
            "generation_config": generation_config,
        }

        if safety_settings:
            call_kwargs["safety_settings"] = safety_settings

        if grounding:
            call_kwargs["grounding"] = grounding

        if tools:
            call_kwargs["tools"] = tools

        return model.generate_content(**call_kwargs)

    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Call Vertex AI streaming API.

        Args:
            request: Provider-specific request dictionary

        Yields:
            Vertex AI stream chunks
        """
        generative_models = self.client
        model_name = request.pop("model")

        # Create the model instance
        model = generative_models.GenerativeModel(model_name)

        # Extract generation config and other parameters
        generation_config = request.pop("generation_config", {})
        safety_settings = request.pop("safety_settings", None)
        grounding = request.pop("grounding", None)
        tools = request.pop("tools", None)
        messages = request.pop("messages", [])

        # Build the generate_content call with streaming
        call_kwargs: dict[str, Any] = {
            "contents": messages,
            "generation_config": generation_config,
            "stream": True,
        }

        if safety_settings:
            call_kwargs["safety_settings"] = safety_settings

        if grounding:
            call_kwargs["grounding"] = grounding

        if tools:
            call_kwargs["tools"] = tools

        return model.generate_content(**call_kwargs)  # type: ignore[no-any-return]

    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute asynchronous completion.

        Args:
            request: The completion request

        Returns:
            CompletionResponse with the model's output
        """
        # For now, use sync version
        # Vertex AI SDK has async support but requires additional setup
        return self.complete(request)

    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata and capabilities.

        Returns:
            Dictionary with provider information and capabilities
        """
        return {
            "provider": "vertex",
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_structured_output": False,
            "supports_multimodal": True
        }
