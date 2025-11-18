"""LLM provider implementations for Nimbus.

This module provides concrete implementations of ModelInterface for various
LLM providers including OpenAI, Anthropic, AWS Bedrock, Azure, and Google Vertex AI.

Example:
    >>> from nimbus.providers.llm import OpenAIProvider
    >>> from nimbus.completion import CompletionRequest
    >>> from nimbus.messages import UserMessage
    >>>
    >>> provider = OpenAIProvider(api_key="sk-...")
    >>> request = CompletionRequest(
    ...     messages=[UserMessage(content="Hello")],
    ...     model="gpt-4"
    ... )
    >>> response = provider.complete(request)
"""

from nimbus.providers.llm.anthropic_provider import AnthropicProvider
from nimbus.providers.llm.azure_provider import AzureOpenAIProvider
from nimbus.providers.llm.bedrock_provider import BedrockProvider
from nimbus.providers.llm.openai_provider import OpenAIProvider
from nimbus.providers.llm.vertex_provider import VertexAIProvider

__all__ = [
    "OpenAIProvider",
    "AnthropicProvider",
    "BedrockProvider",
    "AzureOpenAIProvider",
    "VertexAIProvider",
]
