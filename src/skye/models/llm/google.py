"""Google (Gemini Enterprise Agent Platform, formerly Vertex AI) provider implementation.

Renamed from `vertex` (Google renamed Vertex AI to Gemini Enterprise Agent Platform in April 2026); the extra is now `google`.

This module provides the Google Cloud implementation of the ModelInterface,
supporting Gemini and other Google models.

Features:
- Built-in stdlib REST adapter (no vendor SDK): ``generateContent`` / ``streamGenerateContent``
- Support for Gemini models
- Safety settings configuration
- Grounding features
- Streaming support
- Async support
- Multimodal inputs (images, video)

Example:
    >>> from skye.models.llm.google import GoogleProvider
    >>> from skye.base.completion import CompleteRequest
    >>> from skye.base.messages import UserMessage
    >>>
    >>> provider = GoogleProvider(
    ...     project_id="my-project",
    ...     location="us-central1"
    ... )
    >>> request = CompleteRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gemini-1.5-pro"
    ... )
    >>> response = provider.complete(request)
    >>> print(response.content)
"""

import asyncio
import json
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from skye.auth.google import resolve_google_auth
from skye.base.completion import CapabilityCall, CompleteRequest, CompleteResponse, StreamChunk, TokenUsage
from skye.base.interfaces.authentication import AuthenticationInterface
from skye.models.base import BaseModelProvider
from skye.models.transport.structured import schema_instruction
from skye.models.transport import rest
from skye.models.transport.rest import JsonObject, wrap


def _model_url(location: str, project_id: str, model: str, method: str) -> str:
    """Vertex AI publisher-model URL (the ``global`` location uses the bare host)."""
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    return (
        f"https://{host}/v1/projects/{project_id}/locations/{location}"
        f"/publishers/google/models/{model}:{method}"
    )


def _as_args(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            arguments = {}
    return arguments if isinstance(arguments, dict) else {}


class GoogleProvider(BaseModelProvider):
    """Google provider implementation.

    Implements the ModelInterface for Google Cloud's Google API, supporting
    Gemini models and other Google generative models.

    Args:
        project_id: Google Cloud project ID
        location: Google Cloud region (e.g., 'us-central1')
        credentials: Optional AuthenticationInterface or access token string. If not
                    provided, resolved from the environment (access token, API key,
                    metadata server).
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
        """No vendor SDK: requests go through the stdlib REST transport."""
        return None

    @property
    def authenticator(self) -> AuthenticationInterface:
        """The request authenticator (resolved lazily on first use)."""
        auth = getattr(self, "_authenticator", None)
        if auth is None:
            auth = resolve_google_auth(self.credentials)
            self._authenticator = auth
        return auth

    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Transform Skye messages to Google (Gemini) format.
        
        Google uses a parts-based format where content is broken into parts.
        System messages are kept here as ``role: system`` and moved to
        ``systemInstruction`` by :meth:`_transform_request`.
        
        Args:
            messages: List of Skye message objects
            
        Returns:
            List of dictionaries in Google format
        """
        from skye.base.messages import AssistantMessage, CapabilityMessage, SystemMessage
        
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
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
                images = getattr(msg, "images", None)
                if images:
                    from skye.models.transport.multimodal import ImageHandler

                    parts = [*(ImageHandler.to_google_format(image) for image in images), *parts]

                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    parts = [
                        {
                            "functionCall": {
                                "name": call["function"]["name"],
                                "args": _as_args(call["function"]["arguments"]),
                            }
                        }
                        for call in msg.capability_calls
                    ]

                result.append({"role": role, "parts": parts})
        return result
    
    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        """Transform Skye capabilities to Google Gemini format.
        
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
        """Extract ``functionCall`` parts from a ``generateContent`` response.

        Returns:
            List of CapabilityCall objects, or None if the response has none.
        """
        calls: list[CapabilityCall] = []
        candidates = wrap(response).get("candidates") or []
        if not candidates:
            return None
        parts = (candidates[0].get("content") or JsonObject({})).get("parts") or []
        for idx, part in enumerate(parts):
            fc = part.get("functionCall")
            if fc is not None:
                args = fc.get("args")
                calls.append(
                    CapabilityCall(
                        id=f"google_call_{idx}",  # Google does not provide call ids
                        name=fc.get("name", ""),
                        arguments=args.to_dict() if isinstance(args, JsonObject) else {},
                    )
                )
        return calls or None

    def _transform_request(self, request: CompleteRequest) -> dict[str, Any]:
        """Transform CompleteRequest to the Vertex AI REST body.

        The returned dict carries ``model`` (consumed by ``_call_provider``, not sent) plus
        ``contents``, ``systemInstruction``, ``generationConfig``, ``tools``, ``toolConfig``
        and ``safetySettings``.
        """
        if not request.messages:
            raise ValueError("messages must be provided for Google provider")

        transformed = self._transform_messages(request.messages)
        system_parts = [p for m in transformed if m["role"] == "system" for p in m["parts"]]
        contents = [m for m in transformed if m["role"] != "system"]

        generation_config: dict[str, Any] = {"temperature": request.temperature}
        google_request: dict[str, Any] = {
            "model": request.model,
            "contents": contents,
            "generationConfig": generation_config,
        }
        if request.response_schema:
            # JSON mode plus the schema in the instructions (no schema dialect to translate)
            generation_config["responseMimeType"] = "application/json"
            system_parts = [*system_parts, {"text": schema_instruction(request.response_schema)}]
        if system_parts:
            google_request["systemInstruction"] = {"parts": system_parts}

        if request.max_tokens:
            generation_config["maxOutputTokens"] = request.max_tokens
        if request.top_p:
            generation_config["topP"] = request.top_p
        if request.stop:
            generation_config["stopSequences"] = request.stop

        if request.metadata and "safety_settings" in request.metadata:
            google_request["safetySettings"] = request.metadata["safety_settings"]

        tools: list[dict[str, Any]] = []
        if request.capabilities:
            tools.append({"functionDeclarations": self._transform_capabilities(request.capabilities)})
            choice = request.capability_choice
            if choice == "required":
                google_request["toolConfig"] = {"functionCallingConfig": {"mode": "ANY"}}
            elif choice == "auto":
                google_request["toolConfig"] = {"functionCallingConfig": {"mode": "AUTO"}}
            elif choice and choice != "none":
                google_request["toolConfig"] = {
                    "functionCallingConfig": {"mode": "ANY", "allowedFunctionNames": [choice]}
                }
            elif choice == "none":
                google_request["toolConfig"] = {"functionCallingConfig": {"mode": "NONE"}}

        # Grounding: a REST tool entry (e.g. {"googleSearchRetrieval": {}})
        if request.metadata and isinstance(request.metadata.get("grounding"), dict):
            tools.append(request.metadata["grounding"])
        if tools:
            google_request["tools"] = tools

        # Provider-specific passthrough: google_<restField>
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith("google_"):
                    google_request[key[7:]] = value

        return google_request

    @staticmethod
    def _first_candidate(response: JsonObject) -> JsonObject | None:
        candidates = response.get("candidates") or []
        return candidates[0] if candidates else None

    @staticmethod
    def _finish_reason(candidate: JsonObject) -> str | None:
        raw = candidate.get("finishReason")
        if raw is None:
            return None
        reason = str(raw).lower()
        if reason in ("none", "finish_reason_unspecified"):
            return None
        return reason

    def _transform_response(self, response: Any) -> CompleteResponse:
        """Transform a ``generateContent`` JSON response to CompleteResponse."""
        response = wrap(response)
        content = ""
        finish_reason = "stop"
        metadata: dict[str, Any] = {}

        candidate = self._first_candidate(response)
        if candidate is not None:
            finish_reason = self._finish_reason(candidate) or "stop"
            parts = (candidate.get("content") or JsonObject({})).get("parts") or []
            texts = [p.get("text") for p in parts if p.get("text") is not None]
            content = "".join(texts)

        capability_calls = self._extract_capability_calls(response)
        if capability_calls:
            metadata = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"functionCall": {"name": c.name, "args": c.arguments}}
                                for c in capability_calls
                            ]
                        }
                    }
                ]
            }

        usage = response.get("usageMetadata") or JsonObject({})
        return CompleteResponse(
            id=response.get("responseId", "") or "",
            model=response.get("modelVersion", "") or "",
            provider="google",
            content=content,
            structured_output=None,
            role="assistant",
            finish_reason=finish_reason,
            usage=TokenUsage(
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
                total_tokens=usage.get("totalTokenCount", 0),
            ),
            capability_calls=capability_calls,
            created_at=datetime.now(tz=timezone.utc),
            metadata=metadata,
        )

    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform one SSE event of ``streamGenerateContent`` to StreamChunk."""
        chunk = wrap(chunk)
        content = ""
        finish_reason: str | None = None
        candidate = self._first_candidate(chunk)
        if candidate is not None:
            finish_reason = self._finish_reason(candidate)
            parts = (candidate.get("content") or JsonObject({})).get("parts") or []
            content = "".join(p.get("text") for p in parts if p.get("text") is not None)
        return StreamChunk(id="", delta=content, finish_reason=finish_reason, index=0)

    def _prepare_call(self, request: dict[str, Any], method: str) -> tuple[str, dict[str, Any]]:
        body = dict(request)
        model_name = body.pop("model")
        return _model_url(self.location, self.project_id, model_name, method), body

    def _call_provider(self, request: dict[str, Any]) -> JsonObject:
        """POST ``:generateContent`` and return the JSON response."""
        url, body = self._prepare_call(request, "generateContent")
        return rest.post_json(url, body, authenticator=self.authenticator, provider="google")

    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[JsonObject]:
        """POST ``:streamGenerateContent?alt=sse`` and yield decoded SSE events."""
        url, body = self._prepare_call(request, "streamGenerateContent")
        return rest.stream_sse_json(
            url + "?alt=sse", body, authenticator=self.authenticator, provider="google"
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
        """Asynchronous completion: runs the blocking REST call in the default executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.complete(messages, model, router, temperature, max_tokens, **kwargs))

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
