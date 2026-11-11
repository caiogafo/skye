"""Regression tests for the tools fixes found by the documentation review (tools spec, task 8).

Finding 19: one ``CapabilityInterface``/``CapabilitySchema`` pair, the base Port, from either path.
Finding 20: a failure in ``CapabilityRegistry.execute`` is a ``CapabilityExecutionError``.
Finding 21: ``@capability`` schemas follow nested types, ``Optional``, ``Union``, ``Literal`` and
``Args:``; the call arguments are never logged.
"""

import asyncio
import logging
from typing import Any, Literal, Optional, Union

import pytest

import skye.interfaces
import skye.tools
from skye.base.interfaces.capability import CapabilityInterface as PortInterface
from skye.base.interfaces.capability import CapabilitySchema as PortSchema
from skye.tools import (
    CapabilityExecutionError,
    CapabilityRegistry,
    CapabilitySchema,
    CapabilityValidationError,
    LocalFunctionCapability,
    capability,
)

# --- finding 19: one pair of types ---------------------------------------------------------------


def test_tools_reexports_the_base_port_types() -> None:
    assert skye.tools.CapabilitySchema is PortSchema
    assert skye.tools.CapabilityInterface is PortInterface
    assert skye.interfaces.CapabilitySchema is skye.tools.CapabilitySchema


class _PortCapability(skye.interfaces.CapabilityInterface):
    """A capability written only against the public Port (``skye.interfaces``)."""

    def get_schema(self) -> "skye.interfaces.CapabilitySchema":
        return skye.interfaces.CapabilitySchema(name="port_cap", description="Built from the Port")

    def execute(self, **kwargs: Any) -> Any:
        return "ok"

    async def aexecute(self, **kwargs: Any) -> Any:
        return "ok"


def test_registry_accepts_a_schema_built_from_skye_interfaces() -> None:
    registry = CapabilityRegistry()
    registry.register(_PortCapability())
    assert registry.exists("port_cap")


def test_list_schemas_returns_base_capability_schema() -> None:
    @capability
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    registry = CapabilityRegistry(capabilities=[add, _PortCapability()])
    schemas = asyncio.run(registry.list_schemas())
    assert [s.name for s in schemas] == ["add", "port_cap"]
    assert all(isinstance(s, PortSchema) for s in schemas)


def test_base_schema_keeps_the_tools_guarantees() -> None:
    schema = PortSchema(name="  name  ", description="  text  ")
    assert (schema.name, schema.description) == ("name", "text")
    with pytest.raises(Exception):
        schema.name = "other"  # type: ignore[misc]


# --- finding 20: execution failures are execution errors ---------------------------------------


class _Failing(PortInterface):
    def get_schema(self) -> PortSchema:
        return PortSchema(name="failing", description="Fails")

    def execute(self, **kwargs: Any) -> Any:
        raise ValueError("boom")

    async def aexecute(self, **kwargs: Any) -> Any:
        raise ValueError("boom")


def test_execute_failure_is_an_execution_error() -> None:
    registry = CapabilityRegistry(capabilities=[_Failing()])
    with pytest.raises(CapabilityExecutionError) as exc_info:
        registry.execute("failing", {})
    assert not isinstance(exc_info.value, CapabilityValidationError)
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_aexecute_failure_is_an_execution_error() -> None:
    registry = CapabilityRegistry(capabilities=[_Failing()])
    with pytest.raises(CapabilityExecutionError):
        asyncio.run(registry.aexecute("failing", {}))


def test_invalid_arguments_stay_a_validation_error() -> None:
    @capability
    def greet(name: str) -> str:
        """Greet someone."""
        return name

    registry = CapabilityRegistry(capabilities=[greet])
    with pytest.raises(CapabilityValidationError):
        registry.execute("greet", {})
    with pytest.raises(CapabilityValidationError):
        asyncio.run(registry.aexecute("greet", {}))


# --- finding 21: schema extraction ---------------------------------------------------------------


def _props(cap: Any) -> dict[str, Any]:
    return dict(cap.get_schema().parameters["properties"])


def test_nested_container_types() -> None:
    @capability
    def f(
        ids: list[int],
        nested: list[list[float]],
        scores: dict[str, int],
        pair: tuple[int, str],
        many: tuple[int, ...],
        tags: set[str],
    ) -> list[int]:
        """Nested types."""
        return ids

    props = _props(f)
    assert props["ids"] == {"type": "array", "items": {"type": "integer"}}
    assert props["nested"] == {
        "type": "array",
        "items": {"type": "array", "items": {"type": "number"}},
    }
    assert props["scores"] == {"type": "object", "additionalProperties": {"type": "integer"}}
    assert props["pair"] == {
        "type": "array",
        "prefixItems": [{"type": "integer"}, {"type": "string"}],
        "minItems": 2,
        "maxItems": 2,
    }
    assert props["many"] == {"type": "array", "items": {"type": "integer"}}
    assert props["tags"] == {"type": "array", "items": {"type": "string"}, "uniqueItems": True}
    assert f.get_schema().returns == {"type": "array", "items": {"type": "integer"}}


def test_optional_is_the_inner_type_and_not_required() -> None:
    @capability
    def f(a: int | None, b: Optional[str] = None, c: float | None = None) -> None:  # noqa: UP045
        """Optional types."""

    schema = f.get_schema().parameters
    assert schema["properties"]["a"] == {"type": "integer"}
    assert schema["properties"]["b"] == {"type": "string"}
    assert schema["properties"]["c"] == {"type": "number"}
    assert schema["required"] == []


def test_union_is_any_of() -> None:
    @capability
    def f(
        a: int | str,
        b: Union[int, list[str]],  # noqa: UP007
        c: int | str | None = None,
    ) -> None:
        """Union types."""

    props = _props(f)
    assert props["a"] == {"anyOf": [{"type": "integer"}, {"type": "string"}]}
    assert props["b"] == {
        "anyOf": [{"type": "integer"}, {"type": "array", "items": {"type": "string"}}]
    }
    assert props["c"] == {"anyOf": [{"type": "integer"}, {"type": "string"}]}


def test_literal_is_enum() -> None:
    @capability
    def f(unit: Literal["c", "f"], level: Literal[1, 2, 3]) -> None:
        """Literal types."""

    props = _props(f)
    assert props["unit"] == {"type": "string", "enum": ["c", "f"]}
    assert props["level"] == {"type": "integer", "enum": [1, 2, 3]}


def test_args_section_descriptions() -> None:
    @capability
    def get_weather(city: str, unit: str = "c", days: int = 1) -> str:
        """Get the weather for a city.

        Args:
            city: Name of the city, for example
                "Rome" or "Milan".
            unit (str): "c" or "f".
            days: How many days.

        Returns:
            The forecast.
        """
        return city

    props = _props(get_weather)
    assert props["city"]["description"] == 'Name of the city, for example "Rome" or "Milan".'
    assert props["unit"]["description"] == '"c" or "f".'
    assert props["days"] == {"type": "integer", "description": "How many days."}
    assert get_weather.get_schema().description == "Get the weather for a city."


def test_schema_override_errors_name_the_overridden_capability() -> None:
    def impl(x: int) -> int:
        return x

    override = CapabilitySchema(
        name="public_name",
        description="Overridden",
        parameters={"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]},
    )
    cap = LocalFunctionCapability(impl, schema_override=override)
    with pytest.raises(CapabilityValidationError) as exc_info:
        cap.execute()
    assert "public_name" in str(exc_info.value)
    assert "impl" not in str(exc_info.value)
    assert exc_info.value.details["capability_name"] == "public_name"


def test_local_function_does_not_log_arguments(caplog: pytest.LogCaptureFixture) -> None:
    secret = "mario.rossi@example.com"

    @capability
    def lookup(email: str) -> str:
        """Look up a user."""
        return "found"

    @capability
    def broken(email: str) -> str:
        """Always fails."""
        raise RuntimeError("nope")

    registry = CapabilityRegistry(capabilities=[lookup, broken])
    with caplog.at_level(logging.DEBUG):
        lookup.execute(email=secret)
        asyncio.run(lookup.aexecute(email=secret))
        registry.execute("lookup", {"email": secret})
        asyncio.run(registry.aexecute("lookup", {"email": secret}))
        with pytest.raises(RuntimeError):
            broken.execute(email=secret)
        with pytest.raises(RuntimeError):
            asyncio.run(broken.aexecute(email=secret))
    assert caplog.records
    for record in caplog.records:
        assert secret not in record.getMessage()
        assert secret not in repr(record.__dict__)
        assert not hasattr(record, "arguments")
    names = {getattr(r, "capability_name", None) for r in caplog.records}
    assert {"lookup", "broken"} <= names
