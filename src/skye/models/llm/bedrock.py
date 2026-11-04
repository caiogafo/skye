"""AWS Bedrock provider implementation.

This module provides the AWS Bedrock implementation of the ModelInterface,
supporting Claude, Titan, Llama, and other models available through Bedrock.

Features:
- Built-in stdlib REST transport with SigV4 / Bedrock API key auth (no vendor SDK)
- Bedrock Converse API for unified multi-model access
- Tool/function calling support
- Streaming support
- Multimodal inputs (images)

Example:
    >>> from skye.models.llm.bedrock import BedrockProvider
    >>> from skye.base.completion import CompletionRequest
    >>> from skye.base.messages import UserMessage
    >>>
    >>> provider = BedrockProvider(region_name="us-east-1")
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
    ... )
    >>> response = provider.complete(request)
    >>> print(response.content)
"""

import base64
import json
import asyncio
import urllib.parse
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from skye.base.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from skye.models.base import BaseModelProvider
from skye.models.transport.structured import STRUCTURED_TOOL, schema_of
from skye.models.transport import rest
from skye.models.transport.eventstream import post_eventstream_json


class BedrockProvider(BaseModelProvider):
    """AWS Bedrock provider implementation.
    
    Implements the ModelInterface for AWS Bedrock's Converse API, supporting
    multiple model families including Claude, Titan, Llama, and others.
    
    Uses the built-in stdlib REST adapter; no AWS SDK is imported.
    
    Args:
        region_name: AWS region name (default: "us-east-1")
        profile_name: Optional AWS profile name
        **kwargs: Additional configuration parameters
    
    Example:
        >>> provider = BedrockProvider(region_name="us-west-2")
        >>> response = provider.complete(request)
    """

    
    def __init__(
        self,
        region_name: str = "us-east-1",
        profile_name: str | None = None,
        **kwargs: Any
    ) -> None:
        """Initialize Bedrock provider.
        
        Args:
            region_name: AWS region name (default: "us-east-1")
            profile_name: Optional AWS profile name
            **kwargs: Additional configuration parameters
        """
        super().__init__(
            region_name=region_name,
            profile_name=profile_name,
            **kwargs
        )
        self.region_name = region_name
        self.profile_name = profile_name
    
    def _initialize_client(self) -> Any:
        """No vendor client: requests go through the stdlib REST transport."""
        return None

    def _authenticator(self) -> Any:
        if getattr(self, "_auth", None) is None:
            from skye.auth.aws import bedrock_authenticator

            self._auth = bedrock_authenticator(
                self.region_name,
                api_key=self.config.get("api_key"),
                profile_name=self.profile_name,
                access_key=self.config.get("aws_access_key_id"),
                secret_key=self.config.get("aws_secret_access_key"),
                session_token=self.config.get("aws_session_token"),
            )
        return self._auth

    def _url(self, request: dict[str, Any], operation: str) -> tuple[str, dict[str, Any]]:
        body = {k: v for k, v in request.items() if k != "modelId"}
        model = urllib.parse.quote(str(request["modelId"]), safe="")
        host = self.config.get("endpoint_url") or f"https://bedrock-runtime.{self.region_name}.amazonaws.com"
        return f"{host}/model/{model}/{operation}", body

    async def acomplete(self, *args: Any, **kwargs: Any) -> CompletionResponse:  # type: ignore[override]
        """Run :meth:`complete` in an executor so the event loop is not blocked."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.complete(*args, **kwargs))

    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Transform Skye messages to Bedrock Converse API format.
        
        Bedrock uses a content array format where each message has a content
        array containing text or tool use/result blocks.
        
        Args:
            messages: List of Skye message objects
            
        Returns:
            List of dictionaries in Bedrock Converse API format
        """
        from skye.base.messages import AssistantMessage, CapabilityMessage, SystemMessage
        
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": [{"text": msg.content}]})
            elif isinstance(msg, CapabilityMessage):
                result.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "toolResult": {
                                    "toolUseId": msg.capability_id,
                                    "content": [{"text": msg.content}],
                                }
                            }
                        ],
                    }
                )
            else:
                content: list[dict[str, Any]] = [{"text": msg.content}]
                images = getattr(msg, "images", None)
                if images:
                    from skye.models.transport.multimodal import ImageHandler

                    blocks = []
                    for image in images:
                        block = ImageHandler.to_bedrock_format(image)
                        source = block["image"]["source"]
                        # The REST body is JSON: bytes travel as base64 text.
                        source["bytes"] = base64.b64encode(source["bytes"]).decode("ascii")
                        blocks.append(block)
                    content = [*blocks, {"text": msg.content}]
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    content = [
                        {
                            "toolUse": {
                                "toolUseId": call["id"],
                                "name": call["function"]["name"],
                                "input": call["function"]["arguments"],
                            }
                        }
                        for call in msg.capability_calls
                    ]
                result.append({"role": msg.role, "content": content})
        return result
    
    def _transform_capabilities(self, capabilities: list[Any]) -> list[dict[str, Any]]:
        """Transform Skye capabilities to Bedrock Converse API format.
        
        Bedrock uses a nested structure with "toolSpec" containing the tool
        definition. The inputSchema is the JSON Schema for parameters.
        
        Args:
            capabilities: List of CapabilityInterface objects or dicts
            
        Returns:
            List of tool definitions in Bedrock format
        """
        tools = []
        for capability in capabilities:
            # Handle both CapabilityInterface objects and dict format
            if isinstance(capability, dict):
                # Check if already in Bedrock format
                if "toolSpec" in capability:
                    tools.append(capability)
                else:
                    # Convert from OpenAI format to Bedrock format
                    func = capability.get("function", {})
                    tool = {
                        "toolSpec": {
                            "name": func.get("name", ""),
                            "description": func.get("description", ""),
                            "inputSchema": {
                                "json": func.get("parameters", {
                                    "type": "object",
                                    "properties": {},
                                })
                            },
                        }
                    }
                    tools.append(tool)
            else:
                # CapabilityInterface object, convert to Bedrock format
                schema = capability.get_schema()
                tool = {
                    "toolSpec": {
                        "name": schema.name,
                        "description": schema.description,
                        "inputSchema": {
                            "json": schema.parameters or {
                                "type": "object",
                                "properties": {},
                            }
                        },
                    }
                }
                tools.append(tool)
        return tools
    
    def _extract_capability_calls(self, response: Any) -> list[Any] | None:
        """Extract capability calls from Bedrock response.
        
        Parses tool use blocks from the Bedrock response format and converts them
        to Skye CapabilityCall objects.
        
        Args:
            response: Bedrock response dictionary
            
        Returns:
            List of CapabilityCall objects, or None if no capability calls
        """
        if isinstance(response, rest.JsonObject):
            response = response.to_dict()
        output = response.get("output", {})
        message = output.get("message", {})
        
        capability_calls = []
        for content_block in message.get("content", []):
            if "toolUse" in content_block and content_block["toolUse"]["name"] != STRUCTURED_TOOL:
                tool_use = content_block["toolUse"]
                
                from skye.base.completion import CapabilityCall
                
                capability_calls.append(
                    CapabilityCall(
                        id=tool_use["toolUseId"],
                        name=tool_use["name"],
                        arguments=tool_use["input"]
                    )
                )
        
        return capability_calls if capability_calls else None
    
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to Bedrock Converse API format.
        
        Args:
            request: The skye CompletionRequest
            
        Returns:
            Dictionary in Bedrock Converse API format
        """
        # Ensure messages are available
        if not request.messages:
            raise ValueError("messages must be provided for Bedrock provider")
        
        bedrock_request: dict[str, Any] = {
            "modelId": request.model,
            "messages": self._transform_messages(request.messages),
            "inferenceConfig": {
                "temperature": request.temperature
            }
        }
        
        if request.max_tokens:
            bedrock_request["inferenceConfig"]["maxTokens"] = request.max_tokens
        
        if request.top_p:
            bedrock_request["inferenceConfig"]["topP"] = request.top_p
        
        if request.stop:
            bedrock_request["inferenceConfig"]["stopSequences"] = request.stop
        
        # Handle function/tool calling
        if request.capabilities:
            # Check if capabilities are CapabilityInterface objects or dicts
            if request.capabilities and isinstance(request.capabilities[0], dict):
                # Legacy support: capabilities are already in dict format
                bedrock_request["toolConfig"] = {
                    "tools": [{"toolSpec": cap} for cap in request.capabilities]
                }
            else:
                # Use internal method to convert capabilities to Bedrock format
                bedrock_request["toolConfig"] = {
                    "tools": self._transform_capabilities(request.capabilities)
                }
                
                # Handle capability_choice parameter
                if request.capability_choice:
                    if request.capability_choice == "auto":
                        bedrock_request["toolConfig"]["toolChoice"] = {"auto": {}}
                    elif request.capability_choice == "required":
                        bedrock_request["toolConfig"]["toolChoice"] = {"any": {}}
                    elif isinstance(request.capability_choice, str):
                        # Specific capability name
                        bedrock_request["toolConfig"]["toolChoice"] = {
                            "tool": {"name": request.capability_choice}
                        }
                    elif isinstance(request.capability_choice, dict):
                        # Already formatted capability choice
                        bedrock_request["toolConfig"]["toolChoice"] = request.capability_choice
        
        # Structured output: no native mode, so the answer is forced through one tool (function calling)
        if request.response_schema and not request.capabilities:
            bedrock_request["toolConfig"] = {
                "tools": [
                    {
                        "toolSpec": {
                            "name": STRUCTURED_TOOL,
                            "description": f"Return the answer as a {request.response_schema.__name__}.",
                            "inputSchema": {"json": schema_of(request.response_schema)},
                        }
                    }
                ],
                "toolChoice": {"tool": {"name": STRUCTURED_TOOL}},
            }

        # Provider-specific metadata
        if request.metadata:
            for key, value in request.metadata.items():
                if key.startswith("bedrock_"):
                    # Handle bedrock-specific parameters
                    param_name = key[8:]  # Remove "bedrock_" prefix
                    if param_name == "system":
                        bedrock_request["system"] = value
                    elif param_name == "additionalModelRequestFields":
                        bedrock_request["additionalModelRequestFields"] = value
        
        return bedrock_request
    
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform Bedrock response to CompletionResponse.
        
        Args:
            response: The Bedrock response object
            
        Returns:
            CompletionResponse in skye format
        """
        if isinstance(response, rest.JsonObject):
            response = response.to_dict()
        output = response["output"]
        message = output["message"]
        
        # Extract content from message
        content = ""
        tool_calls_metadata = []
        
        for content_block in message.get("content", []):
            if "text" in content_block:
                content += content_block["text"]
            elif "toolUse" in content_block and content_block["toolUse"]["name"] == STRUCTURED_TOOL:
                # The structured answer: its input is the JSON the declared schema describes
                content += json.dumps(content_block["toolUse"]["input"])
            elif "toolUse" in content_block:
                # Store in metadata for compatibility
                tool_use = content_block["toolUse"]
                tool_calls_metadata.append({
                    "id": tool_use["toolUseId"],
                    "type": "function",
                    "function": {
                        "name": tool_use["name"],
                        "arguments": tool_use["input"]
                    }
                })
        
        # Extract capability calls using internal method
        tool_calls_list = self._extract_capability_calls(response)
        
        # Extract usage information
        usage_info = response.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=usage_info.get("inputTokens", 0),
            completion_tokens=usage_info.get("outputTokens", 0),
            total_tokens=usage_info.get("totalTokens", 0)
        )
        
        # Extract stop reason
        stop_reason = response.get("stopReason", "stop")
        finish_reason_map = {
            "end_turn": "stop",
            "tool_use": "tool_calls",
            "max_tokens": "length",
            "stop_sequence": "stop",
            "content_filtered": "content_filter"
        }
        finish_reason = finish_reason_map.get(stop_reason, stop_reason)
        
        return CompletionResponse(
            id=response.get("ResponseMetadata", {}).get("RequestId", ""),
            model=response.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amzn-bedrock-model-id", ""),
            provider="bedrock",
            content=content,
            structured_output=None,  # Bedrock doesn't have native structured output
            role="assistant",
            finish_reason=finish_reason,
            usage=usage,
            capability_calls=tool_calls_list if tool_calls_list else None,
            created_at=datetime.now(tz=timezone.utc),
            metadata={
                "stop_reason": stop_reason,
                "tool_calls": tool_calls_metadata if tool_calls_metadata else None,
                "metrics": response.get("metrics", {})
            }
        )
    
    def _transform_stream_chunk(self, chunk: Any) -> StreamChunk:
        """Transform Bedrock stream chunk to StreamChunk.
        
        Args:
            chunk: The Bedrock stream chunk
            
        Returns:
            StreamChunk in skye format
        """
        if isinstance(chunk, rest.JsonObject):
            chunk = chunk.to_dict()
        # Bedrock streaming returns different event types
        delta = ""
        finish_reason = None
        
        if "contentBlockDelta" in chunk:
            delta_content = chunk["contentBlockDelta"].get("delta", {})
            if "text" in delta_content:
                delta = delta_content["text"]
        
        if "messageStop" in chunk:
            stop_reason = chunk["messageStop"].get("stopReason", "stop")
            finish_reason_map = {
                "end_turn": "stop",
                "tool_use": "tool_calls",
                "max_tokens": "length",
                "stop_sequence": "stop",
                "content_filtered": "content_filter"
            }
            finish_reason = finish_reason_map.get(stop_reason, stop_reason)
        
        return StreamChunk(
            id="",  # Bedrock streaming doesn't provide chunk IDs
            delta=delta,
            finish_reason=finish_reason,
            index=0
        )
    
    def _call_provider(self, request: dict[str, Any]) -> Any:
        """POST the Converse API; returns a JsonObject."""
        url, body = self._url(request, "converse")
        return rest.post_json(
            url, body, authenticator=self._authenticator(), provider="bedrock",
            timeout=float(self.config.get("timeout", 60.0)),
        )

    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """POST ConverseStream and yield decoded eventstream events."""
        url, body = self._url(request, "converse-stream")
        yield from post_eventstream_json(
            url, body, authenticator=self._authenticator(), provider="bedrock",
            timeout=float(self.config.get("timeout", 60.0)),
        )

    def format_capability_results(self, results: list[Any]) -> list[dict[str, Any]]:
        """Format capability results for Bedrock.
        
        Bedrock expects tool results in this format:
        {
            "toolResult": {
                "toolUseId": "tooluse_123",
                "content": [
                    {
                        "json": {"result": "value"}
                    }
                ]
            }
        }
        
        Args:
            results: List of CapabilityResult objects
            
        Returns:
            List of formatted result dictionaries in Bedrock format
        """
        import json
        
        formatted = []
        for result in results:
            # Convert result to appropriate format
            if result.error:
                result_data = {"error": result.error}
            elif isinstance(result.result, dict):
                result_data = result.result
            elif isinstance(result.result, str):
                try:
                    result_data = json.loads(result.result)
                except json.JSONDecodeError:
                    result_data = {"result": result.result}
            else:
                result_data = {"result": result.result}

            formatted.append({
                "toolResult": {
                    "toolUseId": result.capability_call_id,
                    "content": [{"json": result_data}],
                }
            })

        return formatted
    
    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata and capabilities.
        
        Returns:
            Dictionary with provider information and capabilities
        """
        return {
            "provider": "bedrock",
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_structured_output": False,  # Via function calling only
            "supports_multimodal": True
        }
