"""Message types for Skye conversations.

This module provides type-safe message representations for different roles and contexts
in AI conversations. All message types are dataclasses whose fields are validated when the
message is built (see ``skye.base.validated``).

Example:
    >>> from skye.base.messages import UserMessage, AssistantMessage
    >>>
    >>> user_msg = UserMessage(content="Hello, how are you?")
    >>> assistant_msg = AssistantMessage(content="I'm doing well, thank you!")
    >>>
    >>> # Convert to dict for serialization
    >>> user_msg.to_dict()
    {'role': 'user', 'content': 'Hello, how are you?', ...}
"""

import base64
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from skye.base.validated import Validated, field, from_mapping, validated


def sniff_image_mime(data: bytes) -> str:
    """MIME type of raw image bytes from their first bytes (JPEG when unknown)."""
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _image_text(image: Any) -> str:
    """JSON-safe text for one image input."""
    if isinstance(image, bytes):
        return f"data:{sniff_image_mime(image)};base64," + base64.b64encode(image).decode("ascii")
    return str(image)


@validated
class SkyeMessage(Validated):
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
        >>> msg = SkyeMessage(content="Hello", role="user")
        >>> msg.to_dict()
        {'role': 'user', 'content': 'Hello', ...}
    """

    content: str
    role: Literal["user", "assistant", "system", "capability"]
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def message_type(self) -> str:
        """Return the message type.

        Returns:
            The role of the message.
        """
        return self.role

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SkyeMessage":
        """Create message from dictionary format.

        Args:
            data: Dictionary containing message data with at least 'role' and 'content'.

        Returns:
            Appropriate message subclass based on the role.

        Example:
            >>> data = {'role': 'user', 'content': 'Hello'}
            >>> msg = SkyeMessage.from_dict(data)
            >>> isinstance(msg, UserMessage)
            True
        """
        kinds: dict[Any, type[SkyeMessage]] = {
            "user": UserMessage,
            "assistant": AssistantMessage,
            "system": SystemMessage,
            "capability": CapabilityMessage,
        }
        message: SkyeMessage = from_mapping(kinds.get(data.get("role"), cls), data)
        return message

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary format.

        This is a provider-agnostic representation. Providers handle their own
        transformation logic via their _transform_messages() method.

        Returns:
            Dictionary representation of the message.

        Example:
            >>> msg = UserMessage(content="Hello")
            >>> msg.to_dict()
            {'role': 'user', 'content': 'Hello'}
        """
        return {"role": self.role, "content": self.content}


@validated
class UserMessage(SkyeMessage):
    """Message from a user.

    Represents input from a human user in the conversation.

    Attributes:
        images: Images sent with the text: each is an http(s) URL, a ``data:image`` URI, a file path
            (``str`` or ``Path``) or raw bytes. Each adapter converts them to its provider's shape.

    Example:
        >>> msg = UserMessage(content="What is the weather today?")
        >>> msg.role
        'user'
    """

    role: Literal["user"] = "user"
    images: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary; images (URL, data URI, path or bytes) become strings.

        Bytes turn into a ``data:`` URI and a path into its text, so the result is JSON-safe.
        """
        result = super().to_dict()
        if self.images:
            result["images"] = [_image_text(image) for image in self.images]
        return result


@validated
class AssistantMessage(SkyeMessage):
    """Message from an AI assistant.

    Represents output from the AI model, potentially including capability calls.

    Attributes:
        capability_calls: List of capability calls made by the assistant.

    Example:
        >>> msg = AssistantMessage(
        ...     content="Let me check the weather for you.",
        ...     capability_calls=[{"name": "get_weather", "args": {"city": "NYC"}}]
        ... )
        >>> len(msg.capability_calls)
        1
    """

    role: Literal["assistant"] = "assistant"
    capability_calls: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert assistant message to dictionary format.

        This is a provider-agnostic representation. Providers handle their own
        transformation logic via their _transform_messages() method, including
        how to format capability calls.

        Returns:
            Dictionary representation of the message.

        Example:
            >>> msg = AssistantMessage(
            ...     content="Checking weather",
            ...     capability_calls=[{"name": "get_weather"}]
            ... )
            >>> formatted = msg.to_dict()
            >>> formatted["role"]
            'assistant'
        """
        result = super().to_dict()
        if self.capability_calls:
            result["capability_calls"] = self.capability_calls
        return result


@validated
class SystemMessage(SkyeMessage):
    """System-level instruction message.

    Represents system prompts or instructions that guide the AI's behavior.

    Example:
        >>> msg = SystemMessage(content="You are a helpful assistant.")
        >>> msg.role
        'system'
    """

    role: Literal["system"] = "system"


@validated
class CapabilityMessage(SkyeMessage):
    """Message containing capability execution results.

    Represents the result of a capability execution that is being
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

    def to_dict(self) -> dict[str, Any]:
        """Convert capability message to dictionary format.

        This is a provider-agnostic representation. Providers handle their own
        transformation logic via their _transform_messages() method, including
        how to format capability messages.

        Returns:
            Dictionary representation of the message.

        Example:
            >>> msg = CapabilityMessage(
            ...     content="Result data",
            ...     capability_id="call_123",
            ...     capability_name="get_weather"
            ... )
            >>> formatted = msg.to_dict()
            >>> formatted["role"]
            'capability'
        """
        return {
            "role": self.role,
            "content": self.content,
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
        }


@validated
class ContentChunk(Validated):
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
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_id: str | None = None
    source: str | None = None

    def __str__(self) -> str:
        """Return the text content of the chunk.

        Returns:
            The text content.
        """
        return self.text
