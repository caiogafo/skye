"""Token counter interface for counting tokens in text and messages.

This module defines the abstract interface for counting tokens using
provider-specific tokenizers.
"""

from abc import ABC, abstractmethod

from nimbus.base.messages import NimbusMessage


class TokenCounterInterface(ABC):
    """Abstract interface for token counting.

    This interface defines the contract for counting tokens in text and
    messages using provider-specific tokenizers.

    Example:
        >>> class MyTokenCounter(TokenCounterInterface):
        ...     def count_tokens(self, text, model):
        ...         return len(text.split())
        ...
        ...     def count_message_tokens(self, messages, model):
        ...         return sum(self.count_tokens(m.content, model) for m in messages)
    """

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens for a given text and model.

        Args:
            text: The text to count tokens for.
            model: The model identifier (e.g., 'gpt-4', 'claude-3-sonnet').

        Returns:
            The number of tokens in the text.

        Example:
            >>> count = counter.count_tokens("Hello, world!", "gpt-4")
            >>> count > 0
            True
        """
        pass

    @abstractmethod
    def count_message_tokens(self, messages: list[NimbusMessage], model: str) -> int:
        """Count tokens for a list of messages.

        This method should account for both the message content and the
        per-message overhead that different models add for formatting.

        Args:
            messages: List of messages to count tokens for.
            model: The model identifier.

        Returns:
            The total number of tokens including message overhead.

        Example:
            >>> from nimbus.base.messages import UserMessage
            >>> messages = [UserMessage(content="Hello")]
            >>> count = counter.count_message_tokens(messages, "gpt-4")
            >>> count > 0
            True
        """
        pass
