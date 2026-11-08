"""``cost_based``: the available target with the lowest estimated cost wins (task 3.1, D68).

The cost of a target is ``cost_per_1k_prompt_tokens + cost_per_1k_completion_tokens``, or, with a
token estimate, each price weighted by its tokens / 1000. Targets without a cost come last; ties
keep the configured order.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from skye.base.completion import CompleteRequest
from skye.base.dsl import block_schema, build, to_text
from skye.base.exceptions import ConfigurationError
from skye.base.interfaces.router import RoutingStrategy
from skye.base.messages import UserMessage
from skye.router import ModelRouter, ModelTarget, RouteConfig
from skye.router.routing_strategies import RoutingStrategySelector, estimated_cost


def _target(
    model: str, prompt: float | None = None, completion: float | None = None
) -> ModelTarget:
    return ModelTarget(
        model=model,
        provider="openai",
        api_key="k",
        cost_per_1k_prompt_tokens=prompt,
        cost_per_1k_completion_tokens=completion,
    )


def _pick(targets: dict[str, ModelTarget], available: list[str] | None = None, **kwargs) -> str:
    selector = RoutingStrategySelector(
        health={}, rate_limits={}, model_targets=targets, round_robin_index={}
    )
    return selector.apply_strategy(
        available or list(targets), strategy=RoutingStrategy.COST_BASED, **kwargs
    )


def test_the_cheapest_target_is_picked_whatever_its_position():
    targets = {
        "a": _target("a", 0.03, 0.06),
        "b": _target("b", 0.0005, 0.0015),
        "c": _target("c", 0.001, 0.002),
    }
    assert _pick(targets) == "b"


def test_targets_without_a_cost_sort_last():
    targets = {"free?": _target("free?"), "priced": _target("priced", 5.0, 5.0)}
    assert _pick(targets) == "priced"


def test_with_no_cost_anywhere_the_first_target_is_picked():
    targets = {"a": _target("a"), "b": _target("b")}
    assert _pick(targets) == "a"


def test_ties_keep_the_configured_order():
    targets = {
        "a": _target("a", 1.0, 1.0),
        "b": _target("b", 0.5, 1.5),
        "c": _target("c", 2.0, 0.0),
    }
    assert _pick(targets) == "a"
    assert _pick(targets, ["b", "a", "c"]) == "b"


def test_one_price_left_out_counts_as_zero():
    targets = {"both": _target("both", 0.001, 0.001), "prompt_only": _target("prompt_only", 0.0015)}
    assert estimated_cost(targets["prompt_only"]) == 0.0015
    assert _pick(targets) == "prompt_only"


def test_only_available_targets_are_considered():
    targets = {"cheap": _target("cheap", 0.1, 0.1), "dear": _target("dear", 1.0, 1.0)}
    assert _pick(targets, ["dear"]) == "dear"


def test_a_token_estimate_weights_each_price_by_its_tokens():
    # Cheap prompts, dear completions against the opposite: the long prompt decides.
    targets = {
        "cheap_out": _target("cheap_out", 0.01, 0.001),
        "cheap_in": _target("cheap_in", 0.001, 0.01),
    }
    assert _pick(targets) == "cheap_out"  # equal sums: configured order
    assert _pick(targets, token_estimate=(10_000, 100)) == "cheap_in"
    assert _pick(targets, token_estimate=(100, 10_000)) == "cheap_out"
    assert estimated_cost(targets["cheap_in"], (2000, 500)) == pytest.approx(2 * 0.001 + 0.5 * 0.01)


def test_a_negative_cost_is_rejected():
    with pytest.raises((ConfigurationError, ValueError)):
        _target("x", -0.1, 0.0)


def test_the_router_resolves_a_cost_based_alias_to_the_cheapest_target():
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="budget",
                targets=[_target("dear", 0.03, 0.06), _target("cheap", 0.0005, 0.0015)],
                strategy=RoutingStrategy.COST_BASED,
            )
        ]
    )
    request = CompleteRequest(messages=[UserMessage(content="hi")], model="budget")
    assert asyncio.run(router.select_model(request)) == "budget:openai:cheap"


def test_the_router_weights_prices_by_the_request_size():
    # Cheap prompt / dear completion vs dear prompt / cheap completion: the request decides.
    router = ModelRouter(
        routes=[
            RouteConfig(
                alias="mix",
                targets=[_target("reader", 0.001, 0.1), _target("writer", 0.1, 0.001)],
                strategy=RoutingStrategy.COST_BASED,
            )
        ]
    )
    long_prompt = CompleteRequest(
        messages=[UserMessage(content="x" * 40_000)], model="mix", max_tokens=10
    )
    long_answer = CompleteRequest(
        messages=[UserMessage(content="hi")], model="mix", max_tokens=4_000
    )
    assert asyncio.run(router.select_model(long_prompt)) == "mix:openai:reader"
    assert asyncio.run(router.select_model(long_answer)) == "mix:openai:writer"


ROUTER = """
router "r" {
  route "budget" {
    strategy = "cost_based"
    target {
      model = "dear", provider = "openai"
      cost_per_1k_prompt_tokens = 0.03, cost_per_1k_completion_tokens = 0.06
    }
    target {
      model = "cheap", provider = "openai"
      cost_per_1k_prompt_tokens = 0.0005, cost_per_1k_completion_tokens = 0.0015
    }
  }
}
"""


def test_the_cost_fields_are_target_fields_of_the_language(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    spec = build(ROUTER).raise_for_errors().router("r")
    first = spec.routes[0].targets[0]
    assert (first.cost_per_1k_prompt_tokens, first.cost_per_1k_completion_tokens) == (0.03, 0.06)
    text = to_text(spec)
    assert (
        "cost_per_1k_prompt_tokens = 0.0005" in text
        and "cost_per_1k_completion_tokens = 0.06" in text
    )
    assert to_text(build(text).raise_for_errors().router("r")) == text

    path = tmp_path / "router.skye"
    path.write_text(ROUTER, encoding="utf-8")
    router = ModelRouter.from_file(path)
    cheap = router.aliases["budget"].targets[1]
    assert (cheap.cost_per_1k_prompt_tokens, cheap.cost_per_1k_completion_tokens) == (
        0.0005,
        0.0015,
    )
    assert not cheap.extras

    config = router.to_config()
    assert config["routes"][0]["targets"][1]["cost_per_1k_completion_tokens"] == 0.0015
    again = ModelRouter.from_config_dict(json.loads(json.dumps(config)))
    assert again.to_config() == config
    assert "cost_per_1k_prompt_tokens = 0.03" in router.to_skye("r")


def test_a_negative_cost_in_a_block_is_reported():
    document = build(ROUTER.replace("0.03", "-0.03"))
    assert not document.ok
    assert any("cost_per_1k_prompt_tokens" in d.format() for d in document.diagnostics)


def test_the_block_schema_lists_the_cost_fields():
    schema = json.dumps(block_schema("router"))
    assert "cost_per_1k_prompt_tokens" in schema and "cost_per_1k_completion_tokens" in schema
