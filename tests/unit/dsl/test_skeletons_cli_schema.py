"""Skeletons, the ``skye`` command line (check, new), the JSON Schema and the block models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skye.base.dsl import (
    TEMPLATES,
    SkyeSyntaxError,
    block_schema,
    build,
    check_text,
    new_flow,
    new_prompt,
    new_router,
    parse_duration,
    skeleton,
)
from skye.base.dsl.specs import STRATEGIES
from skye.utils.cli import main

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "skye"
ALL = [(k, t) for k, ts in TEMPLATES.items() for t in ts]


# -- skeletons ---------------------------------------------------------------------------------


@pytest.mark.parametrize("kind,template", ALL)
def test_every_skeleton_passes_check(kind: str, template: str) -> None:
    text = skeleton(kind, None, template)
    assert check_text(text, f"{kind}-{template}.skye") == []
    assert "CHANGE ME" in text
    doc = build(text)
    assert doc.routers or doc.flows or doc.prompts


@pytest.mark.parametrize("kind,template", ALL)
def test_no_skeleton_uses_version_2_syntax(kind: str, template: str) -> None:
    text = skeleton(kind, "x", template)
    assert "wait" not in text and "on_event" not in text


@pytest.mark.parametrize("kind,template", ALL)
def test_every_skeleton_starts_with_front_matter(kind: str, template: str) -> None:
    text = skeleton(kind, "my.name-1", template)
    assert text.startswith('---\ntitle       = "my.name-1"\n')
    meta = build(text).metadata
    assert meta["title"] == "my.name-1"
    assert meta["description"].startswith("CHANGE ME: ")
    assert meta["version"] == "0.1.0" and meta["tags"] == []
    assert "__NAME__" not in text and "__DESCRIPTION__" not in text


def test_named_helpers_and_defaults() -> None:
    assert 'router "main"' in new_router()
    assert 'flow "my_flow"' in new_flow()
    assert 'prompt "my_prompt"' in new_prompt()
    assert 'flow "other"' in new_flow("other", "loop")
    assert 'prompt "p"' in new_prompt("p", "chat")
    assert 'router "r"' in new_router("r", "full")


def test_the_skeleton_name_reaches_the_model() -> None:
    assert build(new_flow("billing", "branch")).flow("billing").start == "Classify"


def test_skeleton_rejects_unknown_kind_template_and_name() -> None:
    with pytest.raises(ValueError, match="unknown kind"):
        skeleton("agent")
    with pytest.raises(ValueError, match="unknown template"):
        skeleton("flow", None, "wait")
    with pytest.raises(ValueError, match="not a valid name"):
        skeleton("flow", 'x" { }')


def test_skeletons_check_against_the_registry_names_they_show() -> None:
    names = ["my_fetch_step", "my_summary_step"]
    assert check_text(new_flow(), registry_names=names) == []
    assert check_text(new_flow(), registry_names=["other"])  # the example names are CHANGE ME


# -- command line ------------------------------------------------------------------------------


def test_check_ok_and_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = tmp_path / "good.skye"
    good.write_text(new_flow(), encoding="utf-8")
    bad = tmp_path / "bad.skye"
    bad.write_text('flow "f" {\n  step "A" {\n    run = planner\n  }\n}\n', encoding="utf-8")
    assert main(["check", str(good)]) == 0
    assert f"{good}: ok" in capsys.readouterr().out
    assert main(["check", str(good), str(bad)]) == 1
    out = capsys.readouterr().out
    assert f"{bad}:3:11 " in out and "has no prefix" in out
    assert f'{bad}:2:3 step "A" has no next. Add: next = "<step>" or next = end' in out


def test_check_registry_option(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    file = tmp_path / "f.skye"
    file.write_text('flow "f" { step "A" { run = registry.x, next = end } }\n', encoding="utf-8")
    assert main(["check", str(file)]) == 0
    assert main(["check", "--registry", "x,y", str(file)]) == 0
    assert main(["check", "--registry", "y", str(file)]) == 1
    assert "is not in the registry" in capsys.readouterr().out


def test_check_syntax_error_and_missing_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    file = tmp_path / "s.skye"
    file.write_text('flow "f" {\n', encoding="utf-8")
    assert main(["check", str(file)]) == 1
    assert "never closed" in capsys.readouterr().out
    assert main(["check", str(tmp_path / "missing.skye")]) == 2
    assert "cannot read" in capsys.readouterr().err
    assert main(["check"]) == 2


def test_check_the_reference_fixtures(capsys: pytest.CaptureFixture[str]) -> None:
    files = sorted(str(p) for p in FIXTURES.glob("*.skye"))
    assert main(["check", *files]) == 0
    assert main(["check", str(FIXTURES / "v2" / "f6.skye")]) == 1
    assert "not available in this version" in capsys.readouterr().out


def test_check_schema_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "--schema"]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert set(schema["$defs"]) == {"router", "flow", "prompt"}


def test_new_prints_to_stdout_and_lists(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["new", "flow", "demo", "--template", "loop"]) == 0
    out = capsys.readouterr().out
    assert out == skeleton("flow", "demo", "loop")
    assert main(["new", "--list"]) == 0
    listing = capsys.readouterr().out
    for kind, templates in TEMPLATES.items():
        assert kind in listing and all(t in listing for t in templates)


def test_new_writes_a_file_and_refuses_to_overwrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "r.skye"
    assert main(["new", "router", "main", "-o", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == new_router("main")
    capsys.readouterr()
    target.write_text("keep me", encoding="utf-8")
    assert main(["new", "router", "main", "-o", str(target)]) == 2
    assert "already exists" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == "keep me"
    assert main(["new", "router", "main", "-o", str(target), "--force"]) == 0
    assert target.read_text(encoding="utf-8") == new_router("main")
    assert main(["check", str(target)]) == 0


def test_new_errors(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["new", "flow", "x", "--template", "nope"]) == 2
    assert "unknown template" in capsys.readouterr().err
    assert main(["new"]) == 2
    with pytest.raises(SystemExit):
        main(["new", "agent"])


# -- schema and models -------------------------------------------------------------------------


def test_block_schema_matches_the_models() -> None:
    router = block_schema("router")
    assert router["title"] == "RouterSpec"
    assert {"strategy", "cooldown", "routes", "retry_policies"} <= set(router["properties"])
    assert router["properties"]["strategy"]["anyOf"][0] == {"enum": list(STRATEGIES)}
    flow = block_schema("flow")
    assert flow["required"] == ["name"] and "nodes" in flow["properties"]
    prompt = block_schema("prompt")
    assert {"variables", "allow_missing", "parts"} <= set(prompt["properties"])
    assert "line" not in json.dumps(flow["properties"]["nodes"])
    json.dumps(block_schema())
    with pytest.raises(ValueError):
        block_schema("agent")


def test_strategies_match_the_router_enum() -> None:
    from skye.base.interfaces.router import RoutingStrategy

    assert set(STRATEGIES) == {s.value for s in RoutingStrategy}


def test_router_field_names_match_today_configuration() -> None:
    import dataclasses

    from skye.base.dsl import TargetSpec
    from skye.router.config_models import ModelTarget

    today = {f.name for f in dataclasses.fields(ModelTarget) if f.init}
    mine = {f.name for f in dataclasses.fields(TargetSpec)}
    assert mine == today


def test_parse_duration() -> None:
    assert parse_duration("30s") == 30
    assert parse_duration("5m") == 300
    assert parse_duration("24h") == 86400
    with pytest.raises(ValueError):
        parse_duration("30")


def test_document_helpers_and_raise() -> None:
    doc = build((FIXTURES / "f9.skye").read_text(encoding="utf-8"))
    assert doc.ok and doc.flow().name == "research" and doc.router().name == "main"
    with pytest.raises(KeyError):
        doc.flow("nope")
    bad = build('flow "f" { step "A" { run = x } }', filename="b.skye")
    with pytest.raises(SkyeSyntaxError) as info:
        bad.raise_for_errors()
    assert info.value.file == "b.skye"


def test_flow_model_content() -> None:
    flow = build((FIXTURES / "flows.skye").read_text(encoding="utf-8")).flow("write_and_review")
    write = flow.node("Write")
    assert write.max_visits == 4 and write.next == "Review"
    decide = flow.node("Decide")
    assert decide.otherwise.set[0].name == "revisions" and decide.otherwise.next == "Write"
    assert [f.name for f in flow.context.fields] == ["brief", "revisions", "quality"]
    search = build((FIXTURES / "flows.skye").read_text(encoding="utf-8")).flow("call_with_care")
    assert search.node("Search").retry.max == 3 and search.node("Search").timeout == "30s"


def test_prompt_model_content() -> None:
    chat = build((FIXTURES / "prompts.skye").read_text(encoding="utf-8")).prompt("chat")
    assert [p.kind for p in chat.parts] == ["message", "each", "message"]
    assert chat.parts[1].children[0].role_from.text == "turn.role"
    summarize = build((FIXTURES / "prompts.skye").read_text(encoding="utf-8")).prompt("summarize")
    assert summarize.allow_missing == ["style"]
    assert [v.required for v in summarize.variables] == [True, False, False]
