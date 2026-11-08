"""Prompt loops (D69): `loop.*` inside `each`, an `each` over a map gives `{key, value}` entries, the `map` filter."""

from __future__ import annotations

import pytest

from skye.base.dsl import check_text
from skye.prompts import load_prompt, render_prompt
from skye.prompts.engine import render_template

LOOPS = """
prompt "p" {
  variables = { data = map({}), xs = list([]) }
  message "user" {
    each entry in data { text = "{{ loop.index }}. {{ entry.key }} = {{ entry.value }}" }
    each x in xs {
      text = "{{ loop.index0 }}/{{ loop.length }} {{ x }}"
      when loop.first { text = "first" }
      when loop.last  { text = "last" }
    }
  }
}
"""


def _content(**variables: object) -> str:
    return render_prompt(load_prompt(LOOPS), variables)[0].content


def test_loop_variables_inside_each() -> None:
    assert _content(xs=["a", "b", "c"]) == "0/3 a\nfirst\n1/3 b\n2/3 c\nlast"


def test_an_each_over_a_map_gives_key_value_entries_in_order() -> None:
    assert _content(data={"name": "Ada", "age": 36}) == "1. name = Ada\n2. age = 36"


def test_nested_each_has_its_own_loop() -> None:
    text = """
prompt "n" {
  variables = { rows = list([]) }
  message "user" {
    each row in rows { each cell in row { text = "{{ loop.index }}:{{ cell }}" } }
  }
}
"""
    assert (
        render_prompt(load_prompt(text), {"rows": [["a", "b"], ["c"]]})[0].content
        == "1:a\n2:b\n1:c"
    )


def test_the_caller_data_is_not_changed() -> None:
    data = {"k": "v"}
    _content(data=data)
    assert data == {"k": "v"}


def test_loop_is_known_to_the_checker_only_inside_each() -> None:
    assert not check_text(LOOPS)
    outside = 'prompt "q" {\n  message "user" { text = "{{ loop.index }}" }\n}\n'
    problems = check_text(outside)
    assert problems and any("loop" in p.message for p in problems)


def test_map_filter_plucks_an_attribute_of_maps_and_objects() -> None:
    class Tool:
        def __init__(self, name: str) -> None:
            self.name = name

    tools = [{"name": "search"}, Tool("calc")]
    assert (
        render_template("{{ tools | map('name') | join(', ') }}", {"tools": tools})
        == "search, calc"
    )


@pytest.mark.parametrize(
    "tools, expected", [([], ""), ([{"name": "a"}], "a"), ([{"name": "a"}, {"name": "b"}], "a, b")]
)
def test_map_filter_keeps_a_list_on_one_line(tools: list[dict[str, str]], expected: str) -> None:
    text = 'prompt "t" {\n  variables = { tools = list([]) }\n  message "user" { text = "Tools: {{ tools | map(\'name\') | join(\', \') }}" }\n}\n'
    assert render_prompt(load_prompt(text), {"tools": tools})[0].content == f"Tools: {expected}"
