"""Check a value against a declared shape: the fields of an ``output`` block or of a structured
prompt variable (``list({ name = string, description = string("") })``).

:func:`conform` returns a copy of the value in which every missing optional field holds its
default, and the list of mistakes, each starting with the path of the value
(``categories[1].name: missing``, ``examples[0].text: expected string, got int``). The value
given is never changed. Keys that the shape does not declare are kept.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

_SCALARS = {"string": "string", "number": "number", "bool": "bool"}


def conform(
    kind: str,
    item_type: str | None,
    fields: Sequence[Any],
    value: Any,
    path: str,
    errors: list[str],
) -> Any:
    """The value checked against a shape, with the defaults of the missing optional fields.

    Args:
        kind: ``string``, ``number``, ``bool``, ``list`` or ``map``.
        item_type: The type of the items of a list (``None``: any).
        fields: The fields (``OutputFieldSpec``) of a map, or of the items of a list of maps.
        value: The value to check (not changed).
        path: Where the value is, for the messages (``categories``).
        errors: The mistakes found are appended here.

    Returns:
        A copy of the value with the defaults filled in (the value itself where it has a mistake).
    """
    if kind == "list":
        if isinstance(value, str | bytes) or not isinstance(value, Sequence):
            errors.append(f"{path}: expected list, got {_name(value)}")
            return value
        if item_type is None:
            return list(value)
        return [
            conform(item_type, None, fields, item, f"{path}[{index}]", errors)
            for index, item in enumerate(value)
        ]
    if kind == "map":
        if not isinstance(value, Mapping):
            errors.append(f"{path}: expected map, got {_name(value)}")
            return value
        out = dict(value)
        for item in fields:
            where = f"{path}.{item.name}"
            given = value.get(item.name)
            if given is None:
                if item.required:
                    errors.append(f"{where}: missing")
                else:
                    out[item.name] = copy.deepcopy(item.default)
                continue
            out[item.name] = conform(item.type, item.item_type, item.fields, given, where, errors)
        return out
    if kind == "string" and not isinstance(value, str):
        errors.append(f"{path}: expected string, got {_name(value)}")
    elif kind == "number" and (isinstance(value, bool) or not isinstance(value, int | float)):
        errors.append(f"{path}: expected number, got {_name(value)}")
    elif kind == "bool" and not isinstance(value, bool):
        errors.append(f"{path}: expected bool, got {_name(value)}")
    return value


def _name(value: Any) -> str:
    return "none" if value is None else type(value).__name__
