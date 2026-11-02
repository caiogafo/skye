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
    "policy-engine",
    "prompts-support",
}
ALLOWED_FILES = {"requirements.md", "design.md", "tasks.md", "tasks.meta.json", ".config.kiro"}
REQ_FILE_REF = "#[[file:.kiro/steering/10-requirements.md]]"
DESIGN_FILE_REF = "#[[file:.kiro/steering/11-design.md]]"
DECISIONS_FILE_REF = "#[[file:.kiro/steering/12-decisions.md]]"


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


CROSS_CUTTING_SPEC = "structure"


def test_every_spec_is_named_like_a_component():
    components, _ = _requirements()
    allowed = set(components) | {CROSS_CUTTING_SPEC} | LEGACY_SPECS
    bad = [p.name for p in _spec_dirs() if p.name not in allowed]
    assert not bad, f"spec folders that are neither a component name nor `{CROSS_CUTTING_SPEC}`: {bad}"
    assert (SPECS / CROSS_CUTTING_SPEC).is_dir(), f"the cross-cutting spec `{CROSS_CUTTING_SPEC}` is missing"


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
HONOR = re.compile(r"^\d+\. THE spec SHALL honor decision (D\d+) of " + re.escape(DECISIONS_FILE_REF) + r"\.$")
HISTORY = re.compile(r"^\d+\. THE spec SHALL keep this story as history only, its criteria being mapped in `[^`]+`\.$")


def check_criterion(line: str, ids: set[str], decisions: set[str]) -> str | None:
    """Return why a spec criterion is not an exact pointer to steering, or None when it is.

    The three allowed forms (the file is always written as a Kiro file reference, never as plain text or a code span):
      1. THE spec SHALL realize Requirement N.k of #[[file:.kiro/steering/10-requirements.md]].
      2. THE spec SHALL honor decision Dn of #[[file:.kiro/steering/12-decisions.md]].
      3. THE spec SHALL keep this story as history only, its criteria being mapped in `<path>`.
    """
    r, h = REALIZE.match(line), HONOR.match(line)
    if r:
        return None if r.group(1) in ids else f"Requirement {r.group(1)} does not exist in 10-requirements.md"
    if h:
        return None if h.group(1) in decisions else f"decision {h.group(1)} does not exist in 12-decisions.md"
    if HISTORY.match(line):
        return None
    if "SHALL honor decision" in line:
        return f"a decision pointer must name the file as {DECISIONS_FILE_REF}: {line[:90]}"
    if "SHALL realize Requirement" in line:
        return f"a requirement pointer must name the file as {REQ_FILE_REF}: {line[:90]}"
    return f"not a pointer to steering (write the rule in steering first): {line[:80]}"


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
                problem = check_criterion(line, ids, decisions)
                if problem:
                    bad.append(f"{p.name}: Requirement {expected} criterion {n}: {problem}")
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


def test_criterion_pointers_are_checked_exactly():
    """Each wrong form of a pointer is rejected, each right one accepted (the decision file must be a #[[file:...]] reference)."""
    ids, decisions = {"28.1", "19.1"}, {"D25"}
    ok = [
        "1. THE spec SHALL realize Requirement 28.1 of #[[file:.kiro/steering/10-requirements.md]].",
        "6. THE spec SHALL honor decision D25 of #[[file:.kiro/steering/12-decisions.md]].",
        "1. THE spec SHALL keep this story as history only, its criteria being mapped in `.kiro/docs/requirements-trace.md`.",
    ]
    for line in ok:
        assert check_criterion(line, ids, decisions) is None, line
    bad = {
        "6. THE spec SHALL honor decision D25 of `.kiro/steering/12-decisions.md`.": "must name the file",
        "6. THE spec SHALL honor decision D25 of .kiro/steering/12-decisions.md.": "must name the file",
        "6. THE spec SHALL honor decision D25.": "must name the file",
        "1. THE spec SHALL realize Requirement 28.1 of `.kiro/steering/10-requirements.md`.": "must name the file",
        "1. THE spec SHALL realize Requirement 28.1.": "must name the file",
        "1. THE spec SHALL realize Requirement 99.9 of #[[file:.kiro/steering/10-requirements.md]].": "does not exist",
        "6. THE spec SHALL honor decision D99 of #[[file:.kiro/steering/12-decisions.md]].": "does not exist",
        "6. THE spec SHALL honor decision D25 of #[[file:.kiro/steering/10-requirements.md]].": "must name the file",
        "1. THE store SHALL keep state in DynamoDB.": "not a pointer",
    }
    for line, why in bad.items():
        got = check_criterion(line, ids, decisions)
        assert got and why in got, f"{line!r} should fail with {why!r}, got {got!r}"


TASK_LINE = re.compile(r"^\s*- \[[ x]\]\*? \d+(?:\.\d+)*\.? \S")


def test_spec_task_lines_follow_the_kiro_task_format():
    """Every checkbox line of a migrated spec is `- [ ] N. title` or `- [x] N.k title` (optional tasks add `*` after the box).

    Kiro validates this syntax; a milestone is a numbered top-level task, not an `M1` label, and nothing may precede the number.
    """
    bad = []
    for p in _spec_dirs():
        if p.name in LEGACY_SPECS:
            continue
        for n, line in enumerate((p / "tasks.md").read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"^\s*- \[", line) and not TASK_LINE.match(line):
                bad.append(f"{p.name}/tasks.md:{n}: {line.strip()[:70]}")
    assert not bad, "; ".join(bad)


def test_the_task_line_pattern_accepts_and_rejects():
    good = ["- [ ] 1. Shared transport", "- [x] 2. Done", "  - [x] 1.1 Sub task", "  - [ ]* 2.3 Optional task", "- [ ] 10. Rename"]
    wrong = ["- [ ] M1. Shared transport", "  - [x] M1.1 Sub task", "- [ ] models:1.1 Task", "- [ ] Do a thing", "- [ ]1. No space"]
    assert all(TASK_LINE.match(x) for x in good)
    assert not any(TASK_LINE.match(x) for x in wrong)
