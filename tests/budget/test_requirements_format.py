"""Deterministic check of the requirements format, for every requirements document of the repository.

Applies to `.kiro/steering/10-requirements.md` and to the `requirements.md` of every spec (migrated or not). The format is the one
Kiro's tools expect, so the documents can be analyzed by them:

    # Requirements Document
    ## Introduction
    ## Requirements
    ### Requirement N: <title>          (N = 1..n, in order, no gaps)
    **User Story:** As a <role>, I want <goal>, so that <benefit>
    #### Acceptance Criteria
    1. <criterion with SHALL>            (numbered 1..n, no gaps)

The rule that the requirements live only in steering, and that a spec only points to them, is checked in test_specs_format.py.
"""

from __future__ import annotations

import re

import pytest

from tests.budget.measure import ROOT

KIRO = ROOT / ".kiro"
DOCUMENTS = [KIRO / "steering" / "10-requirements.md"] + sorted((KIRO / "specs").glob("*/requirements.md"))

STORY = re.compile(r"^\*\*User Story:\*\* As (?:a|an|the) .+?, I (?:want|need) .+?, so that .+", re.DOTALL)
STORY_NO_BENEFIT = re.compile(r"^\*\*User Story:\*\* As (?:a|an|the) .+?, I (?:want|need) .+", re.DOTALL)

# Specs whose user stories still lack the "so that <benefit>" clause. The list may only shrink: a spec that has been fixed
# must be removed (the stale-list test fails otherwise).
STORIES_WITHOUT_BENEFIT: set[str] = set()


def _id(path) -> str:
    return str(path.relative_to(KIRO))


def validate(text: str, require_benefit: bool = True) -> list[str]:
    """Return the format problems of one requirements document (empty when it conforms)."""
    problems: list[str] = []
    if not re.search(r"(?m)^# Requirements Document", text):
        problems.append("missing the title '# Requirements Document'")
    for heading in ("## Introduction", "## Requirements"):
        if not re.search(r"(?m)^" + re.escape(heading) + r"\s*$", text):
            problems.append(f"missing '{heading}'")
    intro = text.find("## Introduction")
    reqs = text.find("## Requirements")
    if intro != -1 and reqs != -1 and intro > reqs:
        problems.append("'## Introduction' must come before '## Requirements'")
    body = text[reqs:] if reqs != -1 else ""
    blocks = re.split(r"(?m)^### Requirement ", body)[1:]
    if not blocks:
        problems.append("no '### Requirement N: <title>' block")
    for expected, block in enumerate(blocks, 1):
        block = re.split(r"(?m)^## ", block, maxsplit=1)[0]  # a later '## ' section (notes, open questions) is not a requirement
        head = re.match(r"(\d+): (\S.*)", block)
        if not head or int(head.group(1)) != expected:
            problems.append(f"block {expected}: heading is not '### Requirement {expected}: <title>'")
            continue
        label = f"Requirement {expected}"
        story = re.search(r"(?m)^\*\*User Story:\*\* .*(?:\n(?!\n|#).*)*", block)
        if not story:
            problems.append(f"{label}: no '**User Story:**'")
        elif not (STORY if require_benefit else STORY_NO_BENEFIT).match(story.group(0)):
            problems.append(f"{label}: the user story is not 'As a <role>, I want <goal>, so that <benefit>'")
        if "#### Acceptance Criteria" not in block:
            problems.append(f"{label}: no '#### Acceptance Criteria'")
            continue
        criteria = block.split("#### Acceptance Criteria", 1)[1]
        numbers = [int(n) for n in re.findall(r"(?m)^(\d+)\. ", criteria)]
        if not numbers:
            problems.append(f"{label}: no numbered criterion")
        elif numbers != list(range(1, len(numbers) + 1)):
            problems.append(f"{label}: criteria are not numbered 1..n ({numbers})")
        for line in re.findall(r"(?m)^\d+\. .*$", criteria):
            if " SHALL " not in line and " SHALL NOT " not in line:
                problems.append(f"{label}: criterion without SHALL: {line[:70]}")
    return problems


@pytest.mark.parametrize("path", DOCUMENTS, ids=_id)
def test_requirements_document_follows_the_kiro_format(path):
    legacy = path.parent.name in STORIES_WITHOUT_BENEFIT
    problems = validate(path.read_text(encoding="utf-8"), require_benefit=not legacy)
    assert not problems, f"{_id(path)}: " + "; ".join(problems)


def test_benefit_exemption_list_is_not_stale():
    """A spec listed in STORIES_WITHOUT_BENEFIT must still lack a benefit clause; once fixed it has to leave the list."""
    stale = []
    for name in sorted(STORIES_WITHOUT_BENEFIT):
        path = KIRO / "specs" / name / "requirements.md"
        if not path.exists() or not validate(path.read_text(encoding="utf-8"), require_benefit=True):
            stale.append(name)
    assert not stale, f"remove from STORIES_WITHOUT_BENEFIT (fixed or gone): {stale}"


def test_the_validator_rejects_a_bad_document():
    """The checker must fail on a document that breaks the format, so a green run means something."""
    bad = (
        "# Requirements Document\n## Introduction\nx\n## Requirements\n"
        "### Requirement 2: Skips one\n\n**User Story:** I just want it\n\n#### Acceptance Criteria\n\n1. Does a thing.\n3. Another.\n"
    )
    problems = validate(bad)
    assert any("heading is not" in p for p in problems)


def test_the_validator_accepts_a_good_document():
    good = (
        "# Requirements Document\n## Introduction\nx\n## Requirements\n"
        "### Requirement 1: Title\n\n**User Story:** As a user, I want a thing, so that I am happy\n\n"
        "#### Acceptance Criteria\n\n1. THE system SHALL do a thing.\n2. WHEN x happens, THE system SHALL do y.\n"
    )
    assert validate(good) == []


def test_there_is_a_requirements_document_for_every_spec():
    missing = [p.name for p in sorted((KIRO / "specs").iterdir()) if p.is_dir() and not (p / "requirements.md").exists()]
    assert not missing, f"specs without requirements.md: {missing}"
