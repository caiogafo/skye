"""LLM provider implementations for Skye.

This module provides concrete implementations of ModelInterface for various
LLM providers including OpenAI, Anthropic, AWS Bedrock, Azure, and Google.

Example:
    >>> from skye.models.llm import OpenAIProvider
    >>> from skye.base.completion import CompleteRequest
    >>> from skye.base.messages import UserMessage
    >>>
    >>> provider = OpenAIProvider(api_key="sk-...")
    >>> request = CompleteRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gpt-4"
    ... )
    >>> response = provider.complete(request)
"""

from skye.models.llm.anthropic import AnthropicProvider
from skye.models.llm.anthropic_compatible import AnthropicCompatibleProvider
from skye.models.llm.bedrock import BedrockProvider
from skye.models.llm.azure import AzureOpenAIProvider
from skye.models.llm.openai import OpenAIProvider
from skye.models.llm.openai_compatible import OpenAICompatibleProvider
from skye.models.llm.google import GoogleProvider

__all__ = [
    "OpenAICompatibleProvider",
    "OpenAIProvider",
    "AnthropicCompatibleProvider",
    "AnthropicProvider",
    "BedrockProvider",
    "AzureOpenAIProvider",
    "GoogleProvider",
]
