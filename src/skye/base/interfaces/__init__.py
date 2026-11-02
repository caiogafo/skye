"""Core interface definitions for Skye.

This module provides all the abstract interfaces that define contracts for
Skye components. All implementations must adhere to these interfaces.
"""

from skye.base.interfaces.authentication import AuthenticationInterface
from skye.base.interfaces.authorizer import AuthorizerInterface, Decision
from skye.base.interfaces.capability import CapabilityInterface, CapabilitySchema
from skye.base.interfaces.config_loader import ConfigLoaderInterface
from skye.base.interfaces.content_reader import ContentReaderInterface
from skye.base.interfaces.cost_calculator import CostCalculatorInterface
from skye.base.interfaces.decision import DecisionModel, DecisionResult
from skye.base.interfaces.error_handler import ErrorHandlerInterface
from skye.base.interfaces.event_handler import EventHandlerInterface
from skye.base.interfaces.memory import MemoryInterface
from skye.base.interfaces.model import ModelInterface
from skye.base.interfaces.multimodal_handler import MultimodalHandlerInterface
from skye.base.interfaces.observer import EventType, ObserverInterface
from skye.base.interfaces.plugin import PluginInterface
from skye.base.interfaces.prompt import PromptBuilderInterface
from skye.base.interfaces.registry import (
    ProviderRegistryInterface,
    RouteRegistryInterface,
)
from skye.base.interfaces.router import ModelRouterInterface, RoutingStrategy
from skye.base.interfaces.runnable import Runnable
from skye.base.interfaces.safety import SafetyFilterInterface, SafetyResult
from skye.base.interfaces.storage import StorageAdapterInterface, StorageBackend
from skye.base.interfaces.token_counter import TokenCounterInterface
from skye.base.interfaces.vector_encoder import VectorEncoderInterface

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
