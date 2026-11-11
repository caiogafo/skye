"""One ``describe(spec)`` for every kind of block (task 9.5 of the prompts spec, decision D83).

The code lives in ``skye.base.dsl.info`` next to the specs; ``skye.dsl`` is its public path, and
``skye.prompts`` keeps ``describe_prompt`` and ``prompt_help``.
"""

from __future__ import annotations

import pytest

import skye.dsl
import skye.prompts
from skye.base.dsl import build
from skye.base.dsl.info import FlowInfo, PromptInfo, RouterInfo, describe, describe_prompt

TEXT = """---
title = "Demo"
version = "2.0"
---

router "main" {
  strategy = "least_busy"
  route "fast" = ["openai/gpt-4o-mini", "anthropic/claude-haiku"]
  route "smart" {
    fallback = ["fast"]
    target {
      model = "gpt-4o"
      provider = "openai"
    }
  }
}

prompt "greet" {
  variables = { name = string "Who to greet" }
  message "user" { text = "Hi {{ name }}" }
}

flow "triage" {
  context { ticket = string, priority = number(1) }
  step "classify" { run = registry.classifier, next = "reply" }
  step "reply" { run = registry.writer, next = end }
}
"""


@pytest.fixture(scope="module")
def document():  # type: ignore[no-untyped-def]
    doc = build(TEXT)
    assert doc.diagnostics == []
    return doc


def test_a_prompt_gives_the_prompt_info(document) -> None:  # type: ignore[no-untyped-def]
    spec = document.prompt("greet")
    info = describe(spec, document.metadata)
    assert isinstance(info, PromptInfo)
    assert info == describe_prompt(spec, document.metadata)
    assert info.title == "Demo" and info.version == "2.0"


def test_a_router_gives_its_routes_targets_and_fallbacks(document) -> None:  # type: ignore[no-untyped-def]
    info = describe(document.routers[0], document.metadata)
    assert isinstance(info, RouterInfo)
    assert info.name == "main" and info.strategy == "least_busy" and info.title == "Demo"
    routes = {route.alias: route for route in info.routes}
    assert routes["fast"].targets == ["openai/gpt-4o-mini"]
    assert routes["fast"].fallback_targets == ["anthropic/claude-haiku"]
    assert routes["smart"].targets == ["openai/gpt-4o"]
    assert routes["smart"].fallback == ["fast"]


def test_a_flow_gives_its_context_and_steps(document) -> None:  # type: ignore[no-untyped-def]
    info = describe(document.flows[0])
    assert isinstance(info, FlowInfo)
    assert info.name == "triage" and info.start == "classify"
    assert [(i.name, i.type, i.required, i.default) for i in info.inputs] == [
        ("ticket", "string", True, None),
        ("priority", "number", False, 1),
    ]
    assert [(s.name, s.kind, s.run, s.next) for s in info.steps] == [
        ("classify", "step", "registry.classifier", "reply"),
        ("reply", "step", "registry.writer", "end"),
    ]


def test_anything_else_is_a_type_error() -> None:
    with pytest.raises(TypeError, match="PromptSpec, RouterSpec or FlowSpec"):
        describe("not a spec")  # type: ignore[arg-type]


def test_describe_is_public_in_skye_dsl_and_prompts_keeps_its_names() -> None:
    assert "describe" in skye.dsl.__all__ and skye.dsl.describe is describe
    for name in ("describe_prompt", "prompt_help"):
        assert name in skye.prompts.__all__
