"""Conformance suite of the ``.skye`` parser (task 8.1 of 0-base-uxui, 10.7 of 0-base-base).

Every version 1 example of the reference set (fixtures under ``tests/fixtures/skye``) must parse and
validate, every version 2 example must be rejected with the "not available in this version"
message, and every row of the error table must give the stated message with file, line and column.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skye.base.dsl import SkyeSyntaxError, build, check_text, parse

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "skye"
V1 = sorted(p for p in FIXTURES.glob("*.skye"))
V2 = sorted(p for p in (FIXTURES / "v2").glob("*.skye"))


@pytest.mark.parametrize("path", V1, ids=lambda p: p.name)
def test_version_1_example_parses_and_validates(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    parse(text, path.name)
    doc = build(text, filename=path.name)
    assert doc.diagnostics == []
    assert doc.routers or doc.flows or doc.prompts


def test_the_reference_set_is_complete() -> None:
    routers = build((FIXTURES / "routers.skye").read_text(encoding="utf-8"))
    assert [r.name for r in routers.routers] == ["r1", "r2", "r3", "main"]
    prompts = build((FIXTURES / "prompts.skye").read_text(encoding="utf-8"))
    assert [p.name for p in prompts.prompts] == ["chat", "summarize", "support_chat"]
    flows = build((FIXTURES / "flows.skye").read_text(encoding="utf-8"))
    assert [f.name for f in flows.flows] == [
        "summarize_url",
        "triage",
        "gather",
        "write_and_review",
        "call_with_care",
        "ingest",
    ]
    assert build((FIXTURES / "f7.skye").read_text(encoding="utf-8")).flow("report").name == "report"
    assert build((FIXTURES / "f9.skye").read_text(encoding="utf-8")).flow().start == "Plan"


@pytest.mark.parametrize("path", V2, ids=lambda p: p.name)
def test_version_2_example_is_rejected(path: Path) -> None:
    diagnostics = check_text(path.read_text(encoding="utf-8"), path.name)
    assert diagnostics
    assert any("is not available in this version" in d.message for d in diagnostics)
    assert all(d.file == path.name and d.line > 0 and d.column > 0 for d in diagnostics)


def test_wait_message_is_the_stated_one() -> None:
    text = (FIXTURES / "v2" / "f6.skye").read_text(encoding="utf-8")
    messages = [d.message for d in check_text(text)]
    assert '"wait" needs persistence and is not available in this version' in messages
    assert len(messages) == 4  # wait and three on_event, nothing else


def test_router_values_of_the_full_example() -> None:
    router = build((FIXTURES / "routers.skye").read_text(encoding="utf-8")).router("r3")
    assert router.cooldown == "60s" and router.strategy == "rate_limit_aware"
    azure = next(r for r in router.routes if r.alias == "azure-gpt4")
    assert azure.fallback == ["gpt-4", "gpt-3.5-turbo"] and len(azure.targets) == 2
    assert azure.targets[0].api_key == "${AZURE_OPENAI_API_KEY_EAST}"
    assert azure.targets[0].timeout == "30s" and azure.targets[0].max_retries == 2
    assert router.retry_policies[0].retry_after == "5s"
    assert router.allowed_fails_policies[0].allowed_fails_per_minute == 100


def test_shorthand_route() -> None:
    doc = build((FIXTURES / "routers.skye").read_text(encoding="utf-8"))
    fast = doc.router("r1").routes[0]
    assert (fast.alias, fast.targets[0].provider, fast.targets[0].model) == (
        "fast",
        "openai",
        "gpt-4o-mini",
    )
    assert [t.model for t in fast.fallback_targets] == ["claude-haiku"]
    mixed = doc.router("r2").routes[0]
    assert mixed.targets[0].rpm == 60 and mixed.targets[0].api_key == "${OPENAI_API_KEY}"


# (name, source, registry names, line, column, message, exact)
CASES = [
    (
        "unknown step",
        'flow "f" {\n  step "A" {\n    run  = registry.a\n    next = "Wirte"\n'
        '    on_error = "Write"\n  }\n'
        '  step "Write" { run = registry.w, next = end }\n}\n',
        None,
        4,
        12,
        'unknown step "Wirte" in "next". Defined steps: A, Write. Did you mean "Write"?',
        True,
    ),
    (
        "no next",
        'flow "f" {\n  step "Fetch" {\n    run = registry.fetch\n  }\n}\n',
        None,
        2,
        3,
        'step "Fetch" has no next. Add: next = "<step>" or next = end',
        True,
    ),
    (
        "choice without else",
        'flow "f" {\n  context { x = number(0) }\n'
        '  step "A" { run = registry.a, next = "Decide" }\n'
        '  choice "Decide" {\n    when context.x > 1 { next = end }\n  }\n}\n',
        None,
        4,
        3,
        'choice "Decide" has no else. Add: else { next = "<step>" }',
        True,
    ),
    (
        "loop without bound",
        'flow "f" {\n  context { x = number(0) }\n  step "Write" {\n    run  = registry.w\n'
        '    next = "Decide"\n  }\n  choice "Decide" {\n    when context.x > 1 { next = end }\n'
        '    else { next = "Write" }\n  }\n}\n',
        None,
        3,
        3,
        'step "Write" can be entered again (Decide -> Write) but has no max_visits. Add: '
        "max_visits = 4",
        True,
    ),
    (
        "not in the registry",
        'flow "f" {\n  step "Plan" {\n    run  = registry.plannr\n    next = end\n  }\n}\n',
        ["planner", "web_search"],
        3,
        12,
        'step "Plan": "plannr" is not in the registry. Known: planner, web_search.',
        False,
    ),
    (
        "no prefix",
        'flow "f" {\n  step "Plan" {\n    run  = planner\n    next = end\n  }\n}\n',
        None,
        3,
        12,
        '"planner" has no prefix. Use registry.planner, flow.planner or router.planner',
        True,
    ),
    (
        "undeclared context field",
        'flow "f" {\n  context { topic = string, quality = number(0) }\n  step "A" {\n'
        "    run   = registry.a\n    input = { q = context.qualty }\n    next  = end\n  }\n}\n",
        None,
        5,
        19,
        '"context.qualty" is not declared. Declared: topic, quality.',
        False,
    ),
    (
        "unreachable step",
        'flow "f" {\n  step "A" { run = registry.a, next = end }\n'
        '  step "Orphan" { run = registry.o, next = end }\n}\n',
        None,
        3,
        3,
        'step "Orphan" can not be reached from the start',
        True,
    ),
    (
        "wait in version 1",
        'flow "f" {\n  step "A" {\n    wait = ["x"]\n    next = end\n  }\n}\n',
        None,
        3,
        5,
        '"wait" needs persistence and is not available in this version',
        True,
    ),
    (
        "wrong type in set",
        'flow "f" {\n  context { quality = number(0) }\n  step "A" {\n    run = registry.a\n'
        '    set quality = "high"\n    next = end\n  }\n}\n',
        None,
        5,
        9,
        '"quality" is number, the value is a string',
        True,
    ),
    (
        "call outside the list",
        'flow "f" {\n  context { x = number(0) }\n  step "A" {\n    run = registry.a\n'
        '    set x = open("f")\n    next = end\n  }\n}\n',
        None,
        5,
        13,
        'call "open(...)" is not allowed in an expression. '
        "Allowed: len, min, max, abs, round, str, int, float",
        True,
    ),
    (
        "typo in a field",
        'flow "f" {\n  step "Search" {\n    run    = registry.s\n    timout = "30s"\n'
        "    next   = end\n  }\n}\n",
        None,
        4,
        5,
        'unknown field "timout" in step "Search". Did you mean "timeout"?',
        True,
    ),
    (
        "bare number as a duration",
        'flow "f" {\n  step "A" {\n    run     = registry.a\n    timeout = 30\n'
        "    next    = end\n  }\n}\n",
        None,
        4,
        15,
        'timeout = 30 is not a duration. Use "30s", "5m" or "24h"',
        True,
    ),
    (
        "invalid prompt role",
        'prompt "p" {\n  message "bot" { text = "hi" }\n}\n',
        None,
        2,
        11,
        'role "bot" is not valid. Use system, user or assistant',
        True,
    ),
    (
        "old unit name",
        "router {\n  cooldown_seconds = 60\n}\n",
        None,
        2,
        3,
        '"cooldown_seconds" was renamed "cooldown" and takes a duration such as "60s"',
        True,
    ),
    (
        "fallback to a missing route",
        'router {\n  route "claude" { target { model = "m", provider = "p" } }\n  route "gpt" {\n'
        '    fallback = ["claud"]\n    target { model = "m", provider = "p" }\n  }\n}\n',
        None,
        4,
        17,
        'route "gpt" has no route "claud" in fallback. Did you mean "claude"?',
        True,
    ),
]


@pytest.mark.parametrize(
    "source,registry,line,column,message,exact",
    [c[1:] for c in CASES],
    ids=[c[0] for c in CASES],
)
def test_error_table_row(
    source: str, registry: list[str] | None, line: int, column: int, message: str, exact: bool
) -> None:
    diagnostics = check_text(source, "app.skye", registry)
    assert len(diagnostics) == 1, [d.format() for d in diagnostics]
    found = diagnostics[0]
    assert (found.file, found.line, found.column) == ("app.skye", line, column)
    if exact:
        assert found.message == message
    else:
        assert found.message.startswith(message)
        assert "Did you mean" in found.message
    assert found.format().startswith(f"app.skye:{line}:{column} ")


def test_all_errors_are_reported_together() -> None:
    source = (
        'flow "f" {\n  step "A" {\n    run = planner\n  }\n'
        '  step "B" {\n    run = registry.b\n    timout = "1s"\n    next = "Z"\n  }\n}\n'
    )
    messages = [d.message for d in check_text(source)]
    assert len(messages) >= 4
    assert any("has no prefix" in m for m in messages)
    assert any("has no next" in m for m in messages)
    assert any("unknown field" in m for m in messages)
    assert any("unknown step" in m for m in messages)


def test_syntax_errors_are_collected_and_raised_together() -> None:
    source = 'flow "f" {\n  step "A" { next = }\n  step "B" { run = [1 2] }\n  = 3\n}\n'
    with pytest.raises(SkyeSyntaxError) as info:
        parse(source, "bad.skye")
    error = info.value
    assert len(error.diagnostics) >= 2
    assert error.file == "bad.skye" and error.line == 2
    assert "bad.skye:2:" in str(error)


def test_unterminated_string_and_unclosed_block() -> None:
    assert check_text('flow "f {\n}\n')[0].reason == "unterminated string"
    unclosed = check_text('flow "f" {\n  step "A" {\n')
    assert any("never closed" in d.reason for d in unclosed)


def test_registry_is_checked_only_when_names_are_given() -> None:
    text = 'flow "f" { step "A" { run = registry.anything, next = end } }'
    assert check_text(text) == []
    assert check_text(text, registry_names=["anything"]) == []
    assert len(check_text(text, registry_names=["other"])) == 1


def test_flow_that_contains_itself_is_rejected() -> None:
    text = 'flow "a" { step "S" { run = flow.a, next = end } }'
    assert any("contains itself" in d.message for d in check_text(text))
