"""Cost calculator interface for API usage cost estimation.

This module defines the abstract interface for calculating API costs based on
token usage and model pricing.

Raises: ValidationError for a negative token count or price.
Missing: ``get_pricing`` returns ``None`` for a model with no price; ``calculate_cost`` for such a model raises ValidationError.
Concurrency: pricing tables are mutated by ``add_custom_pricing``: guard it if called from several threads.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from abc import ABC, abstractmethod


if TYPE_CHECKING:
    from skye.base.completion import TokenUsage



class CostCalculatorInterface(ABC):
    """Abstract interface for cost calculation.

    This interface defines the contract for calculating API costs based on
    token usage and model pricing information.

    Example:
        >>> class MyCostCalculator(CostCalculatorInterface):
        ...     def calculate_cost(self, model, usage, custom_pricing=None):
        ...         # Implementation
        ...         return 0.05
        ...
        ...     def get_pricing(self, model):
        ...         return {"prompt": 10.0, "completion": 30.0}
    """

    @abstractmethod
    def calculate_cost(
        self, model: str, usage: TokenUsage, custom_pricing: dict[str, float] | None = None
    ) -> float:
        """Calculate cost for a completion.

        Args:
            model: Model identifier (e.g., 'gpt-4', 'claude-3-sonnet').
            usage: Token usage information from the completion.
            custom_pricing: Optional custom pricing override with 'prompt' and
                'completion' keys (per 1M tokens).

        Returns:
            Estimated cost in USD.

        Example:
            >>> usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
            >>> cost = calculator.calculate_cost("gpt-4", usage)
            >>> cost > 0
            True
        """
        pass

    @abstractmethod
    def get_pricing(self, model: str) -> dict[str, float] | None:
        """Get pricing information for a model.

        Args:
            model: Model identifier.

        Returns:
            Dictionary with 'prompt' and 'completion' prices per 1M tokens,
            or None if model pricing is not available.

        Example:
            >>> pricing = calculator.get_pricing("gpt-4")
            >>> pricing is not None
            True
        """
        pass

    @abstractmethod
    def add_custom_pricing(
        self, model: str, prompt_price: float, completion_price: float
    ) -> None:
        """Add custom pricing for a model.

        Args:
            model: Model identifier.
            prompt_price: Price per 1M prompt tokens in USD.
            completion_price: Price per 1M completion tokens in USD.

        Example:
            >>> calculator.add_custom_pricing("my-model", 5.0, 10.0)
        """
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """List all models with known pricing.

        Returns:
            List of model identifiers with pricing data.

        Example:
            >>> models = calculator.list_models()
            >>> "gpt-4" in models
            True
        """
        pass
