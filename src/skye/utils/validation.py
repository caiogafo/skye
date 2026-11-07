"""Validation utilities for Skye.

This module provides utilities for validating interface compliance and
generating JSON schemas from dataclasses and Pydantic models.
"""

import dataclasses
import inspect
from abc import ABC
from typing import Any, TypeVar

from pydantic import BaseModel

from skye.base.exceptions import ValidationError
from skye.base.validated import json_schema


def validate_interface_compliance(implementation: Any, interface: type[ABC]) -> None:
    """Validate that an implementation complies with an interface.

    Checks that all abstract methods defined in the interface are implemented
    in the provided implementation class.

    Args:
        implementation: The implementation instance or class to validate.
        interface: The abstract interface class to validate against.

    Raises:
        ValidationError: If the implementation doesn't comply with the interface.

    Example:
        >>> from skye.base.interfaces import ModelInterface
        >>> class MyModel(ModelInterface):
        ...     def complete(self, request):
        ...         return None
        ...     # Missing other required methods
        >>> validate_interface_compliance(MyModel(), ModelInterface)
        ValidationError: Implementation missing required methods: stream, acomplete, ...
    """
    # Get the implementation class if an instance was passed
    impl_class = implementation if inspect.isclass(implementation) else type(implementation)

    # Check if the implementation is a subclass of the interface
    if not issubclass(impl_class, interface):
        raise ValidationError(
            f"Implementation {impl_class.__name__} does not inherit from {interface.__name__}",
            field="interface_inheritance",
            value=impl_class.__name__,
            interface=interface.__name__,
        )

    # Get all abstract methods from the interface
    abstract_methods = set()
    for name, method in inspect.getmembers(interface, predicate=inspect.isfunction):
        if getattr(method, "__isabstractmethod__", False):
            abstract_methods.add(name)

    # Check which abstract methods are not implemented
    missing_methods = []
    for method_name in abstract_methods:
        impl_method = getattr(impl_class, method_name, None)
        if impl_method is None or getattr(impl_method, "__isabstractmethod__", False):
            missing_methods.append(method_name)

    if missing_methods:
        raise ValidationError(
            f"Implementation {impl_class.__name__} missing required methods: "
            f"{', '.join(sorted(missing_methods))}",
            field="abstract_methods",
            value=missing_methods,
            interface=interface.__name__,
            implementation=impl_class.__name__,
        )


def _shape(func: Any) -> tuple[list[tuple[str, str, bool]], str, str | None]:
    """The comparable shape of a method: parameters (name, kind), form, and return annotation by name."""
    func = inspect.unwrap(getattr(func, "__func__", func))
    params = [
        (p.name, p.kind.name, p.default is not inspect.Parameter.empty)
        for p in inspect.signature(func).parameters.values()
        if p.name not in ("self", "cls")
    ]
    if inspect.isasyncgenfunction(func):
        form = "async generator"
    elif inspect.iscoroutinefunction(func):
        form = "async def"
    else:
        form = "def"
    ret = inspect.signature(func).return_annotation
    if ret is inspect.Signature.empty or isinstance(ret, TypeVar):
        name = None
    elif isinstance(ret, str):
        name = ret.replace("typing.", "").split("[")[0].split(".")[-1].strip()
    else:
        name = getattr(ret, "__name__", None) or str(ret).replace("typing.", "").split("[")[0]
    if name:
        name = " ".join(part for part in name.replace("|", " | ").split() if part not in ("|", "None")) or name
        name = name.split(".")[-1]
    return params, form, name


def port_methods(port: type) -> list[str]:
    """The public methods of a Port, an abstract base or a ``Protocol``."""
    return sorted(
        name
        for name, member in vars(port).items()
        if not name.startswith("_") and inspect.isfunction(getattr(member, "__func__", member))
    ) + sorted(
        name
        for base in port.__mro__[1:-1]
        if base is not object and getattr(base, "__module__", "").startswith("skye.")
        for name, member in vars(base).items()
        if not name.startswith("_") and inspect.isfunction(member) and name not in vars(port)
    )


def port_signature_mismatches(implementation: Any, port: type) -> list[str]:
    """Compare an implementation with a Port by signature; return one line per difference (empty when it conforms).

    For every public method of the Port: the parameter names and kinds in order (``self`` and ``cls`` ignored; the implementation may add trailing
    parameters that have a default), the form (``def``, ``async def``, async generator) and the return annotation by name when both sides have one (an implementation may return its own class where the
    Port returns a Port it implements: a covariant return).
    A method the implementation adds is allowed; a method it omits, a parameter it renames or a ``def`` it makes ``async def``
    is not. Works for abstract bases and for ``Protocol`` Ports.
    """
    impl_class = implementation if inspect.isclass(implementation) else type(implementation)
    problems: list[str] = []
    for name in port_methods(port):
        impl_method = getattr(impl_class, name, None)
        if impl_method is None or not callable(impl_method):
            problems.append(f"{name}: missing")
            continue
        if getattr(impl_method, "__isabstractmethod__", False):
            problems.append(f"{name}: still abstract")
            continue
        want_params, want_form, want_ret = _shape(getattr(port, name))
        have_params, have_form, have_ret = _shape(impl_method)
        want_keys = [p[:2] for p in want_params]
        if [p[:2] for p in have_params[: len(want_params)]] != want_keys or any(
            not (p[2] or p[1].startswith("VAR")) for p in have_params[len(want_params) :]
        ):
            problems.append(f"{name}: parameters {[p[:2] for p in have_params]} != Port {want_keys}")
        if want_form != have_form:
            problems.append(f"{name}: form {have_form} != Port {want_form}")
        covariant = have_ret == impl_class.__name__ and any(base.__name__ == want_ret for base in impl_class.__mro__)
        if want_ret and have_ret and "Any" not in (want_ret, have_ret) and want_ret != have_ret and not covariant:
            problems.append(f"{name}: returns {have_ret} != Port {want_ret}")
    return problems


def validate_port_signatures(implementation: Any, port: type) -> None:
    """Raise ``ValidationError`` when an implementation differs from a Port by signature (see ``port_signature_mismatches``)."""
    problems = port_signature_mismatches(implementation, port)
    if problems:
        impl_class = implementation if inspect.isclass(implementation) else type(implementation)
        raise ValidationError(
            f"Implementation {impl_class.__name__} does not match {port.__name__}: " + "; ".join(problems),
            field="port_signature",
            value=problems,
            interface=port.__name__,
            implementation=impl_class.__name__,
        )


def generate_schema(model: type) -> dict[str, Any]:
    """Generate JSON Schema from a dataclass or a Pydantic model.

    Converts a model class to JSON Schema format, which can be used for
    structured output validation or API documentation. The library's own models are
    dataclasses; a Pydantic model (a user's structured-output class) is accepted too.

    Args:
        model: A dataclass or a Pydantic model class.

    Returns:
        JSON Schema dictionary representation of the model.

    Raises:
        ValidationError: If the provided type is neither a dataclass nor a Pydantic model.

    Example:
        >>> from skye.base.messages import UserMessage
        >>> schema = generate_schema(UserMessage)
        >>> schema['type']
        'object'
        >>> 'properties' in schema
        True
    """
    if inspect.isclass(model) and dataclasses.is_dataclass(model):
        return json_schema(model)

    # Validate that the input is a Pydantic model
    if not (inspect.isclass(model) and issubclass(model, BaseModel)):
        raise ValidationError(
            f"Expected a dataclass or a Pydantic BaseModel class, got {type(model).__name__}",
            field="model_type",
            value=str(model),
        )

    # Generate JSON Schema using Pydantic's built-in method
    try:
        schema = model.model_json_schema()
        return schema
    except Exception as e:
        raise ValidationError(
            f"Failed to generate schema for {model.__name__}: {str(e)}",
            field="schema_generation",
            value=model.__name__,
            error=str(e),
        )
