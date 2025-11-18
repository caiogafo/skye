"""Message types for Nimbus conversations.

This module provides type-safe message representations for different roles and contexts
in AI conversations. All message types are based on Pydantic models for validation.

Example:
    >>> from nimbus.messages import UserMessage, AssistantMessage
    >>>
    >>> user_msg = UserMessage(content="Hello, how are you?")
    >>> assistant_msg = AssistantMessage(content="I'm doing well, thank you!")
    >>>
    >>> # Convert to dict for serialization
    >>> user_msg.to_dict()
    {'role': 'user', 'content': 'Hello, how are you?', ...}
"""

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class NimbusMessage(BaseModel):
    """Base class for all message types.

    Provides common functionality for messages including serialization,
    deserialization, and provider-specific formatting.

    Attributes:
        content: The text content of the message.
        role: The role of the message sender (user, assistant, system, capability).
        metadata: Additional metadata associated with the message.
        id: Unique identifier for the message.
        timestamp: When the message was created.

    Example:
        >>> msg = NimbusMessage(content="Hello", role="user")
        >>> msg.to_dict()
        {'role': 'user', 'content': 'Hello', ...}
    """

    content: str
    role: Literal["user", "assistant", "system", "capability"]
    metadata: dict[str, Any] = Field(default_factory=dict)
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def message_type(self) -> str:
        """Return the message type.

        Returns:
            The role of the message.
        """
        return self.role

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary format.

        Returns:
            Dictionary representation of the message.

        Example:
            >>> msg = UserMessage(content="Hello")
            >>> msg.to_dict()
            {'role': 'user', 'content': 'Hello', ...}
        """
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "id": self.id,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NimbusMessage":
        """Create message from dictionary format.

        Args:
            data: Dictionary containing message data with at least 'role' and 'content'.

        Returns:
            Appropriate message subclass based on the role.

        Example:
            >>> data = {'role': 'user', 'content': 'Hello'}
            >>> msg = NimbusMessage.from_dict(data)
            >>> isinstance(msg, UserMessage)
            True
        """
        role = data.get("role")
        if role == "user":
            return UserMessage(**data)
        elif role == "assistant":
            return AssistantMessage(**data)
        elif role == "system":
            return SystemMessage(**data)
        elif role == "capability":
            return CapabilityMessage(**data)
        else:
            return cls(**data)

    def format_for_provider(self, provider: str) -> dict[str, Any]:
        """Format message for specific provider (OpenAI, Anthropic, etc.).

        Args:
            provider: The provider name (e.g., 'openai', 'anthropic', 'bedrock').

        Returns:
            Dictionary formatted for the specific provider's API.

        Example:
            >>> msg = UserMessage(content="Hello")
            >>> msg.format_for_provider("openai")
            {'role': 'user', 'content': 'Hello'}
        """
        # Base implementation - can be overridden by subclasses
        return {"role": self.role, "content": self.content}


class UserMessage(NimbusMessage):
    """Message from a user.

    Represents input from a human user in the conversation.

    Example:
        >>> msg = UserMessage(content="What is the weather today?")
        >>> msg.role
        'user'
    """

    role: Literal["user"] = "user"


class AssistantMessage(NimbusMessage):
    """Message from an AI assistant.

    Represents output from the AI model, potentially including capability calls
    (tool/function calls).

    Attributes:
        capability_calls: List of capability/tool calls made by the assistant.

    Example:
        >>> msg = AssistantMessage(
        ...     content="Let me check the weather for you.",
        ...     capability_calls=[{"name": "get_weather", "args": {"city": "NYC"}}]
        ... )
        >>> len(msg.capability_calls)
        1
    """

    role: Literal["assistant"] = "assistant"
    capability_calls: list[dict[str, Any]] = Field(default_factory=list)

    def format_for_provider(self, provider: str) -> dict[str, Any]:
        """Format assistant message with capability calls for provider.

        Args:
            provider: The provider name (e.g., 'openai', 'anthropic', 'bedrock').

        Returns:
            Dictionary formatted for the specific provider's API, including
            capability calls in the provider's expected format.

        Example:
            >>> msg = AssistantMessage(
            ...     content="Checking weather",
            ...     capability_calls=[{"name": "get_weather"}]
            ... )
            >>> formatted = msg.format_for_provider("openai")
            >>> "tool_calls" in formatted
            True
        """
        base = super().format_for_provider(provider)
        if self.capability_calls:
            if provider == "openai":
                base["tool_calls"] = self.capability_calls
            elif provider == "anthropic":
                base["tool_use"] = self.capability_calls
        return base


class SystemMessage(NimbusMessage):
    """System-level instruction message.

    Represents system prompts or instructions that guide the AI's behavior.

    Example:
        >>> msg = SystemMessage(content="You are a helpful assistant.")
        >>> msg.role
        'system'
    """

    role: Literal["system"] = "system"


class CapabilityMessage(NimbusMessage):
    """Message containing capability execution results.

    Represents the result of a capability/tool execution that is being
    fed back to the model.

    Attributes:
        capability_id: Unique identifier for the capability call.
        capability_name: Name of the capability that was executed.

    Example:
        >>> msg = CapabilityMessage(
        ...     content='{"temperature": 72, "condition": "sunny"}',
        ...     capability_id="call_123",
        ...     capability_name="get_weather"
        ... )
        >>> msg.capability_name
        'get_weather'
    """

    role: Literal["capability"] = "capability"
    capability_id: str
    capability_name: str

    def format_for_provider(self, provider: str) -> dict[str, Any]:
        """Format capability message for provider.

        Args:
            provider: The provider name (e.g., 'openai', 'anthropic', 'bedrock').

        Returns:
            Dictionary formatted for the specific provider's API. OpenAI uses
            a 'tool' role, while others may use 'user' role with special formatting.

        Example:
            >>> msg = CapabilityMessage(
            ...     content="Result data",
            ...     capability_id="call_123",
            ...     capability_name="get_weather"
            ... )
            >>> formatted = msg.format_for_provider("openai")
            >>> formatted["role"]
            'tool'
        """
        base = {
            "role": "tool" if provider == "openai" else "user",
            "content": self.content
        }
        if provider == "openai":
            base["tool_call_id"] = self.capability_id
            base["name"] = self.capability_name
        return base


class ContentChunk(BaseModel):
    """Represents a chunk of content with metadata.

    Used for document processing, RAG systems, and other scenarios where
    content needs to be broken into manageable pieces with associated metadata.

    Attributes:
        text: The text content of the chunk.
        metadata: Additional metadata about the chunk (source, page number, etc.).
        chunk_id: Unique identifier for the chunk.
        source: Source identifier (file path, URL, etc.).

    Example:
        >>> chunk = ContentChunk(
        ...     text="This is a paragraph from a document.",
        ...     metadata={"page": 1, "section": "Introduction"},
        ...     source="document.pdf"
        ... )
        >>> str(chunk)
        'This is a paragraph from a document.'
    """

    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_id: str | None = None
    source: str | None = None

    def __str__(self) -> str:
        """Return the text content of the chunk.

        Returns:
            The text content.
        """
        return self.text
