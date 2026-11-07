"""``to_text``: block models written back as ``.skye`` text, and the round trip with ``build``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from skye.base.dsl import (
    ContextFieldSpec,
    Expression,
    FlowSpec,
    RouterSpec,
    RouteSpec,
    StepSpec,
    TargetSpec,
    build,
    check_text,
    format_duration,
    parse_duration,
    to_text,
)
from skye.base.dsl.emit import quote, value
from skye.base.validated import dump

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "skye"
FILES = sorted(FIXTURES.glob("*.skye"))


def _plain(spec: Any) -> Any:
    """A spec as plain data, without the positions in the file."""

    def strip(item: Any) -> Any:
        if isinstance(item, dict):
            return {k: strip(v) for k, v in item.items() if k not in ("line", "column")}
        if isinstance(item, list):
            return [strip(i) for i in item]
        return item

    return strip(dump(spec))


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_fixture_survives_the_round_trip(path: Path) -> None:
    document = build(path.read_text(encoding="utf-8"), filename=path.name)
    assert document.ok, [d.message for d in document.diagnostics]
    text = to_text(document)
    again = build(text, filename="emitted.skye")
    assert again.ok, ([d.message for d in again.diagnostics], text)
    for kind in ("routers", "flows", "prompts"):
        assert [_plain(s) for s in getattr(again, kind)] == [
            _plain(s) for s in getattr(document, kind)
        ], kind
    assert to_text(again) == text  # writing is stable: the same text comes back


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_the_emitted_text_passes_the_checker(path: Path) -> None:
    document = build(path.read_text(encoding="utf-8"), filename=path.name)
    assert check_text(to_text(document), "emitted.skye") == []


def test_one_spec_alone_is_written_when_it_needs_no_other_block() -> None:
    document = build(
        'flow "f" {\n  step "A" { run = registry.a, next = end }\n}\n', filename="f.skye"
    )
    text = to_text(document.flows[0])
    assert text.startswith('flow "f" {') and check_text(text) == []


def test_a_flow_that_runs_another_block_needs_it_in_the_same_text() -> None:
    document = build(
        'flow "inner" { step "X" { run = registry.x, next = end } }\n'
        'flow "outer" { step "A" { run = flow.inner, next = end } }\n',
        filename="f.skye",
    )
    assert check_text(to_text(document.flows[1])) != []  # inner is missing
    assert check_text(to_text(*document.flows)) == []


def test_defaults_are_left_out() -> None:
    text = to_text(RouterSpec(routes=[]))
    assert text == "router {\n}\n"
    flow = build('flow "f" { step "A" { run = registry.a, next = end } }', filename="f.skye").flows[
        0
    ]
    out = to_text(flow)
    assert "join" not in out and "max_visits" not in out


def test_strings_are_escaped_so_that_they_read_back_the_same() -> None:
    awkward = 'say "hi"\n\tand a \\ backslash'
    assert quote(awkward) == '"say \\"hi\\"\\n\\tand a \\\\ backslash"'
    router = RouterSpec(
        routes=[
            RouteSpec(
                alias="x",
                targets=[
                    TargetSpec(
                        model="m", provider="p", metadata={"note": awkward, "key with space": 1}
                    )
                ],
            )
        ]
    )
    again = build(to_text(router), filename="r.skye")
    assert again.ok
    assert again.routers[0].routes[0].targets[0].metadata == {"note": awkward, "key with space": 1}


def test_value_writes_each_kind() -> None:
    assert value(True) == "true" and value(False) == "false"
    assert value(3) == "3" and value(0.5) == "0.5"
    assert value("a") == '"a"' and value(["a", 1]) == '["a", 1]'
    assert value({"k": "v"}) == '{ k = "v" }' and value({}) == "{}"
    assert value(Expression(text="context.a + 1")) == "context.a + 1"
    assert value("${KEY}") == '"${KEY}"' and value("${KEY}", env=True) == "env.KEY"
    assert value("pre-${KEY}", env=True) == '"pre-${KEY}"'
    with pytest.raises(ValueError):
        value(object())


def test_to_text_refuses_what_is_not_a_block_model() -> None:
    with pytest.raises(TypeError):
        to_text("router {}")  # type: ignore[arg-type]


def test_format_duration_is_the_opposite_of_parse_duration() -> None:
    for seconds in (0, 1, 30, 59, 60, 90, 300, 3600, 5400, 86400, 172800, 1.5, 0.25):
        assert parse_duration(format_duration(seconds)) == seconds
    assert [format_duration(s) for s in (30, 60, 300, 3600, 86400, 90, 1.5)] == [
        "30s",
        "1m",
        "5m",
        "1h",
        "1d",
        "90s",
        "1.5s",
    ]
    with pytest.raises(ValueError):
        format_duration(-1)


def test_a_hand_built_step_is_written_in_the_style_of_the_examples() -> None:
    flow = FlowSpec(
        name="f",
        nodes=[
            StepSpec(
                name="A", run="registry.a", input={"text": Expression(text="context.t")}, next="end"
            )
        ],
    )
    flow.context.fields.append(ContextFieldSpec(name="t", type="string"))
    text = to_text(flow)
    assert 'step "A" { run = registry.a, input = { text = context.t }, next = end }' in text
    assert check_text(text) == []
