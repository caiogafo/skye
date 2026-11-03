"""Codename watermark rules (structure spec, Requirement 9.2, 9.3, 9.6-9.9).

Deterministic and offline: the 15 Component Codenames match ^[a-z]{3,7}$, are unique, number
exactly 15, and never appear in a package name, a file name or an import under src/skye.
`vapor` (the Runnable Port's documentation-only codename) and `nimbus` (the umbrella watermark) are checked separately and are not
one of the 15.

A name "contains" a Codename when one of its words equals it. Words are the pieces left
after splitting on `.`, `_`, `-` and `/`, so `stream` matches `stream.py` and `a/stream_x.py`
but not `streaming.py`. A violation message names the Codename and where it was found.
"""

from __future__ import annotations

import ast
import re

from tests.budget.measure import ROOT

PATTERN = re.compile(r"^[a-z]{3,7}$")
SRC = ROOT / "src" / "skye"

# Requirement 9.1 (fixed mapping, taken as given).
COMPONENT_CODENAMES = {
    "base": "stratus",
    "auth": "ozone",
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
RUNNABLE_CODENAME = "vapor"  # Requirement 9.8: documentation-only, not one of the 15.

_WORD_SPLIT = re.compile(r"[._\-/\\]+")


def _words(name: str) -> set[str]:
    return {w for w in _WORD_SPLIT.split(name) if w}


def _scan_names(codenames: set[str]) -> list[str]:
    """Codename hits in directory names and file names under src/skye."""
    hits = []
    for path in sorted(SRC.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(SRC).as_posix()
        kind = "package name" if path.is_dir() else "file name"
        for word in sorted(_words(path.name) & codenames):
            hits.append(f"codename '{word}' in {kind}: src/skye/{rel}")
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


def test_exactly_15_codenames():
    assert len(COMPONENT_CODENAMES) == 15, f"expected 15 codenames, found {len(COMPONENT_CODENAMES)}"
    assert len(set(COMPONENT_CODENAMES.values())) == 15
    assert COMPONENT_CODENAMES["auth"] == "ozone"


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
    # Not counted among the 15: the mapping stays at 15 without it.
    assert len(COMPONENT_CODENAMES) == 15


def test_vapor_not_in_package_file_or_import_names():
    hits = _scan_names({RUNNABLE_CODENAME}) + _scan_imports({RUNNABLE_CODENAME})
    assert not hits, "\n".join(hits)


def test_codename_is_last_line_of_package_docstring():
    """Requirement 9.2: the last line of each Component's package docstring is `Codename: <name>.`"""
    import ast
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "skye"
    bad = []
    for component, codename in COMPONENT_CODENAMES.items():
        init = root / component / "__init__.py"
        doc = ast.get_docstring(ast.parse(init.read_text()), clean=True) or ""
        if not doc.strip() or doc.strip().splitlines()[-1] != f"Codename: {codename}.":
            bad.append(f"{component}/__init__.py: last docstring line is not 'Codename: {codename}.'")
    assert not bad, "\n".join(bad)


# After the rename to Skye the freed word `nimbus` is the project-wide umbrella watermark
# (Req 23.7): documentation only, outside the 15 Component Codenames, like `vapor`.
UMBRELLA_CODENAME = "nimbus"


def test_umbrella_codename_nimbus():
    assert PATTERN.match(UMBRELLA_CODENAME)
    assert UMBRELLA_CODENAME not in COMPONENT_CODENAMES.values()
    assert len(COMPONENT_CODENAMES) == 15  # not counted among the 15


def test_nimbus_not_in_package_file_or_import_names():
    hits = _scan_names({UMBRELLA_CODENAME}) + _scan_imports({UMBRELLA_CODENAME})
    assert not hits, "\n".join(hits)
