"""Install lines are true (Requirement 24.6 of steering, task 5.5 of the uxui spec).

Every ``pip install skyeai[extra]`` in ``examples/``, ``docs/`` and ``README.md`` names an extra that exists in ``pyproject.toml``
and is not listed in ``known_empty`` of ``budgets.toml`` (an empty extra installs nothing).
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALL_RE = re.compile(r"pip install (?:-\S+ )*skyeai\[([\w, -]+)\]")
# Documents not yet corrected. Only shrinks: a file listed here with no bad line fails the test.
KNOWN_STALE: set[str] = set()


def _extras() -> tuple[set[str], set[str]]:
    declared = set(tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["optional-dependencies"])
    empty = set(tomllib.loads((ROOT / "budgets.toml").read_text())["extras_policy"]["known_empty"])
    return declared, empty


def _files() -> list[Path]:
    out: list[Path] = [ROOT / "README.md"]
    for base in (ROOT / "examples", ROOT / "docs"):
        out += [p for p in sorted(base.rglob("*")) if p.suffix in (".py", ".md") and "__pycache__" not in p.parts]
    return out


def bad_lines(text: str, declared: set[str], empty: set[str]) -> list[str]:
    bad = []
    for match in INSTALL_RE.finditer(text):
        for extra in (e.strip() for e in match.group(1).split(",")):
            if extra not in declared or extra in empty:
                bad.append(extra)
    return bad


def _violations() -> dict[str, list[str]]:
    declared, empty = _extras()
    found = {}
    for path in _files():
        bad = bad_lines(path.read_text(encoding="utf-8"), declared, empty)
        if bad:
            found[str(path.relative_to(ROOT))] = bad
    return found


def test_the_rule_flags_missing_and_empty_extras():
    assert bad_lines("pip install skyeai[nope,memory]", {"memory"}, set()) == ["nope"]
    assert bad_lines("pip install skyeai[openai]", {"openai"}, {"openai"}) == ["openai"]
    assert bad_lines("pip install skyeai[memory]", {"memory"}, set()) == []


def test_install_lines_name_real_extras():
    unexpected = {f: b for f, b in _violations().items() if f not in KNOWN_STALE}
    assert not unexpected, f"install lines naming a missing or empty extra (use `pip install skyeai`): {unexpected}"


def test_known_stale_only_shrinks():
    current = _violations()
    assert not [f for f in KNOWN_STALE if f not in current], "remove fixed documents from KNOWN_STALE"
