"""Observer interface for telemetry and observability.

This module defines the abstract interface for observability, including
event logging, metrics recording, and distributed tracing.

Raises: never raises to the caller: an observer failure is logged and swallowed.
Missing: ``end_trace`` for an unknown trace id is ignored.
Concurrency: called from request threads and tasks; an implementation must be thread-safe and must not block.
"""

from abc import abstractmethod
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class EventType(Enum):
    """Types of events that can be logged."""

    MODEL_INVOKE_START = "model_invoke_start"
    MODEL_INVOKE_END = "model_invoke_end"
    MODEL_INVOKE_ERROR = "model_invoke_error"
    CAPABILITY_INVOKE_START = "capability_invoke_start"
    CAPABILITY_INVOKE_END = "capability_invoke_end"
    CAPABILITY_INVOKE_ERROR = "capability_invoke_error"
    AGENT_STEP = "agent_step"
    AGENT_COMPLETE = "agent_complete"


@runtime_checkable
class ObserverInterface(Protocol):
    """Abstract interface for observability.

    This interface defines the contract for telemetry, logging, and tracing
    implementations. It supports structured event logging, metrics recording,
    and distributed tracing.
    """

    @abstractmethod
    def log_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Log a structured event.

        Args:
            event_type: The type of event being logged.
            data: Event data and metadata.
        """
        pass

    @abstractmethod
    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a metric value.

        Args:
            name: Metric name.
            value: Metric value.
            tags: Optional tags for the metric.
        """
        pass

    @abstractmethod
    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """Start a distributed trace.

        Args:
            name: Name of the trace span.
            metadata: Optional metadata for the trace.

        Returns:
            Trace ID for correlation.
        """
        pass

    @abstractmethod
    def end_trace(self, trace_id: str, metadata: dict[str, Any] | None = None) -> None:
        """End a distributed trace.

        Args:
            trace_id: The trace ID returned from start_trace.
            metadata: Optional metadata to add to the trace.
        """
        pass
