"""Structured prompt variables: the field syntax of ``output`` in ``variables``."""

from __future__ import annotations

import copy

import pytest

from skye.base.dsl import PromptSpec, block_schema, build, check_text, to_text
from skye.base.dsl.fmt import format_text
from skye.base.exceptions import ValidationError
from skye.prompts import describe_prompt, prompt_help, render_prompt

TEXT = """\
prompt "classify" {
  variables = {
    categories = list({
      name = string "Category name"
      description = string("") "What it means"
    }) "Categories to choose from"
    examples = list({ text = string, category = string, why = string("") }, []) "Worked examples"
    owner = map({ team = string, email = string("") }) "Who owns it"
    tags = list(string) "Free labels"
  }

  message "user" { text = "{{ categories | map('name') | join(', ') }}" }
}
"""


def _reasons(variables: str) -> list[str]:
    text = 'prompt "p" {\n  variables = { %s }\n  message "user" { text = "{{ v }}" }\n}\n'
    return [d.reason for d in check_text(text % variables)]


def _spec() -> PromptSpec:
    return build(TEXT).raise_for_errors().prompt()


def test_build() -> None:
    categories, examples, owner, tags = _spec().variables
    assert (categories.type, categories.item_type, categories.required) == ("list", "map", True)
    assert categories.description == "Categories to choose from"
    assert [(f.name, f.required, f.default, f.description) for f in categories.fields] == [
        ("name", True, None, "Category name"),
        ("description", False, "", "What it means"),
    ]
    assert (examples.required, examples.default) == (False, [])
    assert [f.name for f in examples.fields] == ["text", "category", "why"]
    assert (owner.type, owner.item_type, [f.name for f in owner.fields]) == (
        "map",
        None,
        ["team", "email"],
    )
    assert (tags.type, tags.item_type, tags.fields) == ("list", "string", [])
    assert all(v.structured for v in (categories, examples, owner, tags))


def test_shorthands_and_nesting() -> None:
    text = (
        'prompt "p" {\n  variables = { a = [string], b = { c = number, d = [{ e = bool }] },'
        " f = list({ g = list({ h = string }, []) }, []) }\n"
        '  message "user" { text = "{{ a }}{{ b }}{{ f }}" }\n}\n'
    )
    a, b, f = build(text).raise_for_errors().prompt().variables
    assert (a.type, a.item_type) == ("list", "string")
    assert b.type == "map" and b.fields[1].item_type == "map"
    assert b.fields[1].fields[0].name == "e"
    assert f.fields[0].default == [] and not f.fields[0].required


def test_plain_forms_keep_their_meaning() -> None:
    text = (
        'prompt "p" {\n  variables = { a = list([]), b = map({}), c = map({ k = 1 }), d = list,'
        ' e = list(["x"]) }\n  message "user" { text = "{{ a }}{{ b }}{{ c }}{{ d }}{{ e }}" }\n}\n'
    )
    variables = build(text).raise_for_errors().prompt().variables
    assert [(v.name, v.default, v.required, v.structured) for v in variables] == [
        ("a", [], False, False),
        ("b", {}, False, False),
        ("c", {"k": 1}, False, False),
        ("d", None, True, False),
        ("e", ["x"], False, False),
    ]


def test_round_trip_and_fmt() -> None:
    spec = _spec()
    written = to_text(spec)
    assert build(written).raise_for_errors().prompt() == spec
    assert 'list({ text = string, category = string, why = string("") }, [])' in written
    assert format_text(TEXT) == TEXT


def test_block_schema() -> None:
    variable = block_schema("prompt")["properties"]["variables"]["items"]["properties"]
    assert {"item_type", "fields", "description"} <= set(variable)


def test_mistakes() -> None:
    assert _reasons("v = list({ a = strin })")[0].startswith('unknown type "strin"')
    assert (
        "does not match its shape: v[0]: expected map, got int"
        in _reasons("v = list({ a = string }, [1])")[0]
    )
    assert "v.a: missing" in _reasons("v = map({ a = string }, {})")[0]
    assert "takes one argument" in _reasons('v = string("a", "b")')[0]
    assert "takes one argument" in _reasons("v = list([], [])")[0]
    flow = (
        'flow "f" {\n  context { a = list({ x = string }, []) }\n'
        '  step "s" { run = registry.x, next = "end" }\n}\n'
    )
    assert any("takes one argument" in d.reason for d in check_text(flow))


def test_render_fills_defaults_in_a_copy() -> None:
    categories = [{"name": "a"}, {"name": "b", "description": "B", "extra": 1}]
    given = {"categories": categories, "owner": {"team": "t"}, "tags": ["x"]}
    before = copy.deepcopy(given)
    (message,) = render_prompt(_spec(), given)
    assert message.content == "a, b"
    assert given == before


def test_render_checks_the_shape() -> None:
    bad = {
        "categories": [{"name": "a"}, {}],
        "examples": [{"text": 3, "category": "c"}, 5],
        "owner": {"team": 1},
        "tags": "x",
    }
    with pytest.raises(ValidationError) as caught:
        render_prompt(_spec(), bad)
    assert caught.value.details["value"] == [
        "categories[1].name: missing",
        "examples[0].text: expected string, got int",
        "examples[1]: expected map, got int",
        "owner.team: expected string, got int",
        "tags: expected list, got str",
    ]


def test_number_and_bool() -> None:
    text = (
        'prompt "p" {\n  variables = { v = list({ n = number, b = bool(false) }) }\n'
        '  message "user" { text = "{{ v }}" }\n}\n'
    )
    spec = build(text).raise_for_errors().prompt()
    render_prompt(spec, {"v": [{"n": 1}, {"n": 2.5, "b": True}]})
    with pytest.raises(ValidationError, match=r"v\[0\]\.n: expected number, got bool"):
        render_prompt(spec, {"v": [{"n": True}]})
    with pytest.raises(ValidationError, match=r"v\[0\]\.b: expected bool, got int"):
        render_prompt(spec, {"v": [{"n": 1, "b": 1}]})


def test_help_shows_the_fields() -> None:
    text = prompt_help(_spec())
    assert text.startswith(
        "classify\n\nInputs\n"
        "  categories     list of map     required  Categories to choose from\n"
        "    name         string          required  Category name\n"
        '    description  string          = ""      What it means\n'
        "  examples       list of map     = []      Worked examples\n"
    )
    info = describe_prompt(_spec())
    assert info.inputs[3].item_type == "string"
    assert [f.name for f in info.inputs[2].fields] == ["team", "email"]
