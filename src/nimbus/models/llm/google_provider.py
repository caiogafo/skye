"""Google (Gemini Enterprise Agent Platform, formerly Vertex AI) provider implementation.

Renamed from `vertex` (Google renamed Vertex AI to Gemini Enterprise Agent Platform in April 2026); the extra is now `google`.

This module provides the Google Cloud implementation of the ModelInterface,
supporting Gemini and other Google models.

Features:
- Lazy loading of Google SDK
- Support for Gemini models
- Safety settings configuration
- Grounding features
- Streaming support
- Async support
- Multimodal inputs (images, video)

Example:
    >>> from nimbus.models.llm.google_provider import GoogleProvider
    >>> from nimbus.base.completion import CompletionRequest
    >>> from nimbus.base.messages import UserMessage
    >>>
    >>> provider = GoogleProvider(
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

from nimbus.base.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.base.messages import AssistantMessage
from nimbus.models.base import BaseModelProvider
from nimbus.models.lazy_import import LazyImporter


class GoogleProvider(BaseModelProvider):
    """Google provider implementation.

    Implements the ModelInterface for Google Cloud's Google API, supporting
    Gemini models and other Google generative models.

    Args:
        project_id: Google Cloud project ID
        location: Google Cloud region (e.g., 'us-central1')
        credentials: Optional credentials object. If not provided, uses default
                    application credentials from the environment.
        **kwargs: Additional configuration parameters

    Example:
        >>> provider = GoogleProvider(
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
        model: str | None = None,
        router: Any | None = None,
        **kwargs: Any
    ) -> None:
        """Initialize Google provider.

        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region (default: us-central1)
            credentials: Optional credentials object
            model: Optional default model identifier (can be overridden in request)
            router: Optional model router for load balancing
            **kwargs: Additional configuration parameters
        """
        # For Google, model is typically specified in the request, not at init
        # If neither model nor router is provided, use a placeholder
        if model is None and router is None:
            model = "gemini-1.5-pro"  # Default model as placeholder
        
        super().__init__(
            model=model,
            router=router,
            project_id=project_id,
            location=location,
            credentials=credentials,
            **kwargs
        )
        self.project_id = project_id
        self.location = location
        self.credentials = credentials

    def _initialize_client(self) -> Any:
        """Initialize Google client with lazy import.

        Returns:
            Initialized Google GenerativeModel client
        """
        vertexai = LazyImporter.import_module(
            "google.cloud.aiplatform",
            package_name="google-cloud-aiplatform",
            install_extra="google"
        )

        # Initialize Google
        vertexai.init(
            project=self.project_id,
            location=self.location,
            credentials=self.credentials
        )

        # Return the GenerativeModel class for creating model instances
        return vertexai.generative_models
    
    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Transform Nimbus messages to Google (Gemini) format.
        
        Google uses a parts-based format where content is broken into parts.
        System instructions are typically handled separately in the API call.
        
        Args:
            messages: List of Nimbus message objects
            
        Returns:
            List of dictionaries in Google format
        """
        from nimbus.base.messages import AssistantMessage, CapabilityMessage, SystemMessage
        
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                # System messages are typically passed separately in Google
                # but we include them here for completeness
                result.append({"role": "system", "parts": [{"text": msg.content}]})
            elif isinstance(msg, CapabilityMessage):
                result.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": msg.capability_name,
                                    "response": {"content": msg.content},
                                }
                            }
                        ],
                    }
                )
            else:
                # Map assistant to model for Google
                role = "model" if msg.role == "assistant" else msg.role
                parts: list[dict[str, Any]] = [{"text": msg.content}]

                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    parts = [
                        {
                            "functionCall": {
                                "name": call["function"]["name"],
                                "args": call["function"]["arguments"],
                            }
                        }
                        for call in msg.capability_calls
                    ]

                result.append({"role": role, "parts": parts})
        return result
    
    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        """Transform Nimbus capabilities to Google Gemini format.
        
        Google uses a format with "name", "description", and "parameters"
        fields. The parameters field is the JSON Schema for parameters.
        
        Args:
            capabilities: List of CapabilityInterface objects or dicts
            
        Returns:
            List of tool definitions in Google format
        """
        tools = []
        for capability in capabilities:
            # Handle both CapabilityInterface objects and dict format
            if isinstance(capability, dict):
                # Check if already in Google format
                if "parameters" in capability and "function" not in capability:
                    tools.append(capability)
                else:
                    # Convert from OpenAI format to Google format
                    func = capability.get("function", {})
                    tool = {
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {
                            "type": "object",
                            "properties": {},
                        }),
                    }
                    tools.append(tool)
            else:
                # CapabilityInterface object, convert to Google format
                schema = capability.get_schema()
                tool = {
                    "name": schema.name,
                    "description": schema.description,
                    "parameters": schema.parameters or {
                        "type": "object",
                        "properties": {},
                    },
                }
                tools.append(tool)
        return tools
    
    def _extract_capability_calls(self, response: Any) -> list[Any] | None:
        """Extract capability calls from Google response.
        
        Parses function calls from the Google response format and converts them
        to Nimbus CapabilityCall objects.
        
        Args:
            response: Google response object
            
        Returns:
            List of CapabilityCall objects, or None if no capability calls
        """
        # Google response structure varies, need to check for function calls
        # This is a placeholder - actual implementation depends on Google SDK structure
        return None

    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to Google format.

        Args:
            request: The nimbus CompletionRequest

        Returns:
            Dictionary in Google API format
        """
        if not request.messages:
            raise ValueError("messages must be provided for Google provider")

        google_request: dict[str, Any] = {
            "model": request.model,
            "messages": self._transform_messages(request.messages),
            "generation_config": {
                "temperature": request.temperature,
            }
        }

        if request.max_tokens:
            google_request["generation_config"]["max_output_tokens"] = request.max_tokens

        if request.top_p:
            google_request["generation_config"]["top_p"] = request.top_p

        if request.stop:
            google_request["generation_config"]["stop_sequences"] = request.stop

        # Handle safety settings
        if request.metadata and "safety_settings" in request.metadata:
            google_request["safety_settings"] = request.metadata["safety_settings"]

        # Handle grounding features
        if request.metadata and "grounding" in request.metadata:
            google_request["grounding"] = request.metadata["grounding"]

        # Handle capabilities
        if request.capabilities:
            # Convert capabilities to Google format using internal method
            function_declarations = self._transform_capabilities(request.capabilities)
            google_request["tools"] = [
                {
                    "function_declarations": function_declarations
                }
            ]
            
            # Handle capability_choice parameter
            # Note: Google doesn't have direct capability_choice support like OpenAI
            # We can use function_calling_config for similar behavior
            if request.capability_choice:
                if request.capability_choice == "required":
                    # Force function calling
                    google_request["tool_config"] = {
                        "function_calling_config": {
                            "mode": "ANY"
                        }
                    }
                elif request.capability_choice == "auto":
                    # Let model decide
                    google_request["tool_config"] = {
                        "function_calling_config": {
                            "mode": "AUTO"
                        }
                    }
                elif request.capability_choice != "none":
                    # Specific capability name - use allowed_function_names
                    google_request["tool_config"] = {
                        "function_calling_config": {
                            "mode": "ANY",
                            "allowed_function_names": [request.capability_choice]
                        }
                    }

        # Provider-specific metadata
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith("google_"):
                    google_request[key[7:]] = value

        return google_request

    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform Google response to CompletionResponse.

        Args:
            response: The Google response object

        Returns:
            CompletionResponse in nimbus format
        """
        # Extract content from the response
        content = ""
        finish_reason = "stop"
        capability_calls_list = None
        capability_calls_metadata = None

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
                # Store function calls for metadata
                function_calls_raw = []
                
                for idx, part in enumerate(candidate.content.parts):
                    if hasattr(part, "text") and part.text is not None:
                        content = part.text
                    elif hasattr(part, "function_call"):
                        # Handle function calls
                        func_call = part.function_call
                        function_calls_raw.append({
                            "idx": idx,
                            "name": getattr(func_call, "name", ""),
                            "args": dict(getattr(func_call, "args", {}))
                        })
                
                # Store raw function calls in metadata for CapabilityCallHandler
                if function_calls_raw:
                    capability_calls_metadata = {
                        "candidates": [
                            {
                                "content": {
                                    "parts": [
                                        {
                                            "functionCall": {
                                                "name": fc["name"],
                                                "args": fc["args"]
                                            }
                                        }
                                        for fc in function_calls_raw
                                    ]
                                }
                            }
                        ]
                    }
                    
                    # Try to convert to CapabilityCall objects if capabilities package is available
                    try:
                        from nimbus.base.completion import CapabilityCall
                        
                        capability_calls_list = []
                        for fc in function_calls_raw:
                            # Generate ID since Google doesn't provide one
                            call_id = f"google_call_{fc['idx']}"
                            
                            capability_calls_list.append(
                                CapabilityCall(
                                    id=call_id,
                                    name=fc["name"],
                                    arguments=fc["args"]
                                )
                            )
                    except ImportError:
                        # If capabilities package not installed, capability_calls_list stays None
                        pass

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
            provider="google",
            content=content,
            structured_output=None,
            role="assistant",
            finish_reason=finish_reason,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            ),
            capability_calls=capability_calls_list,
            created_at=datetime.now(tz=timezone.utc),
            metadata=capability_calls_metadata or {}
        )

    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform Google stream chunk to StreamChunk.

        Args:
            chunk: The Google stream chunk

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
        """Call Google API.

        Args:
            request: Provider-specific request dictionary

        Returns:
            Google response object
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
        tool_config = request.pop("tool_config", None)
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

        if tool_config:
            call_kwargs["tool_config"] = tool_config

        return model.generate_content(**call_kwargs)

    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Call Google streaming API.

        Args:
            request: Provider-specific request dictionary

        Yields:
            Google stream chunks
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
        tool_config = request.pop("tool_config", None)
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

        if tool_config:
            call_kwargs["tool_config"] = tool_config

        return model.generate_content(**call_kwargs)  # type: ignore[no-any-return]

    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute asynchronous completion.

        Args:
            request: The completion request

        Returns:
            CompletionResponse with the model's output
        """
        # For now, use sync version
        # Google SDK has async support but requires additional setup
        return self.complete(request)

    def format_capability_results(self, results: list[Any]) -> list[dict[str, Any]]:
        """Format capability results for Google.
        
        Google expects tool results in this format:
        {
            "functionResponse": {
                "name": "get_weather",
                "response": {"result": "value"}
            }
        }
        
        Args:
            results: List of CapabilityResult objects
            
        Returns:
            List of formatted result dictionaries in Google format
        """
        import json
        
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

            formatted.append({
                "functionResponse": {
                    "name": result.name,
                    "response": response_data,
                }
            })

        return formatted

    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata and capabilities.

        Returns:
            Dictionary with provider information and capabilities
        """
        return {
            "provider": "google",
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_structured_output": False,
            "supports_multimodal": True
        }
