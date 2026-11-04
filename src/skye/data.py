"""Validated dataclasses: `@validated`, `Validated`, `field` (public path of `skye.base.validated`).

The code lives in `skye.base.validated`; import from here (or from `skye` for the commonest names).
"""

from skye.base.validated import (
    Validated,
    dump,
    field,
    from_mapping,
    json_schema,
    validate_instance,
    validated,
)

__all__ = [
    "Validated",
    "dump",
    "field",
    "from_mapping",
    "json_schema",
    "validate_instance",
    "validated",
]
