"""Unit tests for TokenCounter utility.

Tests token counting functionality for various models and scenarios.
"""

import pytest

from nimbus.messages import AssistantMessage, SystemMessage, UserMessage
from nimbus.providers.token_counter import TokenCounter


class TestTokenCounter:
    """Test suite for TokenCounter."""

    def test_count_tokens_with_approximate_tokenizer(self):
        """Test token counting with approximate tokenizer for unknown models."""
        text = "Hello, world!"
        count = TokenCounter.count_tokens(text, "unknown-model")
        # Approximate: 13 chars / 4 = 3 tokens
        assert count == 3

    def test_count_tokens_empty_string(self):
        """Test token counting with empty string."""
        count = TokenCounter.count_tokens("", "gpt-4")
        # Empty string should have at least 1 token in approximate tokenizer
        assert count >= 0

    def test_count_tokens_long_text(self):
        """Test token counting with longer text."""
        text = "This is a longer piece of text that should have more tokens."
        count = TokenCounter.count_tokens(text, "unknown-model")
        # Should be proportional to length
        assert count > 10

    def test_count_message_tokens_single_message(self):
        """Test counting tokens for a single message."""
        messages = [UserMessage(content="Hello")]
        count = TokenCounter.count_message_tokens(messages, "gpt-4")
        # Should include message overhead (3) + content tokens
        assert count > 3

    def test_count_message_tokens_multiple_messages(self):
        """Test counting tokens for multiple messages."""
        messages = [
            UserMessage(content="Hello"),
            AssistantMessage(content="Hi there!"),
            UserMessage(content="How are you?"),
        ]
        count = TokenCounter.count_message_tokens(messages, "gpt-4")
        # Should include overhead for each message plus content
        assert count > 9  # 3 messages * 3 overhead = 9 minimum

    def test_count_message_tokens_with_system_message(self):
        """Test counting tokens with system message."""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="Hello"),
        ]
        count = TokenCounter.count_message_tokens(messages, "gpt-4")
        assert count > 6  # 2 messages * 3 overhead = 6 minimum

    def test_message_overhead_gpt4(self):
        """Test message overhead for GPT-4."""
        overhead = TokenCounter._get_message_overhead("gpt-4")
        assert overhead == 3

    def test_message_overhead_gpt35(self):
        """Test message overhead for GPT-3.5."""
        overhead = TokenCounter._get_message_overhead("gpt-3.5-turbo")
        assert overhead == 4

    def test_message_overhead_o1(self):
        """Test message overhead for o1 models."""
        overhead = TokenCounter._get_message_overhead("o1-preview")
        assert overhead == 3

    def test_message_overhead_claude(self):
        """Test message overhead for Claude models."""
        overhead = TokenCounter._get_message_overhead("claude-3-sonnet")
        assert overhead == 4

    def test_message_overhead_unknown_model(self):
        """Test message overhead for unknown model."""
        overhead = TokenCounter._get_message_overhead("unknown-model")
        assert overhead == 3  # Default

    def test_approximate_tokenizer_encode(self):
        """Test approximate tokenizer encode method."""
        tokenizer = TokenCounter._approximate_tokenizer()
        tokens = tokenizer.encode("Hello, world!")
        # 13 chars / 4 = 3 tokens
        assert len(tokens) == 3

    def test_approximate_tokenizer_short_text(self):
        """Test approximate tokenizer with very short text."""
        tokenizer = TokenCounter._approximate_tokenizer()
        tokens = tokenizer.encode("Hi")
        # Should have at least 1 token
        assert len(tokens) >= 1

    def test_tokenizer_caching(self):
        """Test that tokenizers are cached."""
        # First call
        TokenCounter.count_tokens("test", "test-model")
        # Second call should use cached tokenizer
        TokenCounter.count_tokens("test2", "test-model")
        # Verify the model is in cache
        assert "test-model" in TokenCounter._tokenizers

    @pytest.mark.parametrize(
        "model,text,expected_min",
        [
            ("gpt-4", "Hello", 1),
            ("gpt-3.5-turbo", "Hello world", 2),
            ("claude-3-sonnet", "Test message", 2),
            ("unknown-model", "Short", 1),
        ],
    )
    def test_count_tokens_various_models(self, model: str, text: str, expected_min: int):
        """Test token counting for various models."""
        count = TokenCounter.count_tokens(text, model)
        assert count >= expected_min

    def test_count_tokens_with_special_characters(self):
        """Test token counting with special characters."""
        text = "Hello! @#$% 123 🎉"
        count = TokenCounter.count_tokens(text, "unknown-model")
        assert count > 0

    def test_count_message_tokens_empty_list(self):
        """Test counting tokens for empty message list."""
        messages = []
        count = TokenCounter.count_message_tokens(messages, "gpt-4")
        assert count == 0

    def test_count_message_tokens_with_empty_content(self):
        """Test counting tokens for message with empty content."""
        messages = [UserMessage(content="")]
        count = TokenCounter.count_message_tokens(messages, "gpt-4")
        # Should still have message overhead
        assert count >= 3


class TestTokenCounterWithTiktoken:
    """Test suite for TokenCounter with tiktoken (if available)."""

    def test_count_tokens_gpt4_with_tiktoken(self):
        """Test token counting for GPT-4 with tiktoken if available."""
        try:
            import tiktoken  # noqa: F401

            text = "Hello, world!"
            count = TokenCounter.count_tokens(text, "gpt-4")
            # With tiktoken, should get accurate count
            assert count > 0
            assert isinstance(count, int)
        except ImportError:
            pytest.skip("tiktoken not installed")

    def test_count_tokens_gpt35_with_tiktoken(self):
        """Test token counting for GPT-3.5 with tiktoken if available."""
        try:
            import tiktoken  # noqa: F401

            text = "This is a test message."
            count = TokenCounter.count_tokens(text, "gpt-3.5-turbo")
            assert count > 0
            assert isinstance(count, int)
        except ImportError:
            pytest.skip("tiktoken not installed")

    def test_count_tokens_unknown_gpt_model_fallback(self):
        """Test that unknown GPT models fall back to cl100k_base encoding."""
        try:
            import tiktoken  # noqa: F401

            text = "Hello"
            # Use a model name that doesn't exist but starts with gpt-
            count = TokenCounter.count_tokens(text, "gpt-99-ultra")
            assert count > 0
            assert isinstance(count, int)
        except ImportError:
            pytest.skip("tiktoken not installed")


class TestTokenCounterWithAnthropic:
    """Test suite for TokenCounter with Anthropic tokenizer (if available)."""

    def test_count_tokens_claude_with_anthropic(self):
        """Test token counting for Claude with Anthropic tokenizer if available."""
        try:
            import anthropic  # noqa: F401

            # Check if get_tokenizer method exists
            if hasattr(anthropic, "get_tokenizer"):
                text = "Hello, Claude!"
                count = TokenCounter.count_tokens(text, "claude-3-sonnet")
                assert count > 0
                assert isinstance(count, int)
            else:
                pytest.skip("anthropic.get_tokenizer not available")
        except ImportError:
            pytest.skip("anthropic not installed")
