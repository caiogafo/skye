"""Tests for the standard-library prompt template engine (no Jinja2)."""

import ast
from pathlib import Path

import pytest

import skye.prompts.engine as engine
from skye.prompts.engine import TemplateSyntaxError, render_template


def test_variables_and_attributes() -> None:
    assert render_template("Hi {{ user.name }} {{ items[1] }}", {"user": {"name": "Al"}, "items": [1, 2]}) == "Hi Al 2"


def test_undefined_left_visible_and_falsy() -> None:
    assert render_template("{{ nope }}", {}) == "{{ nope }}"
    assert render_template("{% if nope %}x{% else %}y{% endif %}", {}) == "y"


def test_if_elif_else() -> None:
    t = '{% if k == "a" %}A{% elif k == "b" %}B{% else %}Z{% endif %}'
    assert [render_template(t, {"k": v}) for v in "abc"] == ["A", "B", "Z"]


def test_for_loop_helpers_and_dict_items() -> None:
    t = "{% for x in xs %}{{ loop.index }}={{ x }}{% if not loop.last %},{% endif %}{% endfor %}"
    assert render_template(t, {"xs": ["a", "b"]}) == "1=a,2=b"
    assert render_template("{% for k, v in d.items() %}{{ k }}:{{ v }};{% endfor %}", {"d": {"a": 1}}) == "a:1;"
    assert render_template("{% for x in xs %}{{ x }}{% else %}none{% endfor %}", {"xs": []}) == "none"


def test_filters_and_inline_if() -> None:
    assert render_template('{{ xs | join(", ") }}', {"xs": ["a", "b"]}) == "a, b"
    assert render_template('{{ v | default("d") }}', {}) == "d"
    assert render_template("{{ r | upper }}", {"r": "user"}) == "USER"
    assert render_template('{{ a if a else "fallback" }}', {"a": ""}) == "fallback"


def test_custom_filter() -> None:
    assert render_template("{{ x | twice }}", {"x": "ab"}, {"twice": lambda v: v * 2}) == "abab"


def test_whitespace_control() -> None:
    assert render_template("a\n{% if x %}\nb\n{% endif %}\nc", {"x": True}) == "a\nb\nc"
    assert render_template("a  {%- if x -%}  b{% endif %}", {"x": True}) == "ab"


def test_comments_dropped() -> None:
    assert render_template("a{# note #}b", {}) == "ab"


def test_syntax_errors() -> None:
    with pytest.raises(TemplateSyntaxError):
        render_template("{% if x %}no end", {})
    with pytest.raises(TemplateSyntaxError):
        render_template("{{ x | nofilter }}", {"x": 1})
    with pytest.raises(TemplateSyntaxError):
        render_template("{% macro m() %}", {})


def test_no_jinja_imports_in_prompts_package() -> None:
    for path in Path(engine.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else (
                [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            )
            assert all(not n.startswith("jinja2") for n in names), path
