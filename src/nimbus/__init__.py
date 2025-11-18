"""Nimbus - Modular GenAI library with optional extras.

Nimbus provides a foundational layer for building AI agents and intelligent applications
with a Clean Architecture approach. The base package includes only interfaces and models,
while all implementations are available as optional extras.

Installation:
    pip install nimbus                    # Base only
    pip install nimbus[bedrock]           # + Bedrock provider
    pip install nimbus[agents,memory]     # + Multiple extras
    pip install nimbus[all]               # Everything

Example:
    >>> from nimbus.completion import CompletionRequest
    >>> from nimbus.messages import UserMessage
    >>> from nimbus.providers.bedrock import BedrockModel
    >>>
    >>> model = BedrockModel(model_id="anthropic.claude-3-sonnet")
    >>> response = model.complete(
    ...     CompletionRequest(
    ...         messages=[UserMessage(content="Hello")],
    ...         model="claude-3-sonnet"
    ...     )
    ... )
"""

__version__ = "0.1.0"

# Core exports
from nimbus.exceptions import (
    NimbusError,
    ProviderError,
    ConfigurationError,
    ValidationError,
    CapabilityExecutionError,
)
from nimbus.messages import (
    NimbusMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    CapabilityMessage,
    ContentChunk,
)
from nimbus.completion import (
    TokenUsage,
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
)
from nimbus.config import (
    RateLimitConfig,
    RetryConfig,
    CooldownConfig,
    ModelConfig,
    NimbusConfig,
)

__all__ = [
    "__version__",
    # Exceptions
    "NimbusError",
    "ProviderError",
    "ConfigurationError",
    "ValidationError",
    "CapabilityExecutionError",
    # Messages
    "NimbusMessage",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "CapabilityMessage",
    "ContentChunk",
    # Completion
    "TokenUsage",
    "CompletionRequest",
    "CompletionResponse",
    "StreamChunk",
    # Configuration
    "RateLimitConfig",
    "RetryConfig",
    "CooldownConfig",
    "ModelConfig",
    "NimbusConfig",
]
