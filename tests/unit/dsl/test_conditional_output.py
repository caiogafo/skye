"""Conditional output blocks (D70): an ``output`` inside a top-level ``when`` of a prompt."""

from __future__ import annotations

import pytest

from skye.base.dsl import OutputFieldSpec, OutputSpec, block_schema, build, check_text, to_text
from skye.base.exceptions import ValidationError
from skye.prompts import active_output, describe_prompt, output_instructions, prompt_help

VARIABLES = 'schema = map({}), format = string("json"), fmt = string("json"), flag = bool(false)'

CONDITIONAL = """
  when schema     { output format { schema = schema } }
  when not schema {
    output format {
      name  = string  "What the extracted item is"
      value = string  "Its value, as written in the input"
    }
  }"""


def _prompt(body: str, variables: str = VARIABLES) -> str:
    return (
        f'prompt "p" {{\n  variables = {{ {variables} }}\n'
        f'  message "user" {{ text = "hi" }}\n{body}\n}}\n'
    )


def _messages(body: str) -> list[str]:
    return [d.message for d in check_text(_prompt(body))]


def test_conditional_outputs_build() -> None:
    doc = build(_prompt(CONDITIONAL))
    assert doc.diagnostics == []
    spec = doc.prompt()
    assert spec.output is None
    variants = spec.output_variants()
    assert [[c.text for c in conditions] for conditions, _ in variants] == [
        ["schema"],
        ["not schema"],
    ]
    assert variants[0][1] == OutputSpec(format_from="format", schema_from="schema")
    assert variants[1][1] == OutputSpec(
        format_from="format",
        fields=[
            OutputFieldSpec(name="name", type="string", description="What the extracted item is"),
            OutputFieldSpec(
                name="value", type="string", description="Its value, as written in the input"
            ),
        ],
    )


def test_nested_when_is_allowed() -> None:
    body = '  when flag {\n    when schema { output "xml" { schema = schema } }\n  }'
    spec = build(_prompt(body)).prompt()
    ((conditions, output),) = spec.output_variants()
    assert [c.text for c in conditions] == ["flag", "schema"]
    assert output.format == "xml"
    assert active_output(spec, {"flag": True, "schema": {"a": "string"}}) == output
    assert active_output(spec, {"flag": False, "schema": {"a": "string"}}) is None


def test_output_in_a_message_or_each_is_an_error() -> None:
    (message,) = _messages('  message "user" { when flag { output { a = string } } }')
    assert message.startswith("an output block belongs to the prompt, not to a message.")
    (message,) = _messages("  each x in [1] { output { a = string } }")
    assert message.startswith("an output block cannot be inside an each block.")
    (message,) = _messages("  each x in [1] { when flag { output { a = string } } }")
    assert message.startswith("an output block cannot be inside an each block.")


def test_unconditional_and_conditional_is_an_error() -> None:
    body = "  output { a = string }\n  when flag { output { b = string } }"
    (message,) = _messages(body)
    assert "has an output block on line 4 and one inside a when block on line 5" in message
    assert "not both" in message


def test_every_check_applies_to_a_conditional_output() -> None:
    assert _messages('  when flag { output "yaml" { a = string } }')[0].startswith(
        'output format "yaml" is not known.'
    )
    assert _messages('  when flag { output "table" { a = list } }')[0].startswith(
        'output "table": column "a" is a list'
    )
    assert _messages("  when flag { output { a = strng } }")[0].startswith('unknown type "strng"')
    assert _messages("  when flag { output { schema = format } }")[0].startswith(
        '"schema" needs a map variable; "format" is string.'
    )
    assert _messages("  when flag { output nope { a = string } }")[0].startswith(
        'variable "nope" is not declared'
    )
    assert _messages('  when flag { output { a = string "" } }')
    (message,) = _messages("  when flag { output { schema = schema, extra = string } }")
    assert message.startswith('"schema" gives all the fields of the output block')


def test_round_trip() -> None:
    spec = build(_prompt(CONDITIONAL)).prompt()
    text = to_text(spec)
    assert "  when schema {\n    output format { schema = schema }\n  }" in text
    assert '      name = string "What the extracted item is"' in text
    again = build(text)
    assert again.diagnostics == []
    assert to_text(again.prompt()) == text
    assert [o for _, o in again.prompt().output_variants()] == [
        o for _, o in spec.output_variants()
    ]


def test_the_block_schema_has_the_output_part() -> None:
    parts = str(block_schema("prompt")["properties"]["parts"])
    assert "'output'" in parts and "schema_from" in parts


def test_active_output_at_render_time() -> None:
    spec = build(_prompt(CONDITIONAL)).prompt()
    default = active_output(spec, {})
    assert default is not None and [f.name for f in default.fields] == ["name", "value"]
    given = active_output(spec, {"schema": {"total": "number"}})
    assert given is not None and given.schema_from == "schema"
    text = output_instructions(spec, {"schema": {"total": "number"}})
    assert '"total"' in text and '"value"' not in text
    assert '"value"' in output_instructions(spec, {})


def test_no_active_output_gives_no_instructions() -> None:
    spec = build(_prompt("  when flag { output { a = string } }")).prompt()
    assert active_output(spec, {}) is None
    assert output_instructions(spec, {}) == ""
    assert output_instructions(spec, {"flag": True}).strip()


def test_two_active_outputs_are_an_error() -> None:
    body = "  when flag { output { a = string } }\n  when schema { output { b = string } }"
    spec = build(_prompt(body)).prompt()
    assert active_output(spec, {"flag": True}) is not None
    with pytest.raises(ValidationError, match=r"2 output blocks are active at once") as caught:
        output_instructions(spec, {"flag": True, "schema": {"x": "string"}})
    assert "when flag; when schema" in str(caught.value)


def test_help_shows_each_variant_with_its_condition() -> None:
    spec = build(_prompt(CONDITIONAL)).prompt()
    info = describe_prompt(spec)
    assert info.output is None
    assert [o.condition for o in info.outputs] == ["schema", "not schema"]
    assert info.outputs[0].fields_from == "schema"
    text = prompt_help(info)
    assert "Output (when schema): from variable format\n  fields from variable schema" in text
    assert "Output (when not schema): from variable format\n  name " in text
    assert "free text" not in text
