"""Core interface definitions for Nimbus.

This module provides all the abstract interfaces that define contracts for
Nimbus components. All implementations must adhere to these interfaces.
"""

from nimbus.interfaces.capability import CapabilityInterface, CapabilitySchema
from nimbus.interfaces.config_loader import ConfigLoaderInterface
from nimbus.interfaces.content_reader import ContentReaderInterface
from nimbus.interfaces.cost_calculator import CostCalculatorInterface
from nimbus.interfaces.error_handler import ErrorHandlerInterface
from nimbus.interfaces.event_handler import EventHandlerInterface
from nimbus.interfaces.memory import MemoryInterface
from nimbus.interfaces.model import ModelInterface
from nimbus.interfaces.multimodal_handler import MultimodalHandlerInterface
from nimbus.interfaces.observer import EventType, ObserverInterface
from nimbus.interfaces.plugin import PluginInterface
from nimbus.interfaces.prompt import PromptBuilderInterface
from nimbus.interfaces.route_registry import RouteRegistryInterface
from nimbus.interfaces.router import ModelRouterInterface, RoutingStrategy
from nimbus.interfaces.safety import SafetyFilterInterface, SafetyResult
from nimbus.interfaces.storage import StorageAdapterInterface
from nimbus.interfaces.token_counter import TokenCounterInterface
from nimbus.interfaces.vector_encoder import VectorEncoderInterface

__all__ = [
    # Core model and provider interfaces
    "ModelInterface",
    "VectorEncoderInterface",
    "ModelRouterInterface",
    "RouteRegistryInterface",
    "RoutingStrategy",
    # Prompt and message interfaces
    "PromptBuilderInterface",
    # Capability and tool interfaces
    "CapabilityInterface",
    "CapabilitySchema",
    # Memory and storage interfaces
    "MemoryInterface",
    "StorageAdapterInterface",
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
