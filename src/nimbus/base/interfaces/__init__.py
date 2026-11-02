"""Core interface definitions for Nimbus.

This module provides all the abstract interfaces that define contracts for
Nimbus components. All implementations must adhere to these interfaces.
"""

from nimbus.base.interfaces.authentication import AuthenticationInterface
from nimbus.base.interfaces.authorizer import AuthorizerInterface, Decision
from nimbus.base.interfaces.capability import CapabilityInterface, CapabilitySchema
from nimbus.base.interfaces.config_loader import ConfigLoaderInterface
from nimbus.base.interfaces.content_reader import ContentReaderInterface
from nimbus.base.interfaces.cost_calculator import CostCalculatorInterface
from nimbus.base.interfaces.decision import DecisionModel, DecisionResult
from nimbus.base.interfaces.error_handler import ErrorHandlerInterface
from nimbus.base.interfaces.event_handler import EventHandlerInterface
from nimbus.base.interfaces.memory import MemoryInterface
from nimbus.base.interfaces.model import ModelInterface
from nimbus.base.interfaces.multimodal_handler import MultimodalHandlerInterface
from nimbus.base.interfaces.observer import EventType, ObserverInterface
from nimbus.base.interfaces.plugin import PluginInterface
from nimbus.base.interfaces.prompt import PromptBuilderInterface
from nimbus.base.interfaces.registry import (
    ProviderRegistryInterface,
    RouteRegistryInterface,
)
from nimbus.base.interfaces.router import ModelRouterInterface, RoutingStrategy
from nimbus.base.interfaces.runnable import Runnable
from nimbus.base.interfaces.safety import SafetyFilterInterface, SafetyResult
from nimbus.base.interfaces.storage import StorageAdapterInterface, StorageBackend
from nimbus.base.interfaces.token_counter import TokenCounterInterface
from nimbus.base.interfaces.vector_encoder import VectorEncoderInterface

__all__ = [
    # Core model and provider interfaces
    "ModelInterface",
    "VectorEncoderInterface",
    "ModelRouterInterface",
    "ProviderRegistryInterface",
    "RouteRegistryInterface",
    "RoutingStrategy",
    # Prompt and message interfaces
    "PromptBuilderInterface",
    # Composition and decision Ports
    "AuthorizerInterface",
    "Decision",
    "AuthenticationInterface",
    "Runnable",
    "DecisionModel",
    "DecisionResult",
    # Capability interfaces
    "CapabilityInterface",
    "CapabilitySchema",
    # Memory and storage interfaces
    "MemoryInterface",
    "StorageAdapterInterface",
    "StorageBackend",
    # Safety and filtering interfaces
    "SafetyFilterInterface",
    "SafetyResult",
    # Observability interfaces
    "ObserverInterface",
    "EventType",
    "EventHandlerInterface",
    # Plugin and extension interfaces
    "PluginInterface",
    # Content handling interfaces
    "ContentReaderInterface",
    "MultimodalHandlerInterface",
    # Utility interfaces
    "CostCalculatorInterface",
    "TokenCounterInterface",
    "ErrorHandlerInterface",
    "ConfigLoaderInterface",
]
