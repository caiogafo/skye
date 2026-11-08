"""A prompt variable may carry a description: ``task = string "The goal"``."""

from __future__ import annotations

from skye.base.dsl import block_schema, build, check_text, to_text


def _prompt(variables: str) -> str:
    return (
        'prompt "p" {\n'
        f"  variables = {variables}\n"
        '  message "user" { text = "{{ task }}" }\n'
        "}\n"
    )


def test_descriptions_one_per_line() -> None:
    text = _prompt(
        "{\n"
        '    task = string "What the agent must achieve"\n'
        '    phase = string("plan") "plan, execute or replan"\n'
        "    steps = number(3)\n"
        "  }"
    )
    variables = build(text).raise_for_errors().prompt().variables
    assert [(v.name, v.required, v.default, v.description) for v in variables] == [
        ("task", True, None, "What the agent must achieve"),
        ("phase", False, "plan", "plan, execute or replan"),
        ("steps", False, 3, None),
    ]


def test_descriptions_in_the_comma_form() -> None:
    text = _prompt('{ task = string "x", tags = list([]) "y", n = number }')
    variables = build(text).raise_for_errors().prompt().variables
    assert [(v.name, v.description) for v in variables] == [
        ("task", "x"),
        ("tags", "y"),
        ("n", None),
    ]


def test_round_trip() -> None:
    text = _prompt('{ task = string "The goal", phase = string("plan") "The phase" }')
    spec = build(text).raise_for_errors().prompt()
    written = to_text(spec)
    assert '    task = string "The goal"\n' in written
    assert '    phase = string("plan") "The phase"\n' in written
    assert build(written).raise_for_errors().prompt() == spec


def test_without_descriptions_the_text_is_unchanged() -> None:
    spec = build(_prompt("{ task = string, n = number(1) }")).raise_for_errors().prompt()
    assert "variables = { task = string, n = number(1) }" in to_text(spec)


def test_the_block_schema_has_the_description() -> None:
    schema = block_schema("prompt")
    variable = schema["properties"]["variables"]["items"]["properties"]
    assert "description" in variable


def test_mistakes() -> None:
    (empty,) = check_text(_prompt('{ task = string "" }'))
    assert 'the description of "task" is empty' in empty.reason
    (inner,) = check_text(_prompt('{ task = string, m = map({ k = 1 "x" }) }'))
    assert '"k" is a key of a default value' in inner.reason
    assert check_text(_prompt('{ task = string "a" "b" }'))


def test_only_prompt_variables_take_a_description() -> None:
    flow = 'flow "f" {\n  context { a = string "x" }\n  step "s" { run = registry.x }\n}\n'
    assert check_text(flow)
    router = 'router {\n  route "fast" = "openai/gpt-4o-mini" "x"\n}\n'
    assert check_text(router)
    message = 'prompt "p" {\n  message "user" { text = "hi" "there" }\n}\n'
    assert check_text(message)
