"""AWS Bedrock provider implementation.

This module provides the AWS Bedrock implementation of the ModelInterface,
supporting Claude, Titan, Llama, and other models available through Bedrock.

Features:
- Lazy loading of boto3 (optional in Lambda environments)
- Bedrock Converse API for unified multi-model access
- Tool/function calling support
- Streaming support
- Multimodal inputs (images)

Example:
    >>> from nimbus.models.llm.bedrock import BedrockProvider
    >>> from nimbus.base.completion import CompletionRequest
    >>> from nimbus.base.messages import UserMessage
    >>>
    >>> provider = BedrockProvider(region_name="us-east-1")
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
    ... )
    >>> response = provider.complete(request)
    >>> print(response.content)
"""

import sys
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from nimbus.base.completion import CompletionRequest, CompletionResponse, StreamChunk, TokenUsage
from nimbus.models.base import BaseModelProvider
from nimbus.models.lazy_import import LazyImporter


class BedrockProvider(BaseModelProvider):
    """AWS Bedrock provider implementation.
    
    Implements the ModelInterface for AWS Bedrock's Converse API, supporting
    multiple model families including Claude, Titan, Llama, and others.
    
    The boto3 dependency is optional - if boto3 is already available in the
    environment (e.g., pre-installed in AWS Lambda), it will be used without
    requiring installation.
    
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
        """Initialize Bedrock client with optional boto3.
        
        This method checks if boto3 is already available in the environment
        (e.g., pre-installed in AWS Lambda) before attempting to import it.
        
        Returns:
            Initialized Bedrock runtime client
        """
        # Check if boto3 is already loaded in the environment
        if "boto3" in sys.modules:
            boto3 = sys.modules["boto3"]
        else:
            # Try to import boto3, providing helpful error if not available
            boto3 = LazyImporter.import_module(
                "boto3",
                package_name="boto3",
                install_extra="bedrock"
            )
        
        session = boto3.Session(
            region_name=self.region_name,
            profile_name=self.profile_name
        )
        return session.client("bedrock-runtime")
    
    def _transform_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Transform Nimbus messages to Bedrock Converse API format.
        
        Bedrock uses a content array format where each message has a content
        array containing text or tool use/result blocks.
        
        Args:
            messages: List of Nimbus message objects
            
        Returns:
            List of dictionaries in Bedrock Converse API format
        """
        from nimbus.base.messages import AssistantMessage, CapabilityMessage, SystemMessage
        
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
        """Transform Nimbus capabilities to Bedrock Converse API format.
        
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
        to Nimbus CapabilityCall objects.
        
        Args:
            response: Bedrock response dictionary
            
        Returns:
            List of CapabilityCall objects, or None if no capability calls
        """
        output = response.get("output", {})
        message = output.get("message", {})
        
        capability_calls = []
        for content_block in message.get("content", []):
            if "toolUse" in content_block:
                tool_use = content_block["toolUse"]
                
                from nimbus.base.completion import CapabilityCall
                
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
            request: The nimbus CompletionRequest
            
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
            CompletionResponse in nimbus format
        """
        output = response["output"]
        message = output["message"]
        
        # Extract content from message
        content = ""
        tool_calls_metadata = []
        
        for content_block in message.get("content", []):
            if "text" in content_block:
                content += content_block["text"]
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
            StreamChunk in nimbus format
        """
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
        """Call Bedrock Converse API.
        
        Args:
            request: Provider-specific request dictionary
            
        Returns:
            Bedrock response object
        """
        return self.client.converse(**request)
    
    def _call_provider_stream(self, request: dict[str, Any]) -> Iterator[Any]:
        """Call Bedrock streaming API.
        
        Args:
            request: Provider-specific request dictionary
            
        Yields:
            Bedrock stream events
        """
        response = self.client.converse_stream(**request)
        # The stream is in response["stream"]
        for event in response.get("stream", []):
            yield event
    
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
