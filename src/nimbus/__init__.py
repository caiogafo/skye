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
    >>> import nimbus
    >>> from nimbus.messages import UserMessage
    >>>
    >>> client = nimbus.provider("bedrock", region="us-east-1")
    >>> response = client.complete(
    ...     messages=[UserMessage("Hello")],
    ...     model="anthropic.claude-3-sonnet-20240229-v1:0"
    ... )
    >>> print(response.text)
"""

__version__ = "0.1.0"

# Core exports
from nimbus.completion import (
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
    TokenUsage,
)
from nimbus.config import (
    ConfigLoader,
    CooldownConfig,
    ModelConfig,
    NimbusConfig,
    RateLimitConfig,
    RetryConfig,
)
from nimbus.exceptions import (
    CapabilityExecutionError,
    ConfigurationError,
    NimbusError,
    ProviderError,
    ValidationError,
)
from nimbus.interfaces import (
    CapabilityInterface,
    CapabilitySchema,
    ContentReaderInterface,
    EventHandlerInterface,
    EventType,
    MemoryInterface,
    ModelInterface,
    ModelRouterInterface,
    ObserverInterface,
    PluginInterface,
    PromptBuilderInterface,
    RoutingStrategy,
    SafetyFilterInterface,
    SafetyResult,
    StorageAdapterInterface,
    VectorEncoderInterface,
)
from nimbus.messages import (
    AssistantMessage,
    CapabilityMessage,
    ContentChunk,
    NimbusMessage,
    SystemMessage,
    UserMessage,
)
from nimbus.providers.registry import provider
from nimbus import routes

__all__ = [
    "__version__",
    # Simple API
    "provider",
    "routes",
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
    "ConfigLoader",
    # Interfaces
    "ModelInterface",
    "PromptBuilderInterface",
    "CapabilityInterface",
    "CapabilitySchema",
    "MemoryInterface",
    "SafetyFilterInterface",
    "SafetyResult",
    "ObserverInterface",
    "EventType",
    "StorageAdapterInterface",
    "PluginInterface",
    "EventHandlerInterface",
    "VectorEncoderInterface",
    "ContentReaderInterface",
    "ModelRouterInterface",
    "RoutingStrategy",
]
