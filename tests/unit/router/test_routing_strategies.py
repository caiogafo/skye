"""Routing strategies: the weighted strategy must not fail when every weight is zero."""

from __future__ import annotations

from types import SimpleNamespace

from skye.base.interfaces.router import RoutingStrategy
from skye.router.routing_strategies import RoutingStrategySelector


def _selector(weights: dict[str, float]) -> RoutingStrategySelector:
    targets = {name: SimpleNamespace(weight=w) for name, w in weights.items()}
    return RoutingStrategySelector(health={}, rate_limits={}, model_targets=targets, round_robin_index={})


def test_weighted_picks_among_models_with_positive_weight():
    selector = _selector({"a": 0.0, "b": 1.0})
    picks = {selector.apply_strategy(["a", "b"], strategy=RoutingStrategy.WEIGHTED) for _ in range(50)}
    assert picks == {"b"}


def test_weighted_with_all_zero_weights_falls_back_to_a_uniform_pick():
    selector = _selector({"a": 0.0, "b": 0.0})
    pick = selector.apply_strategy(["a", "b"], strategy=RoutingStrategy.WEIGHTED)
    assert pick in {"a", "b"}
