"""A rendered prompt as provider-agnostic parts (task 9.6, Requirement 33.9, decisions D81, D101).

``render_parts`` returns a :class:`PromptParts`: the system text apart from the messages, the
JSON Schema of the ``output`` block as an :class:`OutputSchema` and the output instructions as
``fallback_text``, which are not also appended to the messages.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from skye.base.exceptions import ValidationError
from skye.base.messages import AssistantMessage, UserMessage
from skye.base.prompt_parts import OutputSchema, PromptParts
from skye.prompts import (
    BasePromptBuilder,
    load_prompt,
    output_instructions,
    output_json_schema,
    render_parts,
    render_prompt,
)

TEXT = """prompt "Product List" {
  variables = {
    catalogue = string          "Catalogue text"
    format    = string("json")  "json, table or xml"
  }
  output format {
    name  = string "Product name"
    price = number "Unit price"
  }
  message "system" { text = "You read catalogues." }
  placeholder "history"
  message "user" { text = "List the products:\\n{{ catalogue }}" }
}
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Product name"},
        "price": {"type": "number", "description": "Unit price"},
    },
    "required": ["name", "price"],
}


def _shape(parts: PromptParts) -> tuple[object, ...]:
    """The parts without the message ids and timestamps."""
    messages = [(m.role, m.content) for m in parts.messages]
    return (parts.system, messages, parts.output, parts.fallback_text)


@pytest.fixture(scope="module")
def spec():  # type: ignore[no-untyped-def]
    return load_prompt(TEXT)


def test_json_output_gives_a_schema_and_the_instructions_as_fallback(spec) -> None:  # type: ignore[no-untyped-def]
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]
    parts = render_parts(spec, {"catalogue": "Lamp 24.90"}, history={"history": history})
    assert isinstance(parts, PromptParts)
    assert parts.system == "You read catalogues."
    assert [(m.role, m.content) for m in parts.messages] == [
        ("user", "Hi"),
        ("assistant", "Hello"),
        ("user", "List the products:\nLamp 24.90"),
    ]
    assert isinstance(parts.messages[1], AssistantMessage)
    assert parts.output == OutputSchema(name="Product_List", schema=SCHEMA)
    assert parts.fallback_text == output_instructions(spec, {"catalogue": "x"})
    # the instructions are not also in the messages
    assert all("JSON Schema" not in m.content for m in parts.messages)
    rendered = render_prompt(spec, {"catalogue": "Lamp 24.90"})
    assert rendered[-1].content.endswith(parts.fallback_text)


def test_table_and_xml_have_no_schema_only_the_text(spec) -> None:  # type: ignore[no-untyped-def]
    for fmt in ("table", "xml"):
        parts = render_parts(spec, {"catalogue": "x", "format": fmt})
        assert parts.output is None
        assert parts.fallback_text == output_instructions(spec, {"catalogue": "x", "format": fmt})


def test_a_prompt_without_output_or_system_gives_none() -> None:
    spec = load_prompt('prompt "p" {\n  message "user" { text = "Hi" }\n}\n')
    parts = render_parts(spec, {})
    assert _shape(parts) == (None, [("user", "Hi")], None, None)
    assert isinstance(parts.messages[0], UserMessage)


def test_output_json_schema_is_the_schema_of_the_active_output(spec) -> None:  # type: ignore[no-untyped-def]
    assert output_json_schema(spec, {"catalogue": "x"}) == SCHEMA
    assert (
        output_json_schema(load_prompt('prompt "p" {\n  message "user" { text = "Hi" }\n}\n'))
        is None
    )


def test_errors_are_the_ones_of_render_prompt(spec) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValidationError, match="catalogue"):
        render_parts(spec, {})


# -- the builder --------------------------------------------------------------------------------


@dataclass
class Invoice:
    number: str
    total: float


def test_the_builder_gives_parts_for_a_skye_prompt(spec) -> None:  # type: ignore[no-untyped-def]
    builder = BasePromptBuilder()
    builder.register_template("products", TEXT)
    parts = builder.render_parts("products", {"catalogue": "Lamp"})
    expected = render_parts(spec, {"catalogue": "Lamp"})
    assert parts.output == OutputSchema(name="products", schema=SCHEMA)
    assert _shape(parts)[:2] == _shape(expected)[:2]
    assert parts.fallback_text == expected.fallback_text


def test_the_builder_gives_parts_for_a_text_template_with_a_schema() -> None:
    builder = BasePromptBuilder()
    builder.register_template("inv", "[SYSTEM]\nBe exact.\n[USER]\nRead: {{ text }}")
    builder.set_output_schema("inv", Invoice)
    parts = builder.render_parts("inv", {"text": "INV-1 10.0"})
    assert parts.system == "Be exact."
    assert [(m.role, m.content) for m in parts.messages] == [("user", "Read: INV-1 10.0")]
    assert parts.output is not None and parts.output.name == "inv"
    assert parts.output.schema["required"] == ["number", "total"]
    assert parts.fallback_text == builder.get_output_instructions("inv")


def test_the_builder_without_schema_and_with_a_table_format() -> None:
    builder = BasePromptBuilder()
    builder.register_template("t", "Hi {{ name }}")
    assert _shape(builder.render_parts("t", {"name": "Ada"})) == (
        None,
        [("user", "Hi Ada")],
        None,
        None,
    )
    builder.set_output_schema("t", Invoice, output_format="table")
    parts = builder.render_parts("t", {"name": "Ada"})
    assert parts.output is None and parts.fallback_text == builder.get_output_instructions("t")


def test_the_port_has_a_default_render_parts_from_render() -> None:
    from skye.base.interfaces.prompt import PromptRenderingInterface

    assert "render_parts" not in PromptRenderingInterface.__abstractmethods__

    class Minimal(BasePromptBuilder):
        render_parts = PromptRenderingInterface.render_parts  # the Port's default

    builder = Minimal()
    builder.register_template("t", "[SYSTEM]\nA\n[USER]\nHi {{ name }}\n[SYSTEM]\nB")
    assert _shape(builder.render_parts("t", {"name": "Ada"})) == (
        "A\n\nB",
        [("user", "Hi Ada")],
        None,
        None,
    )
