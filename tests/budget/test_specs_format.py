"""Deterministic check that the specs follow the steering conventions (.kiro/steering/20-repo.md).

Requirements live only in .kiro/steering/10-requirements.md and the high-level design in 11-design.md; a spec states its user
stories in Kiro format with pointer criteria and opens its design with a `Builds on:` line. Specs that have not been migrated yet are listed in
LEGACY_SPECS: the list may only shrink, and a name that no longer exists there fails the test so the list cannot go stale.
"""

from __future__ import annotations

import re

from tests.budget.measure import ROOT

KIRO = ROOT / ".kiro"
SPECS = KIRO / "specs"
STEERING = KIRO / "steering"

# Specs still in the old format. Remove a name when its spec is migrated.
LEGACY_SPECS = {
    "agent-runtime",
    "capability-support",
    "gateway",
    "model-providers",
    "policy-engine",
    "prompts-support",
}
ALLOWED_FILES = {"requirements.md", "design.md", "tasks.md", "tasks.meta.json", ".config.kiro"}
REQ_FILE_REF = "#[[file:.kiro/steering/10-requirements.md]]"
DESIGN_FILE_REF = "#[[file:.kiro/steering/11-design.md]]"


def _requirements() -> tuple[list[str], set[str]]:
    """Return the component names (Requirement 1.1) and every existing criterion id `N.k`."""
    text = (STEERING / "10-requirements.md").read_text(encoding="utf-8")
    first = re.search(r"(?m)^1\. THE library SHALL have exactly 15 components: (.*)\.$", text)
    assert first, "Requirement 1.1 (the component list) not found"
    components = [c.strip() for c in first.group(1).split(",")]
    ids: set[str] = set()
    current = None
    for line in text.splitlines():
        h = re.match(r"### Requirement (\d+):", line)
        if h:
            current = h.group(1)
        c = re.match(r"(\d+)\. ", line)
        if current and c:
            ids.add(f"{current}.{c.group(1)}")
    return components, ids


def _design_sections() -> list[str]:
    text = (STEERING / "11-design.md").read_text(encoding="utf-8")
    return [m.group(1).strip().lower() for m in re.finditer(r"(?m)^## (.*)$", text)]


def _spec_dirs() -> list:
    return sorted(p for p in SPECS.iterdir() if p.is_dir())


def test_every_spec_is_named_like_a_component():
    components, _ = _requirements()
    bad = []
    cross = [p.name for p in _spec_dirs() if p.name.endswith("-structure")]
    for p in _spec_dirs():
        if p.name in LEGACY_SPECS or p.name in components or p.name.endswith("-structure"):
            continue
        bad.append(p.name)
    assert not bad, f"spec folders that are not a component name (nor the one cross-cutting spec): {bad}"
    assert len(cross) <= 1, f"more than one cross-cutting spec: {cross}"


def test_legacy_list_is_not_stale():
    existing = {p.name for p in _spec_dirs()}
    stale = sorted(LEGACY_SPECS - existing)
    assert not stale, f"remove from LEGACY_SPECS (spec no longer exists, so it was migrated or renamed): {stale}"


def test_migrated_specs_have_only_the_three_files_and_no_subfolder():
    bad = []
    for p in _spec_dirs():
        if p.name in LEGACY_SPECS:
            continue
        for child in p.iterdir():
            if child.is_dir():
                bad.append(f"{p.name}/{child.name} is a folder")
            elif child.name not in ALLOWED_FILES:
                bad.append(f"{p.name}/{child.name} is not allowed")
        for needed in ("requirements.md", "design.md", "tasks.md"):
            if not (p / needed).exists():
                bad.append(f"{p.name}/{needed} is missing")
    assert not bad, "; ".join(bad)


def _decisions() -> set[str]:
    text = (STEERING / "12-decisions.md").read_text(encoding="utf-8")
    return set(re.findall(r"(?m)^\| (D\d+) \|", text))


REALIZE = re.compile(
    r"^\d+\. THE spec SHALL realize Requirement (\d+\.\d+) of " + re.escape(REQ_FILE_REF) + r"\.$"
)
HONOR = re.compile(r"^\d+\. THE spec SHALL honor decision (D\d+) of `\.kiro/steering/12-decisions\.md`\.$")
HISTORY = re.compile(r"^\d+\. THE spec SHALL keep this story as history only, its criteria being mapped in `[^`]+`\.$")


def test_spec_requirements_follow_kiro_format_and_only_point_to_steering():
    """Kiro format (Introduction, Requirements, `### Requirement N:`, user story, numbered criteria), but every criterion is a pointer.

    The requirements live only in steering (10-requirements.md). A spec states each user story and cites the steering criteria
    it realizes; a criterion that is anything else (a copied or a new rule) fails: write the rule in steering first.
    """
    _, ids = _requirements()
    decisions = _decisions()
    bad = []
    for p in _spec_dirs():
        if p.name in LEGACY_SPECS:
            continue
        text = (p / "requirements.md").read_text(encoding="utf-8")
        for heading in ("# Requirements Document", "## Introduction", "## Requirements"):
            if not re.search(r"(?m)^" + re.escape(heading) + r"$", text):
                bad.append(f"{p.name}: missing '{heading}'")
        sections = re.split(r"(?m)^### Requirement ", text)[1:]
        if not sections:
            bad.append(f"{p.name}: no '### Requirement N:' block")
        for expected, sec in enumerate(sections, 1):
            head = re.match(r"(\d+): \S", sec)
            if not head or int(head.group(1)) != expected:
                bad.append(f"{p.name}: heading {expected} is not '### Requirement {expected}: <title>'")
                continue
            if "**User Story:**" not in sec or "#### Acceptance Criteria" not in sec:
                bad.append(f"{p.name}: Requirement {expected} lacks a user story or acceptance criteria")
                continue
            lines = [x for x in sec.split("#### Acceptance Criteria", 1)[1].splitlines() if re.match(r"\d+\. ", x)]
            if not lines:
                bad.append(f"{p.name}: Requirement {expected} has no criterion")
            for n, line in enumerate(lines, 1):
                if not line.startswith(f"{n}. "):
                    bad.append(f"{p.name}: Requirement {expected} criteria are not numbered 1..n")
                    break
                r, h, hist = REALIZE.match(line), HONOR.match(line), HISTORY.match(line)
                if r:
                    if r.group(1) not in ids:
                        bad.append(f"{p.name}: Requirement {expected} cites {r.group(1)}, which does not exist")
                elif h:
                    if h.group(1) not in decisions:
                        bad.append(f"{p.name}: Requirement {expected} cites decision {h.group(1)}, which does not exist")
                elif not hist:
                    bad.append(f"{p.name}: Requirement {expected} criterion {n} is not a pointer to steering: {line[:80]}")
    assert not bad, "; ".join(bad)


def test_spec_designs_build_on_the_steering_design():
    sections = _design_sections()
    bad = []
    for p in _spec_dirs():
        if p.name in LEGACY_SPECS:
            continue
        text = (p / "design.md").read_text(encoding="utf-8")
        head = text.split("\n", 15)[:15]
        line = next((x for x in head if x.startswith("Builds on:")), None)
        if not line:
            bad.append(f"{p.name}: design.md does not open with a 'Builds on:' line")
            continue
        if DESIGN_FILE_REF not in line:
            bad.append(f"{p.name}: 'Builds on:' does not name {DESIGN_FILE_REF}")
        listed = re.search(r"\(sections: (.*?)\)", line)
        if listed:
            for name in [s.strip().lower() for s in listed.group(1).split(",")]:
                if not any(name in s for s in sections):
                    bad.append(f"{p.name}: section '{name}' is not in 11-design.md")
    assert not bad, "; ".join(bad)
