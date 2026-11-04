"""Structured output: the schema a model is asked to follow, and the check of its reply (Requirement 27, D24).

``response_schema`` is a dataclass (the standard, ``@validated`` or plain ``@dataclass``). A class with
``model_json_schema`` and ``model_validate_json`` (a user's pydantic model) is accepted too, without the library importing pydantic.
A reply that does not conform raises ``ValidationError`` naming the field.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping
from typing import Any

from skye.base.exceptions import ValidationError
from skye.base.validated import from_mapping, json_schema, validate_instance


STRUCTURED_TOOL = "skye_structured_output"
"""Name of the tool that carries a structured answer on providers without a native mode (Requirement 27.1: function calling)."""


def schema_instruction(cls: Any) -> str:
    """A sentence that asks for a JSON reply following the schema of ``cls`` (for providers with only a JSON mode)."""
    return "Reply only with a JSON object that follows this JSON Schema: " + json.dumps(schema_of(cls), separators=(",", ":"))


def schema_of(cls: Any) -> dict[str, Any]:
    """The JSON Schema of a declared output class (a dataclass, or a class with ``model_json_schema``)."""
    if hasattr(cls, "model_json_schema"):
        schema: dict[str, Any] = cls.model_json_schema()
        return schema
    if isinstance(cls, type) and dataclasses.is_dataclass(cls):
        return json_schema(cls)
    raise ValidationError(
        f"response_schema must be a dataclass, got {cls!r}", field="response_schema", value=cls
    )


def strict_schema(schema: dict[str, Any]) -> dict[str, Any] | None:
    """The schema in the form a provider's strict mode accepts, or ``None`` when it cannot be used strictly.

    Strict mode needs every object to list all its properties as required and to forbid additional ones. Only a schema that
    already meets the first condition is returned (with the second added); otherwise the provider is asked in non-strict mode.
    """
    def convert(node: Any) -> Any:
        if isinstance(node, dict):
            out = {key: convert(value) for key, value in node.items()}
            if "properties" in out:
                if set(out.get("required", [])) != set(out["properties"]):
                    raise _NotStrict
                out["additionalProperties"] = False
            return out
        if isinstance(node, list):
            return [convert(item) for item in node]
        return node

    try:
        converted: dict[str, Any] = convert(schema)
    except _NotStrict:
        return None
    return converted


class _NotStrict(Exception):
    pass


def parse_structured(cls: Any, text: str) -> Any:
    """Read the JSON ``text`` of a reply as ``cls``; raises ``ValidationError`` naming the field when it does not conform."""
    name = getattr(cls, "__name__", str(cls))
    try:
        if hasattr(cls, "model_validate_json"):
            return cls.model_validate_json(text)
        data = json.loads(text)
        if not isinstance(data, Mapping):
            raise ValidationError(f"The response is not a JSON object for {name}", field="<root>", value=text)
        if not (isinstance(cls, type) and dataclasses.is_dataclass(cls)):
            raise ValidationError(f"response_schema must be a dataclass, got {cls!r}", field="response_schema", value=cls)
        missing = [
            f.name
            for f in dataclasses.fields(cls)
            if f.init
            and f.default is dataclasses.MISSING
            and f.default_factory is dataclasses.MISSING
            and f.name not in data
        ]
        if missing:
            raise ValidationError(f"The response lacks the field {missing[0]!r} of {name}", field=missing[0], value=text)
        instance = from_mapping(cls, data)
        validate_instance(instance)
        return instance
    except ValidationError:
        raise  # it already names the field
    except Exception as e:  # json errors, or a pydantic ValidationError
        errors = e.errors() if hasattr(e, "errors") else []
        field = ".".join(str(part) for part in errors[0]["loc"]) if errors and errors[0].get("loc") else "response_schema"
        raise ValidationError(f"The response does not conform to {name}: {e}", field=field, value=text) from e


__all__ = ["STRUCTURED_TOOL", "schema_instruction", "schema_of", "strict_schema", "parse_structured"]
