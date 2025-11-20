"""Tool transformer for converting capabilities to provider-specific formats.

This module provides the ToolTransformer class that converts Nimbus capabilities
to provider-specific tool/function calling formats for OpenAI, Anthropic, Bedrock,
Azure, and Vertex AI.
"""

from typing import Any

from nimbus.capabilities.interface import CapabilityInterface


class ToolTransformer:
    """Transforms capabilities to provider-specific tool formats.

    Converts Nimbus CapabilityInterface instances to the native tool/function
    calling formats used by different LLM providers. Each provider has slightly
    different schema requirements, and this class handles those differences
    transparently.

    Supported Providers:
    - OpenAI: Function calling format
    - Anthropic: Tool use format
    - Bedrock: Converse API format
    - Azure: OpenAI-compatible format
    - Vertex AI: Gemini format

    Example:
        >>> from nimbus.capabilities import LocalFunctionCapability
        >>> 
        >>> def get_weather(location: str) -> str:
        ...     '''Get weather for a location.'''
        ...     return f"Weather for {location}"
        >>> 
        >>> capability = LocalFunctionCapability(get_weather)
        >>> openai_tools = ToolTransformer.to_openai_format([capability])
        >>> anthropic_tools = ToolTransformer.to_anthropic_format([capability])
    """

    @staticmethod
    def to_openai_format(capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """Convert capabilities to OpenAI function calling format.

        OpenAI uses a nested structure with "type": "function" and a "function"
        object containing the tool definition. The function object uses standard
        JSON Schema for parameters.

        Format:
            {
                "type": "function",
                "function": {
                    "name": "tool_name",
                    "description": "Tool description",
                    "parameters": {
                        "type": "object",
                        "properties": {...},
                        "required": [...]
                    }
                }
            }

        Args:
            capabilities: List of CapabilityInterface instances to convert

        Returns:
            List of tool definitions in OpenAI format

        Example:
            >>> tools = ToolTransformer.to_openai_format([capability])
            >>> # Use with OpenAI API
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[...],
            ...     tools=tools
            ... )
        """
        tools = []
        for capability in capabilities:
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

    @staticmethod
    def to_anthropic_format(capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """Convert capabilities to Anthropic tool use format.

        Anthropic uses a flat structure with "name", "description", and
        "input_schema" fields. The input_schema is the JSON Schema for
        parameters.

        Format:
            {
                "name": "tool_name",
                "description": "Tool description",
                "input_schema": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }

        Args:
            capabilities: List of CapabilityInterface instances to convert

        Returns:
            List of tool definitions in Anthropic format

        Example:
            >>> tools = ToolTransformer.to_anthropic_format([capability])
            >>> # Use with Anthropic API
            >>> response = client.messages.create(
            ...     model="claude-3-opus-20240229",
            ...     max_tokens=1024,
            ...     tools=tools,
            ...     messages=[...]
            ... )
        """
        tools = []
        for capability in capabilities:
            schema = capability.get_schema()
            tool = {
                "name": schema.name,
                "description": schema.description,
                "input_schema": schema.parameters or {
                    "type": "object",
                    "properties": {},
                },
            }
            tools.append(tool)
        return tools

    @staticmethod
    def to_bedrock_format(capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """Convert capabilities to AWS Bedrock Converse API format.

        Bedrock uses a nested structure with "toolSpec" containing the tool
        definition. The inputSchema is the JSON Schema for parameters.

        Format:
            {
                "toolSpec": {
                    "name": "tool_name",
                    "description": "Tool description",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {...},
                            "required": [...]
                        }
                    }
                }
            }

        Args:
            capabilities: List of CapabilityInterface instances to convert

        Returns:
            List of tool definitions in Bedrock format

        Example:
            >>> tools = ToolTransformer.to_bedrock_format([capability])
            >>> # Use with Bedrock Converse API
            >>> response = client.converse(
            ...     modelId="anthropic.claude-3-opus-20240229-v1:0",
            ...     messages=[...],
            ...     tools=tools
            ... )
        """
        tools = []
        for capability in capabilities:
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

    @staticmethod
    def to_azure_format(capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """Convert capabilities to Azure OpenAI format.

        Azure OpenAI uses the same format as OpenAI (function calling format).
        This method is provided for clarity and consistency.

        Format:
            {
                "type": "function",
                "function": {
                    "name": "tool_name",
                    "description": "Tool description",
                    "parameters": {
                        "type": "object",
                        "properties": {...},
                        "required": [...]
                    }
                }
            }

        Args:
            capabilities: List of CapabilityInterface instances to convert

        Returns:
            List of tool definitions in Azure format

        Example:
            >>> tools = ToolTransformer.to_azure_format([capability])
            >>> # Use with Azure OpenAI API
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[...],
            ...     tools=tools
            ... )
        """
        # Azure uses the same format as OpenAI
        return ToolTransformer.to_openai_format(capabilities)

    @staticmethod
    def to_vertex_format(capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """Convert capabilities to Google Vertex AI Gemini format.

        Vertex AI uses a format with "name", "description", and "parameters"
        fields. The parameters field is the JSON Schema for parameters.

        Format:
            {
                "name": "tool_name",
                "description": "Tool description",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }

        Args:
            capabilities: List of CapabilityInterface instances to convert

        Returns:
            List of tool definitions in Vertex AI format

        Example:
            >>> tools = ToolTransformer.to_vertex_format([capability])
            >>> # Use with Vertex AI Gemini API
            >>> response = model.generate_content(
            ...     contents=[...],
            ...     tools=[tools]
            ... )
        """
        tools = []
        for capability in capabilities:
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
