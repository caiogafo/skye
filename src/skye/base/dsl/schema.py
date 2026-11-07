"""The JSON Schema of the ``router``, ``flow`` and ``prompt`` blocks.

Generated from the block models with :func:`skye.base.validated.json_schema`, so the schema and
the models cannot drift apart. It describes the validated blocks (what :func:`skye.base.dsl.build`
returns, as ``to_dict()``), which is the form an editor or a model needs to check a generated block.
"""

from __future__ import annotations

from typing import Any

from skye.base.dsl.specs import FlowSpec, PromptSpec, RouterSpec
from skye.base.validated import json_schema

_KINDS: dict[str, type] = {"router": RouterSpec, "flow": FlowSpec, "prompt": PromptSpec}
_DRAFT = "https://json-schema.org/draft/2020-12/schema"


def block_schema(kind: str | None = None) -> dict[str, Any]:
    """The JSON Schema of one block kind, or of all of them.

    Args:
        kind: ``"router"``, ``"flow"`` or ``"prompt"``; ``None`` for the three together under
            ``$defs``.

    Returns:
        A JSON Schema as a dict.

    Raises:
        ValueError: If ``kind`` is not a block kind.
    """
    if kind is not None:
        if kind not in _KINDS:
            raise ValueError(f'unknown block kind "{kind}"; use router, flow or prompt')
        return {"$schema": _DRAFT, **json_schema(_KINDS[kind])}
    return {
        "$schema": _DRAFT,
        "title": "Skye .skye blocks",
        "$defs": {name: json_schema(model) for name, model in _KINDS.items()},
        "oneOf": [{"$ref": f"#/$defs/{name}"} for name in _KINDS],
    }
