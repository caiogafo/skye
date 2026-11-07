"""One name, one home (Requirement 22.4 of steering, task 2.1 of the uxui spec).

A public class name is defined in one module of ``src/skye``. A re-export (an import) is not a definition.
``KNOWN_DUPLICATES`` only shrinks: an entry that is no longer a duplicate fails the test.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "skye"

# name -> modules that define it. The pydantic CapabilitySchema of `tools` leaves with the pydantic removal (O4, 0-base-structure group 14).
KNOWN_DUPLICATES: dict[str, set[str]] = {
    "CapabilitySchema": {"skye.base.interfaces.capability", "skye.tools.schema"},
    # Found by this test, not named in the audit: the `tools` interface is the older, pydantic-typed copy of the base Port.
    "CapabilityInterface": {"skye.base.interfaces.capability", "skye.tools.interface"},
}


def _module(path: Path) -> str:
    parts = list(path.relative_to(SRC.parent).with_suffix("").parts)
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def definitions() -> dict[str, set[str]]:
    found: dict[str, set[str]] = defaultdict(set)
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                found[node.name].add(_module(path))
    return found


def duplicates() -> dict[str, set[str]]:
    return {name: mods for name, mods in definitions().items() if len(mods) > 1}


def test_no_unexpected_duplicate_class_name():
    unexpected = {n: sorted(m) for n, m in duplicates().items() if n not in KNOWN_DUPLICATES}
    assert not unexpected, f"public class names defined in more than one module: {unexpected}"


def test_known_duplicates_only_shrink():
    current = duplicates()
    stale = [n for n in KNOWN_DUPLICATES if n not in current]
    assert not stale, f"no longer duplicated, remove from KNOWN_DUPLICATES: {stale}"
    grown = {n: sorted(current[n] - KNOWN_DUPLICATES[n]) for n in KNOWN_DUPLICATES if current[n] - KNOWN_DUPLICATES[n]}
    assert not grown, f"a known duplicate spread to new modules: {grown}"
