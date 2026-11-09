"""``to_mermaid``: a flow or a router as a Mermaid diagram (Requirement 54.21, decision D88).

There is no Mermaid library (D49): the tests check the structure of the text.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from skye.base.dsl import build, to_mermaid
from skye.base.dsl.specs import FlowSpec, ParallelSpec, StepSpec

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "skye"

FLOW = """\
flow "review" {
  step "Draft" {
    run = registry.writer
    next = "Check"
    on_error = "Fail"
    timeout = "30s"
    max_visits = 3
    on_timeout = "Fail"
  }
  choice "Check" {
    when step.Draft.output.score > 0.8 { next = end }
    else { next = "Draft" }
  }
  step "Fail" { run = registry.notify, next = end }
}
"""


def _flow(text: str = FLOW) -> FlowSpec:
    document = build(text, registry_names=None)
    assert not document.diagnostics, document.diagnostics
    return document.flows[0]


def _nodes(diagram: str) -> dict[str, str]:
    """Node id -> label, for boxes, diamonds and subgraphs."""
    found = {}
    for match in re.finditer(r'^\s*(?:subgraph )?(\w+)\s*[\[{(]+"([^"]*)"', diagram, re.M):
        found[match.group(1)] = match.group(2)
    return found


def _edges(diagram: str) -> list[tuple[str, str, str, str]]:
    """(source, arrow, label, target) for every edge."""
    pattern = r'^\s*(\w+) (-->|-\.->)(?:\|"([^"]*)"\|)? (\w+)\s*$'
    return [(m[1], m[2], m[3] or "", m[4]) for m in re.finditer(pattern, diagram, re.M)]


def test_every_step_is_a_node_and_every_next_an_edge():
    diagram = to_mermaid(_flow())
    nodes = _nodes(diagram)
    labels = {label.split("<br/>")[0]: node for node, label in nodes.items()}
    assert {"Draft", "Check", "Fail"} <= set(labels)
    assert 'start(("start"))' in diagram and 'done(("end"))' in diagram
    edges = _edges(diagram)
    draft, check, fail = labels["Draft"], labels["Check"], labels["Fail"]
    assert (draft, "-->", "", check) in edges
    assert (draft, "-.->", "on_error", fail) in edges
    assert (draft, "-.->", "on_timeout", fail) in edges
    assert (check, "-->", "else", draft) in edges
    assert (check, "-->", "step.Draft.output.score #gt; 0.8", "done") in edges
    assert f'start(("start")) --> {draft}' in diagram
    assert diagram.startswith("flowchart TD\n") and diagram.endswith("\n")


def test_a_choice_is_a_diamond_and_run_is_in_the_label():
    diagram = to_mermaid(_flow())
    assert re.search(r'^\s*n2\{"Check"\}$', diagram, re.M)
    assert '["Draft<br/>run: registry.writer<br/>max_visits: 3"]' in diagram


def test_the_diagram_is_deterministic():
    assert to_mermaid(_flow()) == to_mermaid(_flow())


def test_labels_are_escaped():
    diagram = to_mermaid(_flow(FLOW.replace("> 0.8", '== "a<b&c"')))
    assert "#quot;a#lt;b#amp;c#quot;" in diagram
    edge_labels = re.findall(r'\|"([^"]*)"\|', diagram)
    assert all('"' not in label for label in edge_labels)


def test_parallel_is_a_subgraph_with_its_branches_and_join():
    flow = FlowSpec(
        name="fan",
        nodes=[
            ParallelSpec(
                name="Fan",
                join="any",
                steps=[StepSpec(name="A", run="registry.a"), StepSpec(name="B", run="registry.b")],
                next="end",
            )
        ],
    )
    diagram = to_mermaid(flow)
    assert 'subgraph n1 ["Fan (join any, on branch error cancel)"]' in diagram
    assert '["A<br/>run: registry.a"]' in diagram and '["B<br/>run: registry.b"]' in diagram
    assert ("n1", "-->", "", "done") in _edges(diagram)


def test_foreach_and_max_visits_are_noted():
    step = StepSpec(
        name="Each", run="registry.x", foreach="context.items", max_visits=3, next="end"
    )
    diagram = to_mermaid(FlowSpec(name="f", nodes=[step]))
    assert "foreach: context.items" in diagram and "max_visits: 3" in diagram


def test_router_routes_and_fallback_chains():
    document = build((FIXTURES / "routers.skye").read_text(encoding="utf-8"))
    assert not document.diagnostics
    router = next(r for r in document.routers if len(r.routes) > 2)
    diagram = to_mermaid(router)
    assert diagram.startswith("flowchart LR\n")
    nodes = _nodes(diagram)
    for route in router.routes:
        assert any(
            label.startswith(f"route {route.alias}") for label in nodes.values()
        ), route.alias
    edges = _edges(diagram)
    for route in router.routes:
        here = next(
            n
            for n, label in nodes.items()
            if label.startswith(f"route {route.alias}<br/>") or label == f"route {route.alias}"
        )
        for order, _ in enumerate(route.fallback, start=1):
            assert any(e[0] == here and e[2] == f"fallback {order}" for e in edges)


def test_shorthand_fallback_targets_are_drawn():
    document = build(
        'router "r" { route "fast" = ["openai/gpt-4o-mini", "anthropic/claude-haiku"] }'
    )
    diagram = to_mermaid(document.routers[0])
    assert '["anthropic/claude-haiku"]' in diagram and '|"fallback 1"|' in diagram


def test_direction_can_be_chosen():
    assert to_mermaid(_flow(), direction="LR").startswith("flowchart LR\n")


def test_every_fixture_flow_and_router_renders():
    for path in sorted(FIXTURES.glob("*.skye")):
        document = build(path.read_text(encoding="utf-8"))
        for spec in [*document.flows, *document.routers]:
            diagram = to_mermaid(spec)
            assert diagram.count("\n") > 1 and '""' not in diagram, (path.name, spec.name)


def test_a_prompt_is_not_a_graph():
    document = build('prompt "p" { message "user" { text = "hi" } }')
    with pytest.raises(TypeError, match="not a graph"):
        to_mermaid(document.prompts[0])  # type: ignore[arg-type]
