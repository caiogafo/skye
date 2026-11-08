"""Plain output (Requirement 24.7 of steering, task 5.9 of the uxui spec).

No banner row (``"=" * 60``) and no emoji in the examples. A folder still dirty is listed in ``KNOWN_FOLDERS``; the list only
shrinks.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
KNOWN_FOLDERS: set[str] = set()
BANNER_RE = re.compile(r"""["'][=\-─━*#_]["']\s*\*\s*\d+|["'][=\-─━*#_]{10,}["']""")
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-⛿✀-➿⭐️]")


def style_problems(text: str) -> list[str]:
    problems = []
    for number, line in enumerate(text.splitlines(), 1):
        if BANNER_RE.search(line):
            problems.append(f"{number}: banner row")
        if EMOJI_RE.search(line):
            problems.append(f"{number}: emoji")
    return problems


def _scripts() -> list[Path]:
    return [p for p in sorted(EXAMPLES.rglob("*.py")) if "__pycache__" not in p.parts]


def test_the_rule_flags_a_banner_and_an_emoji():
    assert style_problems('print("=" * 60)') == ["1: banner row"]
    assert style_problems('print("✅ done")') == ["1: emoji"]
    assert style_problems('print("done")') == []


def test_examples_print_plainly():
    found = {}
    for path in _scripts():
        rel = path.relative_to(EXAMPLES)
        if rel.parts[0] in KNOWN_FOLDERS:
            continue
        problems = style_problems(path.read_text(encoding="utf-8"))
        if problems:
            found[rel.as_posix()] = problems[:3]
    assert not found, f"banner rows or emoji in examples: {found}"


def test_known_folders_only_shrink():
    for folder in KNOWN_FOLDERS:
        dirty = any(style_problems(p.read_text(encoding="utf-8")) for p in _scripts() if p.relative_to(EXAMPLES).parts[0] == folder)
        assert dirty, f"examples/{folder} is clean now, remove it from KNOWN_FOLDERS"
