"""Event handler interface for lifecycle hooks.

This module defines the abstract interface for event handlers that respond
to various lifecycle events during model and capability invocations.
"""

from abc import ABC, abstractmethod
from typing import Any


class EventHandlerInterface(ABC):
    """Abstract interface for event handlers.

    This interface defines the contract for handling lifecycle events
    during model invocations, capability executions, and agent operations.
    """

    @abstractmethod
    def on_model_invoke_start(self, model_id: str, request: Any) -> None:
        """Called when a model invocation starts.

        Args:
            model_id: Identifier of the model being invoked.
            request: The completion request.
        """
        pass

    @abstractmethod
    def on_model_invoke_end(self, model_id: str, response: Any) -> None:
        """Called when a model invocation completes successfully.

        Args:
            model_id: Identifier of the model that was invoked.
            response: The completion response.
        """
        pass

    @abstractmethod
    def on_model_invoke_error(self, model_id: str, error: Exception) -> None:
        """Called when a model invocation fails.

        Args:
            model_id: Identifier of the model that failed.
            error: The exception that occurred.
        """
        pass

    @abstractmethod
    def on_capability_invoke_start(self, capability_name: str, args: dict[str, Any]) -> None:
        """Called when a capability invocation starts.

        Args:
            capability_name: Name of the capability being invoked.
            args: Arguments passed to the capability.
        """
        pass

    @abstractmethod
    def on_capability_invoke_end(self, capability_name: str, result: Any) -> None:
        """Called when a capability invocation completes successfully.

        Args:
            capability_name: Name of the capability that was invoked.
            result: The result returned by the capability.
        """
        pass

    @abstractmethod
    def on_capability_invoke_error(self, capability_name: str, error: Exception) -> None:
        """Called when a capability invocation fails.

        Args:
            capability_name: Name of the capability that failed.
            error: The exception that occurred.
        """
        pass

    @abstractmethod
    def on_execution_step(self, step_number: int, data: dict[str, Any]) -> None:
        """Called after each execution step.

        Args:
            step_number: The step number in the execution sequence.
            data: Data about the step execution.
        """
        pass

    @abstractmethod
    def on_execution_complete(self, result: Any) -> None:
        """Called when execution completes.

        Args:
            result: The final result of the execution.
        """
        pass
