"""Output schema from a dataclass or a JSON-schema dictionary (task 3.5; property 8)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

import pytest

from skye.base.exceptions import ValidationError
from skye.prompts import BasePromptBuilder


@pytest.fixture(scope="module")
def shared() -> BasePromptBuilder:
    return BasePromptBuilder()


@pytest.fixture
def builder(shared: BasePromptBuilder) -> BasePromptBuilder:
    return shared.partial()


@dataclass
class Address:
    city: str
    zip_code: str | None = None


@dataclass
class Person:
    name: str
    age: int
    score: float
    active: bool
    kind: Literal["employee", "contractor"]
    tags: list[str] = field(default_factory=list)
    address: Address | None = None
    nicknames: list[Address] = field(default_factory=list)


def test_dataclass_schema(builder: BasePromptBuilder) -> None:
    builder.set_output_schema("t", Person)
    schema = builder._schema_json["t"]
    props = schema["properties"]
    assert schema["required"] == ["name", "age", "score", "active", "kind"]
    assert props["name"] == {"type": "string"}
    assert props["age"] == {"type": "integer"}
    assert props["score"] == {"type": "number"}
    assert props["active"] == {"type": "boolean"}
    assert props["kind"] == {"enum": ["employee", "contractor"], "type": "string"}
    assert props["tags"] == {"type": "array", "items": {"type": "string"}}
    assert props["address"]["properties"]["city"] == {"type": "string"}
    assert props["nicknames"]["items"]["title"] == "Address"
    assert builder.get_template_metadata  # schema stays retrievable as given
    instructions = builder.get_output_instructions("t")
    assert json.dumps(schema) in instructions
    for path in ("name", "age", "kind", "tags", "address", "address.city", "nicknames[].city"):
        assert f"- {path} (" in instructions


def test_no_schema_no_instructions(builder: BasePromptBuilder) -> None:
    assert builder.get_output_instructions("nothing") == ""


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"title": "no type"},
        {"type": "thing"},
        {"type": "object", "properties": ["a"]},
        {"type": "object", "properties": {"a": "string"}},
        {"type": "object", "properties": {}, "required": "a"},
        "not a schema",
        int,
    ],
)
def test_invalid_schema_raises(builder: BasePromptBuilder, bad: object) -> None:
    with pytest.raises(ValidationError):
        builder.set_output_schema("t", bad)  # type: ignore[arg-type]
    assert builder.get_output_instructions("t") == ""


SCHEMAS = [
    {"type": "object", "properties": {"result": {"type": "string"}}},
    {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {"type": "object", "properties": {"text": {}, "label": {}}},
            },
            "meta": {"type": "object", "properties": {"source": {"type": "string"}}},
        },
        "required": ["entities"],
    },
    {"properties": {"a": {"type": ["string", "null"]}, "b": {"enum": [1, 2]}}},
    {"type": "string"},
]


def _all_fields(schema: dict, prefix: str = "") -> list[str]:
    out = []
    for name, sub in schema.get("properties", {}).items():
        out.append(prefix + name)
        out += _all_fields(sub, f"{prefix}{name}.")
        if isinstance(sub.get("items"), dict):
            out += _all_fields(sub["items"], f"{prefix}{name}[].")
    return out


@pytest.mark.parametrize("schema", SCHEMAS)
def test_property_8_instructions_name_every_field(builder: BasePromptBuilder, schema: dict) -> None:
    assert builder.get_output_instructions("t") == ""
    builder.set_output_schema("t", schema)
    instructions = builder.get_output_instructions("t")
    assert "JSON" in instructions and json.dumps(schema) in instructions
    for path in _all_fields(schema):
        assert f"- {path} (" in instructions
