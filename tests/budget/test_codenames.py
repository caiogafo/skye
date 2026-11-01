"""Codename watermark rules (structure spec, Requirement 9.2, 9.3, 9.6-9.9).

Deterministic and offline: the 14 Component Codenames match ^[a-z]{3,7}$, are unique, number
exactly 14, and never appear in a package name, a file name or an import under src/nimbus.
`vapor` (the Runnable Port's documentation-only codename) is checked separately and is not
one of the 14.

A name "contains" a Codename when one of its words equals it. Words are the pieces left
after splitting on `.`, `_`, `-` and `/`, so `stream` matches `stream.py` and `a/stream_x.py`
but not `streaming.py`. A violation message names the Codename and where it was found.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from tests.budget.measure import ROOT

PATTERN = re.compile(r"^[a-z]{3,7}$")
SRC = ROOT / "src" / "nimbus"

# Requirement 9.1 (fixed mapping, taken as given).
COMPONENT_CODENAMES = {
    "base": "stratus",
    "models": "zephyr",
    "store": "lake",
    "router": "jet",
    "tools": "updraft",
    "prompts": "cirrus",
    "memory": "dew",
    "guard": "halo",
    "policy": "isobar",
    "observe": "radar",
    "gateway": "horizon",
    "agents": "cyclone",
    "teams": "front",
    "flows": "stream",
}
RUNNABLE_CODENAME = "vapor"  # Requirement 9.8: documentation-only, not one of the 14.

_WORD_SPLIT = re.compile(r"[._\-/\\]+")


def _words(name: str) -> set[str]:
    return {w for w in _WORD_SPLIT.split(name) if w}


def _scan_names(codenames: set[str]) -> list[str]:
    """Codename hits in directory names and file names under src/nimbus."""
    hits = []
    for path in sorted(SRC.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(SRC).as_posix()
        kind = "package name" if path.is_dir() else "file name"
        for word in sorted(_words(path.name) & codenames):
            hits.append(f"codename '{word}' in {kind}: src/nimbus/{rel}")
    return hits


def _scan_imports(codenames: set[str]) -> list[str]:
    """Codename hits in import statements (module path and imported names)."""
    hits = []
    for path in sorted(SRC.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                targets = [node.module or ""] + [a.name for a in node.names]
            else:
                continue
            for target in targets:
                for word in sorted(_words(target) & codenames):
                    hits.append(f"codename '{word}' in import '{target}': {rel}:{node.lineno}")
    return hits


def test_codenames_match_pattern():
    bad = [f"codename '{c}' (component '{k}') does not match ^[a-z]{{3,7}}$"
           for k, c in COMPONENT_CODENAMES.items() if not PATTERN.match(c)]
    assert not bad, "\n".join(bad)


def test_codenames_are_unique():
    seen: dict[str, str] = {}
    dups = []
    for component, codename in COMPONENT_CODENAMES.items():
        if codename in seen:
            dups.append(f"codename '{codename}' used by both '{seen[codename]}' and '{component}'")
        seen[codename] = component
    assert not dups, "\n".join(dups)


def test_exactly_14_codenames():
    assert len(COMPONENT_CODENAMES) == 14, f"expected 14 codenames, found {len(COMPONENT_CODENAMES)}"
    assert len(set(COMPONENT_CODENAMES.values())) == 14


def test_codenames_not_in_package_or_file_names():
    hits = _scan_names(set(COMPONENT_CODENAMES.values()))
    assert not hits, "\n".join(hits)


def test_codenames_not_in_imports():
    hits = _scan_imports(set(COMPONENT_CODENAMES.values()))
    assert not hits, "\n".join(hits)


def test_runnable_codename_vapor():
    assert PATTERN.match(RUNNABLE_CODENAME), f"codename '{RUNNABLE_CODENAME}' does not match ^[a-z]{{3,7}}$"
    assert RUNNABLE_CODENAME not in COMPONENT_CODENAMES.values(), (
        f"codename '{RUNNABLE_CODENAME}' collides with a Component Codename"
    )
    # Not counted among the 14: the mapping stays at 14 without it.
    assert len(COMPONENT_CODENAMES) == 14


def test_vapor_not_in_package_file_or_import_names():
    hits = _scan_names({RUNNABLE_CODENAME}) + _scan_imports({RUNNABLE_CODENAME})
    assert not hits, "\n".join(hits)
