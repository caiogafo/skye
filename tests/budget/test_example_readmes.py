"""A README matches its folder (Requirement 24.8 of steering, task 5.6 of the uxui spec).

Each example folder has a README that names exactly the ``*.py`` files of the folder (and no file that is missing), and
``examples/README.md`` carries a numbered reading order of the folders. ``prompts/`` is owned by the ``prompts`` spec (task 5).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
KNOWN_FOLDERS = {"prompts"}
NAME_RE = re.compile(r"[\w/-]+\.py")


def folders() -> list[Path]:
    return sorted(p for p in EXAMPLES.iterdir() if p.is_dir() and p.name != "__pycache__" and p.name not in KNOWN_FOLDERS)


def readme_problems(folder: Path) -> list[str]:
    readme = folder / "README.md"
    if not readme.exists():
        return ["no README.md"]
    actual = {p.name for p in folder.glob("*.py") if p.name != "__init__.py"}
    named = {Path(n).name for n in NAME_RE.findall(readme.read_text(encoding="utf-8"))}
    problems = [f"missing from README: {n}" for n in sorted(actual - named)]
    problems += [f"README names a file that is not there: {n}" for n in sorted(named - actual)]
    return problems


@pytest.mark.parametrize("folder", folders(), ids=lambda p: p.name)
def test_readme_lists_exactly_the_folder(folder: Path):
    assert readme_problems(folder) == []


def test_top_readme_numbers_a_reading_order():
    text = (EXAMPLES / "README.md").read_text(encoding="utf-8")
    assert "## Reading order" in text
    listed = re.findall(r"^\d+\. `examples/(\w+)/`", text, re.M)
    assert listed, "no numbered list of folders"
    assert [f for f in listed if not (EXAMPLES / f).is_dir()] == []
    on_disk = {p.name for p in EXAMPLES.iterdir() if p.is_dir() and p.name != "__pycache__"}
    assert on_disk - set(listed) == set(), "folders missing from the reading order"


def test_known_folders_only_shrink():
    for folder in KNOWN_FOLDERS:
        assert readme_problems(EXAMPLES / folder), f"examples/{folder} has a matching README now, remove it from KNOWN_FOLDERS"
