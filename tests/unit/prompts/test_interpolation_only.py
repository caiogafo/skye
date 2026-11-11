"""Text templates do interpolation only (task 9.1, decision D76, Requirement 30.8).

``{{ }}`` with its filters stays; a ``{% %}`` control tag is rejected with an error that names the
tag and its line and points to ``when`` and ``each`` of a ``.skye`` prompt.
"""

from __future__ import annotations

import pytest

import skye.prompts.engine as engine
from skye.base.exceptions import ValidationError
from skye.prompts import BasePromptBuilder
from skye.prompts.engine import TemplateSyntaxError, compile_template, render_template


@pytest.mark.parametrize(
    "tag",
    [
        "{% if x %}",
        "{% for x in xs %}",
        "{% endif %}",
        "{% else %}",
        "{%- if x -%}",
        "{% macro m() %}",
        "{% set a = 1 %}",
    ],
)
def test_the_engine_rejects_every_control_tag(tag: str) -> None:
    with pytest.raises(TemplateSyntaxError) as info:
        compile_template(f"first\n{tag}x")
    message = str(info.value)
    assert tag in message
    assert "line 2" in message
    assert "when" in message and "each" in message
    assert info.value.line == 2


def test_the_engine_keeps_interpolation_filters_and_comments() -> None:
    assert render_template('{{ xs | join(", ") }}', {"xs": ["a", "b"]}) == "a, b"
    assert render_template('{{ v | default("d") }}', {}) == "d"
    assert render_template("{{ d | tojson }}", {"d": {"a": 1}}) == '{"a": 1}'
    assert render_template('{{ a if a else "fallback" }}', {"a": ""}) == "fallback"
    assert render_template("a{# note #}b", {}) == "ab"
    assert render_template("a  {{- x -}}  b", {"x": "X"}) == "aXb"


def test_every_name_read_by_interpolation_is_required_unless_defaulted() -> None:
    compiled = compile_template('{{ a }} {{ b | default("z") }} {{ c.x }} {{ a }}')
    assert compiled.variables == ("a", "b", "c")
    assert compiled.required_variables == ("a", "c")


def test_the_engine_has_no_tag_machinery_left() -> None:
    source = engine.__doc__ or ""
    assert "{% if %}" not in source and "endfor" not in source
    assert not hasattr(engine, "_TemplateParser") or not hasattr(
        engine._TemplateParser, "parse_for"
    )


def test_the_builder_names_the_template_the_line_and_the_tag() -> None:
    builder = BasePromptBuilder()
    with pytest.raises(ValidationError) as info:
        builder.register_template("greet", "Hello {{ name }}\n{% if vip %}Welcome back{% endif %}")
    message = info.value.message
    assert "'greet'" in message
    assert "line 2" in message and "{% if vip %}" in message
    assert "when" in message and "each" in message
    assert info.value.details["line"] == 2
    with pytest.raises(KeyError):
        builder.get_template("greet")


def test_a_text_with_only_a_tag_is_rejected_too() -> None:
    with pytest.raises(ValidationError, match=r"line 1"):
        BasePromptBuilder().register_template("t", "{% for x in xs %}{% endfor %}")


def test_validate_template_reports_the_tag_without_raising() -> None:
    builder = BasePromptBuilder()
    builder.register_template("t", "{{ a }}")
    builder._templates["t:1.0"] = "{% if a %}x{% endif %}"
    result = builder.validate_template("t")
    assert result["valid"] is False
    assert "when" in result["errors"][0]


def test_a_variable_read_by_interpolation_is_required() -> None:
    builder = BasePromptBuilder()
    builder.register_template("t", "{{ zeta }} {{ alpha }} {{ beta | default('-') }}")
    with pytest.raises(ValueError, match=r"Missing required variables: alpha, zeta"):
        builder.render("t", {})
    assert builder.render("t", {"zeta": "z", "alpha": "a"})[0].content == "z a -"
    meta = builder.get_template_metadata("t")
    assert meta["variables"] == ["zeta", "alpha"]
    assert meta["optional_variables"] == ["beta"]
