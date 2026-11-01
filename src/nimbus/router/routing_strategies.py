"""Routing strategy implementations for model router.

This module contains the logic for different routing strategies
used to select models from available targets.
"""

import random
from typing import TYPE_CHECKING

from nimbus.base.interfaces.router import RoutingStrategy

if TYPE_CHECKING:
    from .config_models import ModelTarget
    from .health_tracker import ModelHealth, RateLimitTracker


class RoutingStrategySelector:
    """Handles model selection based on different routing strategies."""

    def __init__(
        self,
        health: dict[str, "ModelHealth"],
        rate_limits: dict[str, "RateLimitTracker"],
        model_targets: dict[str, "ModelTarget"],
        round_robin_index: dict[str, int],
    ):
        """Initialize the strategy selector.

        Args:
            health: Dictionary of model health trackers.
            rate_limits: Dictionary of rate limit trackers.
            model_targets: Dictionary of model target configurations.
            round_robin_index: Dictionary tracking round-robin indices.
        """
        self.health = health
        self.rate_limits = rate_limits
        self.model_targets = model_targets
        self.round_robin_index = round_robin_index

    def apply_strategy(
        self,
        available_models: list[str],
        alias: str | None = None,
        strategy: RoutingStrategy | None = None,
    ) -> str:
        """Apply routing strategy to select a model.

        Args:
            available_models: List of available model IDs.
            alias: Optional alias for round-robin tracking.
            strategy: Routing strategy to use.

        Returns:
            Selected model ID.

        Raises:
            ValueError: If no models are available or strategy is invalid.
        """
        if not available_models:
            raise ValueError("No available models for routing")

        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_strategy(available_models, alias)
        elif strategy == RoutingStrategy.SIMPLE_SHUFFLE:
            return self._simple_shuffle_strategy(available_models)
        elif strategy == RoutingStrategy.LEAST_BUSY:
            return self._least_busy_strategy(available_models)
        elif strategy == RoutingStrategy.LATENCY_BASED:
            return self._latency_based_strategy(available_models)
        elif strategy == RoutingStrategy.RATE_LIMIT_AWARE:
            return self._rate_limit_aware_strategy(available_models)
        elif strategy == RoutingStrategy.WEIGHTED:
            return self._weighted_strategy(available_models)
        elif strategy == RoutingStrategy.PRIORITY_BASED:
            return self._priority_based_strategy(available_models)
        else:
            # Default to first available
            return available_models[0]

    def _round_robin_strategy(self, available_models: list[str], alias: str | None) -> str:
        """Round-robin selection strategy."""
        key = alias if alias else "_default"
        index = self.round_robin_index.get(key, 0)
        model_id = available_models[index % len(available_models)]
        self.round_robin_index[key] = index + 1
        return model_id

    def _simple_shuffle_strategy(self, available_models: list[str]) -> str:
        """Random selection strategy."""
        return random.choice(available_models)

    def _least_busy_strategy(self, available_models: list[str]) -> str:
        """Select model with least active requests."""
        return min(
            available_models,
            key=lambda m: self.rate_limits[m].active_requests,
        )

    def _latency_based_strategy(self, available_models: list[str]) -> str:
        """Select model with lowest average latency."""
        return min(
            available_models,
            key=lambda m: self.health[m].get_avg_latency_ms(),
        )

    def _rate_limit_aware_strategy(self, available_models: list[str]) -> str:
        """Select model with most available rate limit capacity."""

        def get_capacity_score(model_id: str) -> float:
            """Calculate capacity score (0.0 = full, 1.0 = empty)."""
            tracker = self.rate_limits[model_id]
            if tracker.rpm_limit is None and tracker.tpm_limit is None:
                return 1.0

            rpm_capacity = 1.0
            if tracker.rpm_limit:
                rpm_capacity = 1.0 - (tracker.rpm_used / tracker.rpm_limit)

            tpm_capacity = 1.0
            if tracker.tpm_limit:
                tpm_capacity = 1.0 - (tracker.tpm_used / tracker.tpm_limit)

            return min(rpm_capacity, tpm_capacity)

        return max(available_models, key=get_capacity_score)

    def _weighted_strategy(self, available_models: list[str]) -> str:
        """Select model based on weights (target weight or success rate)."""
        weights = []
        for model_id in available_models:
            if model_id in self.model_targets:
                weights.append(self.model_targets[model_id].weight)
            else:
                weights.append(self.health[model_id].get_success_rate())
        
        return random.choices(available_models, weights=weights)[0]

    def _priority_based_strategy(self, available_models: list[str]) -> str:
        """Select model with highest success rate (priority)."""
        return max(
            available_models,
            key=lambda m: self.health[m].get_success_rate(),
        )