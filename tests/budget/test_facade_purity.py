"""Facades only re-export (Requirement 7.15 of steering, task 1.4 of the uxui spec).

A facade module holds imports and ``__all__``, nothing else: no ``def``, no ``class``, no other assignment.
Every name in ``__all__`` must be defined by the module it is imported from.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "skye"
FACADES = ["interfaces", "data", "dsl", "messages", "completion", "exceptions", "config"]


def _tree(name: str) -> ast.Module:
    return ast.parse((SRC / f"{name}.py").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", FACADES)
def test_facade_defines_nothing(name: str):
    bad = []
    for node in _tree(name).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bad.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if names != ["__all__"]:
                bad.append(", ".join(names) or "assignment")
    assert not bad, f"skye.{name} must only re-export, but defines: {bad}"


@pytest.mark.parametrize("name", FACADES)
def test_all_names_come_from_their_source_module(name: str):
    sources: dict[str, str] = {}
    for node in _tree(name).body:
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("skye."):
            for alias in node.names:
                sources[alias.asname or alias.name] = node.module
    facade = importlib.import_module(f"skye.{name}")
    for exported in facade.__all__:
        assert exported in sources, f"skye.{name}.__all__ lists {exported!r}, which is not imported from a skye module"
        source = importlib.import_module(sources[exported])
        assert hasattr(source, exported), f"{sources[exported]} does not define {exported!r}"
        assert getattr(facade, exported) is getattr(source, exported)
