"""Tests for the standard-library prompt template engine (no Jinja2; interpolation only, D76)."""

import ast
from pathlib import Path

import pytest

import skye.prompts.engine as engine
from skye.prompts.engine import TemplateSyntaxError, render_template


def test_variables_and_attributes() -> None:
    assert (
        render_template(
            "Hi {{ user.name }} {{ items[1] }}", {"user": {"name": "Al"}, "items": [1, 2]}
        )
        == "Hi Al 2"
    )


def test_undefined_left_visible_and_falsy() -> None:
    assert render_template("{{ nope }}", {}) == "{{ nope }}"
    assert render_template('{{ "x" if nope else "y" }}', {}) == "y"


def test_inline_conditions_and_comparisons() -> None:
    t = '{{ "A" if k == "a" else ("B" if k == "b" else "Z") }}'
    assert [render_template(t, {"k": v}) for v in "abc"] == ["A", "B", "Z"]
    assert render_template("{{ 'yes' if 'a' in xs else 'no' }}", {"xs": ["a"]}) == "yes"


def test_method_calls_and_map() -> None:
    assert render_template("{{ d.items() | list | length }}", {"d": {"a": 1, "b": 2}}) == "2"
    xs = [{"name": "a"}, {"name": "b"}]
    assert render_template("{{ xs | map('name') | join(',') }}", {"xs": xs}) == "a,b"


def test_filters_and_inline_if() -> None:
    assert render_template('{{ xs | join(", ") }}', {"xs": ["a", "b"]}) == "a, b"
    assert render_template('{{ v | default("d") }}', {}) == "d"
    assert render_template("{{ r | upper }}", {"r": "user"}) == "USER"
    assert render_template('{{ a if a else "fallback" }}', {"a": ""}) == "fallback"


def test_custom_filter() -> None:
    assert render_template("{{ x | twice }}", {"x": "ab"}, {"twice": lambda v: v * 2}) == "abab"


def test_whitespace_control() -> None:
    assert render_template("a  {{- x -}}  b", {"x": "X"}) == "aXb"
    assert render_template("a\n  {# note #}\nb", {}) == "a\nb"


def test_comments_dropped() -> None:
    assert render_template("a{# note #}b", {}) == "ab"


def test_syntax_errors() -> None:
    with pytest.raises(TemplateSyntaxError, match="when"):
        render_template("{% if x %}no end", {})
    with pytest.raises(TemplateSyntaxError):
        render_template("{{ x | nofilter }}", {"x": 1})
    with pytest.raises(TemplateSyntaxError):
        render_template("{% macro m() %}", {})
    with pytest.raises(TemplateSyntaxError):
        render_template("{{ x + }}", {"x": 1})


def test_no_jinja_imports_in_prompts_package() -> None:
    for path in Path(engine.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            )
            assert all(not n.startswith("jinja2") for n in names), path


def test_compile_template_lists_free_names_in_first_seen_order() -> None:
    compiled = engine.compile_template(
        "{{ b }} {{ a | upper if c.x else '' }} {{ items | map('name') | join }} {{ b }}"
        "{{ True }} {{ 'lit' }} {{ d['k'] }}"
    )
    assert compiled.variables == ("b", "a", "c", "items", "d")


def test_required_variables_are_the_ones_not_read_through_default() -> None:
    compiled = engine.compile_template('{{ a }} {{ b | default("z") }} {{ c if d else e }}')
    assert compiled.variables == ("a", "b", "c", "d", "e")
    assert compiled.required_variables == ("a", "c", "d", "e")


def test_compiled_template_renders_like_render_template() -> None:
    source = "{{ xs | length }}:{{ xs | join | twice }}"
    filters = {"twice": lambda v: v * 2}
    compiled = engine.compile_template(source)
    for xs in (["a"], ["a", "b"], []):
        assert compiled.render({"xs": xs}, filters) == render_template(source, {"xs": xs}, filters)


def test_compile_template_raises_syntax_error() -> None:
    with pytest.raises(TemplateSyntaxError):
        engine.compile_template("{% for x %}")
