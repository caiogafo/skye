"""Examples and docs import from short public paths (decision D34).

A user-facing import has at most two levels (`skye.router`, `skye.interfaces`), never goes through `skye.base`, and never reaches into a
module inside a component (`skye.models.registry`). `skye.base` stays the architectural name of the foundation layer; the public paths
are `skye` (the commonest names), `skye.messages`, `skye.completion`, `skye.exceptions`, `skye.config`, `skye.data` and `skye.interfaces`.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCANNED = [ROOT / "examples", ROOT / "docs", ROOT / "README.md"]
# Documents that describe the internal layout on purpose.
EXEMPT = {ROOT / "docs" / "_notes"}
FROM_RE = re.compile(r"^\s*(?:>>> |\.\.\. )?from (skye[\w.]*) import", re.M)


def _files() -> list[Path]:
    out: list[Path] = []
    for base in SCANNED:
        paths = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.suffix in (".py", ".md"))
        out += [p for p in paths if "__pycache__" not in p.parts and not any(e in p.parents for e in EXEMPT)]
    return out


def _imported_modules(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        mods = []
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "skye":
                mods.append(node.module)
            elif isinstance(node, ast.Import):
                mods += [a.name for a in node.names if a.name.split(".")[0] == "skye"]
        return mods
    return FROM_RE.findall(text)


def violations(modules: list[str]) -> list[str]:
    return [m for m in modules if m.startswith("skye.base") or len(m.split(".")) > 2]


def test_the_rule_flags_long_and_base_paths():
    assert violations(["skye.base.messages", "skye.models.registry", "skye.router", "skye", "skye.interfaces"]) == [
        "skye.base.messages",
        "skye.models.registry",
    ]


@pytest.mark.parametrize("path", _files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_imports_are_short_public_paths(path: Path):
    bad = violations(_imported_modules(path))
    assert not bad, f"{path.relative_to(ROOT)} imports {sorted(set(bad))}: use `skye`, `skye.<package>` or a public facade (D34)"
