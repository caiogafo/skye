"""Token counting utilities for different model providers.

This module provides utilities for counting tokens in text and messages
using provider-specific tokenizers. It supports lazy loading of tokenizers
and provides fallback approximation for unknown models.

Example:
    >>> from skye.models.transport.token_counter import TokenCounter
    >>> from skye.base.messages import UserMessage
    >>>
    >>> # Count tokens in text
    >>> count = TokenCounter.count_tokens("Hello, world!", "gpt-4")
    >>> print(count)
    3
    >>>
    >>> # Count tokens in messages
    >>> messages = [UserMessage(content="Hello")]
    >>> count = TokenCounter.count_message_tokens(messages, "gpt-4")
    >>> print(count)
    6
"""

from typing import Any

from skye.base.messages import SkyeMessage
from skye.models.lazy_import import LazyImporter


class TokenCounter:
    """Calculate token counts for different models.

    This class provides methods to count tokens in text and messages using
    provider-specific tokenizers. Tokenizers are lazy-loaded only when needed.

    Attributes:
        _tokenizers: Cache of loaded tokenizers by model name.

    Example:
        >>> count = TokenCounter.count_tokens("Hello", "gpt-4")
        >>> isinstance(count, int)
        True
    """

    # Model-specific tokenizers (lazy loaded)
    _tokenizers: dict[str, Any] = {}

    @classmethod
    def count_tokens(cls, text: str, model: str) -> int:
        """Count tokens for a given text and model.

        Args:
            text: The text to count tokens for.
            model: The model identifier (e.g., 'gpt-4', 'claude-3-sonnet').

        Returns:
            The number of tokens in the text.

        Example:
            >>> count = TokenCounter.count_tokens("Hello, world!", "gpt-4")
            >>> count > 0
            True
        """
        tokenizer = cls._get_tokenizer(model)
        return len(tokenizer.encode(text))

    @classmethod
    def count_message_tokens(cls, messages: list[SkyeMessage], model: str) -> int:
        """Count tokens for a list of messages.

        This method accounts for both the message content and the per-message
        overhead that different models add for formatting.

        Args:
            messages: List of messages to count tokens for.
            model: The model identifier.

        Returns:
            The total number of tokens including message overhead.

        Example:
            >>> from skye.base.messages import UserMessage
            >>> messages = [UserMessage(content="Hello")]
            >>> count = TokenCounter.count_message_tokens(messages, "gpt-4")
            >>> count > 0
            True
        """
        total = 0
        for msg in messages:
            # Add message overhead (varies by model)
            total += cls._get_message_overhead(model)
            total += cls.count_tokens(msg.content, model)
        return total

    @classmethod
    def _get_tokenizer(cls, model: str) -> Any:
        """Get tokenizer for model (lazy loaded).

        Args:
            model: The model identifier.

        Returns:
            A tokenizer object with an encode() method.

        Example:
            >>> tokenizer = TokenCounter._get_tokenizer("gpt-4")
            >>> hasattr(tokenizer, 'encode')
            True
        """
        if model not in cls._tokenizers:
            if model.startswith("gpt-") or model.startswith("o1-") or model.startswith("o3-"):
                try:
                    tiktoken = LazyImporter.import_module("tiktoken", install_extra="tokens")
                    # Handle different model naming patterns
                    try:
                        cls._tokenizers[model] = tiktoken.encoding_for_model(model)
                    except KeyError:
                        # Fallback to cl100k_base for newer models
                        cls._tokenizers[model] = tiktoken.get_encoding("cl100k_base")
                except ImportError:
                    # If tiktoken not available, use approximate tokenizer
                    cls._tokenizers[model] = cls._approximate_tokenizer()
            elif model.startswith("claude-"):
                # No vendor SDK: Claude counts use the stdlib ~4 chars/token estimate.
                # (Exact counts are available server-side via POST /v1/messages/count_tokens.)
                cls._tokenizers[model] = cls._approximate_tokenizer()
            else:
                # Fallback to approximate counting for unknown models
                cls._tokenizers[model] = cls._approximate_tokenizer()
        return cls._tokenizers[model]

    @staticmethod
    def _get_message_overhead(model: str) -> int:
        """Get per-message token overhead.

        Different models add different amounts of overhead for message formatting.

        Args:
            model: The model identifier.

        Returns:
            The number of overhead tokens per message.

        Example:
            >>> overhead = TokenCounter._get_message_overhead("gpt-4")
            >>> overhead >= 0
            True
        """
        if model.startswith("gpt-4"):
            return 3
        elif model.startswith("gpt-3.5"):
            return 4
        elif model.startswith("o1-") or model.startswith("o3-"):
            return 3
        elif model.startswith("claude-"):
            return 4
        else:
            return 3  # Default overhead

    @staticmethod
    def _approximate_tokenizer() -> Any:
        """Approximate tokenizer for unknown models.

        Uses a simple heuristic: 1 token ≈ 4 characters.

        Returns:
            A tokenizer-like object with an encode() method.

        Example:
            >>> tokenizer = TokenCounter._approximate_tokenizer()
            >>> len(tokenizer.encode("hello"))
            1
        """

        class ApproximateTokenizer:
            """Simple approximate tokenizer based on character count."""

            @staticmethod
            def encode(text: str) -> list[int]:
                """Encode text to approximate token list.

                Args:
                    text: The text to encode.

                Returns:
                    A list of dummy token IDs (length represents token count).
                """
                # Rough approximation: 1 token ≈ 4 characters
                token_count = max(1, len(text) // 4)
                return [0] * token_count

        return ApproximateTokenizer()
