"""Message transformation utilities for provider-specific formats.

This module provides utilities to transform Nimbus messages into provider-specific
formats (OpenAI, Anthropic, Bedrock, Vertex AI) and vice versa.

Example:
    >>> from nimbus.messages import UserMessage, SystemMessage
    >>> from nimbus.providers.transformers import MessageTransformer
    >>>
    >>> messages = [
    ...     SystemMessage(content="You are helpful"),
    ...     UserMessage(content="Hello")
    ... ]
    >>> openai_msgs = MessageTransformer.to_openai_format(messages)
    >>> len(openai_msgs)
    2
"""

from typing import Any

from nimbus.messages import (
    AssistantMessage,
    CapabilityMessage,
    NimbusMessage,
    SystemMessage,
)


class MessageTransformer:
    """Transform nimbus messages to provider-specific formats."""

    @staticmethod
    def to_openai_format(messages: list[NimbusMessage]) -> list[dict[str, Any]]:
        """Convert to OpenAI message format.

        OpenAI uses a simple role-content format with tool calls as a separate field.
        System messages are included in the messages array.

        Args:
            messages: List of Nimbus messages to transform.

        Returns:
            List of dictionaries in OpenAI format.

        Example:
            >>> from nimbus.messages import UserMessage, AssistantMessage
            >>> messages = [
            ...     UserMessage(content="Hello"),
            ...     AssistantMessage(content="Hi there!")
            ... ]
            >>> result = MessageTransformer.to_openai_format(messages)
            >>> result[0]["role"]
            'user'
        """
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
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    openai_msg["tool_calls"] = msg.capability_calls
                result.append(openai_msg)
        return result

    @staticmethod
    def to_anthropic_format(
        messages: list[NimbusMessage],
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert to Anthropic format (separate system message).

        Anthropic requires the system message to be passed separately from
        the conversation messages. Tool results are formatted as user messages
        with special content blocks.

        Args:
            messages: List of Nimbus messages to transform.

        Returns:
            Tuple of (system_message, anthropic_messages) where system_message
            is a string or None, and anthropic_messages is a list of dicts.

        Example:
            >>> from nimbus.messages import SystemMessage, UserMessage
            >>> messages = [
            ...     SystemMessage(content="You are helpful"),
            ...     UserMessage(content="Hello")
            ... ]
            >>> system, msgs = MessageTransformer.to_anthropic_format(messages)
            >>> system
            'You are helpful'
            >>> len(msgs)
            1
        """
        system = None
        anthropic_messages = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system = msg.content
            elif isinstance(msg, CapabilityMessage):
                anthropic_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.capability_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )
            else:
                content: str | list[dict[str, Any]] = msg.content
                if isinstance(msg, AssistantMessage) and msg.capability_calls:
                    content = [
                        {
                            "type": "tool_use",
                            "id": call["id"],
                            "name": call["function"]["name"],
                            "input": call["function"]["arguments"],
                        }
                        for call in msg.capability_calls
                    ]
                anthropic_messages.append({"role": msg.role, "content": content})

        return system, anthropic_messages

    @staticmethod
    def to_bedrock_format(messages: list[NimbusMessage]) -> list[dict[str, Any]]:
        """Convert to Bedrock Converse API format.

        Bedrock uses a content array format where each message has a content
        array containing text or tool use/result blocks.

        Args:
            messages: List of Nimbus messages to transform.

        Returns:
            List of dictionaries in Bedrock Converse API format.

        Example:
            >>> from nimbus.messages import UserMessage
            >>> messages = [UserMessage(content="Hello")]
            >>> result = MessageTransformer.to_bedrock_format(messages)
            >>> result[0]["content"][0]["text"]
            'Hello'
        """
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

    @staticmethod
    def to_vertex_format(messages: list[NimbusMessage]) -> list[dict[str, Any]]:
        """Convert to Vertex AI (Gemini) format.

        Vertex AI uses a parts-based format where content is broken into parts.
        System instructions are typically handled separately in the API call.

        Args:
            messages: List of Nimbus messages to transform.

        Returns:
            List of dictionaries in Vertex AI format.

        Example:
            >>> from nimbus.messages import UserMessage
            >>> messages = [UserMessage(content="Hello")]
            >>> result = MessageTransformer.to_vertex_format(messages)
            >>> result[0]["parts"][0]["text"]
            'Hello'
        """
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                # System messages are typically passed separately in Vertex AI
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
                # Map assistant to model for Vertex AI
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
