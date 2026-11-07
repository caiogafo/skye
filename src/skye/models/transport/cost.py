"""Cost calculation utilities for model API usage.

This module provides utilities for estimating API costs based on token usage
and model pricing. It includes pricing data for major models and supports
custom pricing configurations.

Example:
    >>> from skye.models.transport.cost import CostCalculator
    >>> from skye.base.completion import TokenUsage
    >>>
    >>> usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    >>> cost = CostCalculator.calculate_cost("gpt-4", usage)
    >>> print(f"${cost:.4f}")
    $0.0045
"""

from skye.base.completion import TokenUsage
from skye.base.interfaces.cost_calculator import CostCalculatorInterface


class CostCalculator(CostCalculatorInterface):
    """Calculate API costs based on token usage.

    This class provides methods to estimate costs for API calls based on
    token usage and model pricing. Pricing is per 1M tokens.

    Attributes:
        PRICING: Dictionary of pricing data for known models.

    Example:
        >>> usage = TokenUsage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        >>> cost = CostCalculator.calculate_cost("gpt-4", usage)
        >>> cost > 0
        True
    """

    # Pricing data (per 1M tokens) - Updated as of November 2024
    PRICING: dict[str, dict[str, float]] = {
        # OpenAI GPT-4 models
        "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
        "gpt-4-turbo-preview": {"prompt": 10.00, "completion": 30.00},
        "gpt-4-1106-preview": {"prompt": 10.00, "completion": 30.00},
        "gpt-4-0125-preview": {"prompt": 10.00, "completion": 30.00},
        "gpt-4": {"prompt": 30.00, "completion": 60.00},
        "gpt-4-0613": {"prompt": 30.00, "completion": 60.00},
        "gpt-4-32k": {"prompt": 60.00, "completion": 120.00},
        "gpt-4-32k-0613": {"prompt": 60.00, "completion": 120.00},
        # OpenAI GPT-3.5 models
        "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
        "gpt-3.5-turbo-0125": {"prompt": 0.50, "completion": 1.50},
        "gpt-3.5-turbo-1106": {"prompt": 1.00, "completion": 2.00},
        "gpt-3.5-turbo-16k": {"prompt": 3.00, "completion": 4.00},
        # OpenAI o1 models
        "o1-preview": {"prompt": 15.00, "completion": 60.00},
        "o1-mini": {"prompt": 3.00, "completion": 12.00},
        # Anthropic Claude 3 models
        "claude-3-opus-20240229": {"prompt": 15.00, "completion": 75.00},
        "claude-3-sonnet-20240229": {"prompt": 3.00, "completion": 15.00},
        "claude-3-haiku-20240307": {"prompt": 0.25, "completion": 1.25},
        "claude-3-5-sonnet-20240620": {"prompt": 3.00, "completion": 15.00},
        # Simplified model names
        "claude-3-opus": {"prompt": 15.00, "completion": 75.00},
        "claude-3-sonnet": {"prompt": 3.00, "completion": 15.00},
        "claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
        "claude-3.5-sonnet": {"prompt": 3.00, "completion": 15.00},
        # AWS Bedrock models (approximate, may vary by region)
        "anthropic.claude-3-opus-20240229-v1:0": {"prompt": 15.00, "completion": 75.00},
        "anthropic.claude-3-sonnet-20240229-v1:0": {"prompt": 3.00, "completion": 15.00},
        "anthropic.claude-3-haiku-20240307-v1:0": {"prompt": 0.25, "completion": 1.25},
        "anthropic.claude-3-5-sonnet-20240620-v1:0": {"prompt": 3.00, "completion": 15.00},
        # Google models (approximate)
        "gemini-pro": {"prompt": 0.50, "completion": 1.50},
        "gemini-pro-vision": {"prompt": 0.50, "completion": 1.50},
        "gemini-1.5-pro": {"prompt": 3.50, "completion": 10.50},
        "gemini-1.5-flash": {"prompt": 0.35, "completion": 1.05},
    }

    @classmethod
    def calculate_cost(
        cls, model: str, usage: TokenUsage, custom_pricing: dict[str, float] | None = None
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
            >>> usage = TokenUsage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
            >>> cost = CostCalculator.calculate_cost("gpt-4", usage)
            >>> cost > 0
            True
            >>>
            >>> # With custom pricing
            >>> custom = {"prompt": 5.0, "completion": 10.0}
            >>> cost = CostCalculator.calculate_cost("custom-model", usage, custom)
            >>> cost > 0
            True
        """
        pricing = custom_pricing or cls.PRICING.get(model)

        if not pricing:
            return 0.0  # Unknown model, can't estimate

        prompt_cost = (usage.prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1_000_000) * pricing["completion"]

        return prompt_cost + completion_cost

    @classmethod
    def add_custom_pricing(cls, model: str, prompt_price: float, completion_price: float) -> None:
        """Add custom pricing for a model.

        This allows you to add pricing for custom or fine-tuned models that
        aren't in the default pricing table.

        Args:
            model: Model identifier.
            prompt_price: Price per 1M prompt tokens in USD.
            completion_price: Price per 1M completion tokens in USD.

        Example:
            >>> CostCalculator.add_custom_pricing("my-custom-model", 5.0, 10.0)
            >>> "my-custom-model" in CostCalculator.PRICING
            True
        """
        cls.PRICING[model] = {"prompt": prompt_price, "completion": completion_price}

    @classmethod
    def get_pricing(cls, model: str) -> dict[str, float] | None:
        """Get pricing information for a model.

        Args:
            model: Model identifier.

        Returns:
            Dictionary with 'prompt' and 'completion' prices per 1M tokens,
            or None if model pricing is not available.

        Example:
            >>> pricing = CostCalculator.get_pricing("gpt-4")
            >>> pricing is not None
            True
            >>> "prompt" in pricing and "completion" in pricing
            True
        """
        return cls.PRICING.get(model)

    @classmethod
    def list_models(cls) -> list[str]:
        """List all models with known pricing.

        Returns:
            List of model identifiers with pricing data.

        Example:
            >>> models = CostCalculator.list_models()
            >>> "gpt-4" in models
            True
        """
        return list(cls.PRICING.keys())
