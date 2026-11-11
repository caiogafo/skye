"""Deterministic checks of the documentation wiki (Requirement 15.5).

Every page under docs/ (except docs/_notes, which holds personal local notes and is not part of the wiki) has front matter with
a title and a status (the date of a page comes from git, decision D103); every relative link in the wiki and in README.md resolves; and every page can be
reached from docs/index.md by following links. Offline, no network.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.budget.measure import ROOT

DOCS = ROOT / "docs"
REQUIRED_KEYS = ("title", "status")
#: Pages that only link to others and may be short.
INDEX_PAGES = {"index.md"}
MIN_LINES = 20
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


def test_extension_page_has_a_row_for_every_exported_name():
    """Requirement 15.10: `docs/guides/extend/index.md` lists every name of `skye.interfaces.__all__`."""
    import skye.interfaces as interfaces

    text = (DOCS / "guides" / "extend" / "index.md").read_text(encoding="utf-8")
    missing = [name for name in interfaces.__all__ if f"| `{name}` |" not in text]
    assert not missing, f"docs/guides/extend/index.md has no row for {missing}"


def test_no_page_is_a_stub():
    """D103: no empty page; a page that is not an index has at least MIN_LINES lines of content."""
    short = []
    for page in pages():
        if page.name in INDEX_PAGES or "reference/api" in page.relative_to(DOCS).as_posix():
            continue
        body = re.sub(r"^---\n.*?\n---\n", "", page.read_text(encoding="utf-8"), flags=re.DOTALL)
        lines = [line for line in body.splitlines() if line.strip()]
        if len(lines) < MIN_LINES or "TODO" in body:
            short.append(f"{page.relative_to(ROOT)} ({len(lines)} lines)")
    assert not short, f"stub pages (fewer than {MIN_LINES} lines or a TODO): {short}"


def test_no_page_dates_itself_by_hand():
    """D103: the date of a page comes from git; `last_updated` and a codename line are not written in pages."""
    bad = [
        str(p.relative_to(ROOT))
        for p in pages()
        if "last_updated:" in p.read_text(encoding="utf-8") or "*codename:" in p.read_text(encoding="utf-8")
    ]
    assert not bad, f"pages with a hand-written date or a codename line: {bad}"


def test_every_nav_entry_exists_and_every_page_is_in_the_nav():
    """D103: mkdocs.yml and docs/ agree: no missing page, no page left out of the navigation."""
    nav_text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8").split("\nnav:", 1)[1]
    in_nav = set(re.findall(r"([\w./-]+\.md)", nav_text))
    missing = sorted(p for p in in_nav if not (DOCS / p).exists())
    on_disk = {p.relative_to(DOCS).as_posix() for p in pages()}
    left_out = sorted(on_disk - in_nav)
    assert not missing and not left_out, f"in nav but missing: {missing}; not in nav: {left_out}"
