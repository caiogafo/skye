"""Message transformer interface for converting between message formats.

This module defines the abstract interface for transforming Nimbus messages
to provider-specific formats and vice versa.
"""

from abc import ABC, abstractmethod
from typing import Any

from nimbus.messages import NimbusMessage


class MessageTransformerInterface(ABC):
    """Abstract interface for message transformation.

    This interface defines the contract for transforming messages between
    Nimbus format and provider-specific formats.

    Example:
        >>> class MyTransformer(MessageTransformerInterface):
        ...     def to_provider_format(self, messages):
        ...         return [{"role": m.role, "content": m.content} for m in messages]
        ...
        ...     def from_provider_format(self, provider_messages):
        ...         return [UserMessage(content=m["content"]) for m in provider_messages]
    """

    @abstractmethod
    def to_provider_format(self, messages: list[NimbusMessage]) -> list[dict[str, Any]]:
        """Transform Nimbus messages to provider-specific format.

        Args:
            messages: List of Nimbus messages to transform.

        Returns:
            List of messages in provider-specific format.

        Example:
            >>> from nimbus.messages import UserMessage
            >>> messages = [UserMessage(content="Hello")]
            >>> provider_msgs = transformer.to_provider_format(messages)
        """
        pass

    @abstractmethod
    def from_provider_format(self, provider_messages: list[dict[str, Any]]) -> list[NimbusMessage]:
        """Transform provider-specific messages to Nimbus format.

        Args:
            provider_messages: List of messages in provider-specific format.

        Returns:
            List of Nimbus messages.

        Example:
            >>> provider_msgs = [{"role": "user", "content": "Hello"}]
            >>> messages = transformer.from_provider_format(provider_msgs)
        """
        pass

    @abstractmethod
    def supports_multimodal(self) -> bool:
        """Check if this transformer supports multimodal content.

        Returns:
            True if multimodal content is supported, False otherwise.

        Example:
            >>> if transformer.supports_multimodal():
            ...     # Handle images
            ...     pass
        """
        pass
