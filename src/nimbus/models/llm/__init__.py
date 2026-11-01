"""LLM provider implementations for Nimbus.

This module provides concrete implementations of ModelInterface for various
LLM providers including OpenAI, Anthropic, AWS Bedrock, Azure, and Google.

Example:
    >>> from nimbus.models.llm import OpenAIProvider
    >>> from nimbus.base.completion import CompletionRequest
    >>> from nimbus.base.messages import UserMessage
    >>>
    >>> provider = OpenAIProvider(api_key="sk-...")
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gpt-4"
    ... )
    >>> response = provider.complete(request)
"""

from nimbus.models.llm.anthropic import AnthropicProvider
from nimbus.models.llm.bedrock import BedrockProvider
from nimbus.models.llm.openai_compatible import AzureOpenAIProvider, OpenAIProvider
from nimbus.models.llm.google_provider import GoogleProvider

__all__ = [
    "OpenAIProvider",
    "AnthropicProvider",
    "BedrockProvider",
    "AzureOpenAIProvider",
    "GoogleProvider",
]
