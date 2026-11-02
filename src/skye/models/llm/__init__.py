"""LLM provider implementations for Skye.

This module provides concrete implementations of ModelInterface for various
LLM providers including OpenAI, Anthropic, AWS Bedrock, Azure, and Google.

Example:
    >>> from skye.models.llm import OpenAIProvider
    >>> from skye.base.completion import CompletionRequest
    >>> from skye.base.messages import UserMessage
    >>>
    >>> provider = OpenAIProvider(api_key="sk-...")
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gpt-4"
    ... )
    >>> response = provider.complete(request)
"""

from skye.models.llm.anthropic import AnthropicProvider
from skye.models.llm.bedrock import BedrockProvider
from skye.models.llm.openai_compatible import AzureOpenAIProvider, OpenAIProvider
from skye.models.llm.google_provider import GoogleProvider

__all__ = [
    "OpenAIProvider",
    "AnthropicProvider",
    "BedrockProvider",
    "AzureOpenAIProvider",
    "GoogleProvider",
]
