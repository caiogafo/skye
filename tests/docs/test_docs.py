"""Deterministic checks of the documentation wiki (Requirement 15.5).

Every page under docs/ (except docs/_notes, which holds personal local notes and is not part of the wiki) has front matter with
a title, a status and a last_updated date; every relative link in the wiki and in README.md resolves; and every page can be
reached from docs/index.md by following links. Offline, no network.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.budget.measure import ROOT

DOCS = ROOT / "docs"
REQUIRED_KEYS = ("title", "status", "last_updated")
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")


def pages() -> list[Path]:
    return sorted(p for p in DOCS.rglob("*.md") if "_notes" not in p.relative_to(DOCS).parts)


def front_matter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def links(path: Path) -> list[tuple[str, Path]]:
    """Relative file links of a page: (the link as written, the file it points to)."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?s)```.*?```", "", text)  # links inside code blocks are examples
    found = []
    for target in LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        file_part = target.split("#", 1)[0]
        if file_part:
            found.append((target, (path.parent / file_part).resolve()))
    return found


def test_there_are_pages():
    assert (DOCS / "index.md").exists()
    assert len(pages()) >= 15


def test_every_page_has_front_matter():
    bad = []
    for page in pages():
        fm = front_matter(page.read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED_KEYS if not fm.get(k)]
        if missing:
            bad.append(f"{page.relative_to(ROOT)}: missing {missing}")
    assert not bad, "; ".join(bad)


def test_every_relative_link_resolves():
    bad = []
    for page in pages() + [ROOT / "README.md"]:
        for target, resolved in links(page):
            if not resolved.exists():
                bad.append(f"{page.relative_to(ROOT)} -> {target}")
    assert not bad, "; ".join(bad)


def test_every_page_is_reachable_from_the_index():
    seen: set[Path] = set()
    todo = [(DOCS / "index.md").resolve()]
    while todo:
        page = todo.pop()
        if page in seen or not page.exists() or page.suffix != ".md":
            continue
        seen.add(page)
        for _, resolved in links(page):
            if DOCS.resolve() in resolved.parents:
                todo.append(resolved)
    orphans = [str(p.relative_to(ROOT)) for p in pages() if p.resolve() not in seen]
    assert not orphans, f"pages not reachable from docs/index.md: {orphans}"


def test_the_checks_catch_a_bad_page(tmp_path):
    """The helpers reject a page without front matter and find a broken link."""
    page = tmp_path / "x.md"
    page.write_text("# No front matter\n\n[broken](missing.md)\n", encoding="utf-8")
    assert not front_matter(page.read_text(encoding="utf-8"))
    assert [t for t, r in links(page) if not r.exists()] == ["missing.md"]
