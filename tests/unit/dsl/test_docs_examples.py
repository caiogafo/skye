"""Every ``skye`` code block in ``docs/`` and ``README.md``, and every ``.skye`` file in
``examples/``, passes ``skye check`` (Property 17).

A block that is meant to show an error is written with the ``text`` fence, not ``skye``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from skye.base.dsl import check_text
from skye.utils.cli import main

ROOT = Path(__file__).resolve().parents[3]
FENCE = re.compile(r"^```skye\n(.*?)^```", re.DOTALL | re.MULTILINE)


def blocks() -> list[tuple[str, int, str]]:
    found = []
    pages = [*sorted((ROOT / "docs").rglob("*.md")), ROOT / "README.md"]
    for page in pages:
        if "_notes" in page.parts or not page.exists():
            continue
        text = page.read_text(encoding="utf-8")
        for match in FENCE.finditer(text):
            if match.group(1).lstrip().startswith("--8<--"):
                continue  # a snippet of a file in examples/, checked as a file below
            line = text.count("\n", 0, match.start()) + 1
            found.append((str(page.relative_to(ROOT)), line, match.group(1)))
    return found


def test_the_language_page_has_examples() -> None:
    pages = {page for page, _, _ in blocks()}
    assert "docs/reference/skye-language.md" in pages
    assert sum(1 for page, _, _ in blocks() if page == "docs/reference/skye-language.md") >= 3


@pytest.mark.parametrize("page,line,text", blocks(), ids=lambda v: str(v)[:40])
def test_skye_block_passes_check(page: str, line: int, text: str) -> None:
    assert [d.format() for d in check_text(text, f"{page}:{line}")] == []


EXAMPLE_FILES = sorted((ROOT / "examples").rglob("*.skye"))


def test_the_examples_folder_has_skye_files() -> None:
    assert len(EXAMPLE_FILES) >= 2


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_skye_example_file_passes_check(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert [d.format() for d in check_text(text, str(path.relative_to(ROOT)))] == []


def test_the_cli_agrees_on_a_docs_block(tmp_path: Path) -> None:
    page, _, text = blocks()[0]
    file = tmp_path / "doc.skye"
    file.write_text(text, encoding="utf-8")
    assert main(["check", str(file)]) == 0
