"""Validation utilities for Skye.

This module provides utilities for validating interface compliance and
generating JSON schemas from Pydantic models.
"""

import inspect
from abc import ABC
from typing import Any

from pydantic import BaseModel

from skye.base.exceptions import ValidationError


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


def generate_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Generate JSON Schema from a Pydantic model.

    Converts a Pydantic model to JSON Schema format, which can be used for
    structured output validation or API documentation.

    Args:
        model: A Pydantic model class.

    Returns:
        JSON Schema dictionary representation of the model.

    Raises:
        ValidationError: If the provided type is not a Pydantic model.

    Example:
        >>> from skye.base.messages import UserMessage
        >>> schema = generate_schema(UserMessage)
        >>> schema['type']
        'object'
        >>> 'properties' in schema
        True
    """
    # Validate that the input is a Pydantic model
    if not (inspect.isclass(model) and issubclass(model, BaseModel)):
        raise ValidationError(
            f"Expected a Pydantic BaseModel class, got {type(model).__name__}",
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
