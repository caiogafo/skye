"""Core interface definitions for Nimbus.

This module provides all the abstract interfaces that define contracts for
Nimbus components. All implementations must adhere to these interfaces.
"""

from nimbus.interfaces.capability import CapabilityInterface, CapabilitySchema
from nimbus.interfaces.content_reader import ContentReaderInterface
from nimbus.interfaces.event_handler import EventHandlerInterface
from nimbus.interfaces.memory import MemoryInterface
from nimbus.interfaces.model import ModelInterface
from nimbus.interfaces.observer import EventType, ObserverInterface
from nimbus.interfaces.plugin import PluginInterface
from nimbus.interfaces.prompt import PromptBuilderInterface
from nimbus.interfaces.router import ModelRouterInterface, RoutingStrategy
from nimbus.interfaces.safety import SafetyFilterInterface, SafetyResult
from nimbus.interfaces.storage import StorageAdapterInterface
from nimbus.interfaces.vector_encoder import VectorEncoderInterface

__all__ = [
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
