"""The footprint jobs of the pull-request workflow cover exactly the extras that have a budget.

Each job of `.github/workflows/budgets.yml` runs `pytest -k "<target>"`. A target that selects no test makes pytest exit with code 5 and
fails the job (it happened when extras were renamed or became empty and the list kept their old names); an extra with a budget and no
target is never measured in CI. This keeps the list and `budgets.toml` in step.
"""

from __future__ import annotations

import re

from tests.budget.measure import ROOT, load_budgets

WORKFLOW = ROOT / ".github" / "workflows" / "budgets.yml"
CORE_TARGET = "test_core or test_serverless"


def workflow_targets(text: str) -> list[str]:
    footprint = text.split("  footprint:", 1)[1]
    matrix = footprint.split("    steps:", 1)[0]
    return re.findall(r'(?m)^\s+- "([^"]+)"\s*$', matrix)


def test_the_footprint_jobs_match_the_extras_with_a_budget():
    targets = workflow_targets(WORKFLOW.read_text(encoding="utf-8"))
    expected = [CORE_TARGET] + [f"test_extra_footprint and {extra}" for extra in sorted(load_budgets()["extras"])]
    assert targets == expected, (
        "the matrix of the `footprint` job of .github/workflows/budgets.yml differs from the extras of budgets.toml:\n"
        f"  workflow: {targets}\n  expected: {expected}"
    )


def test_the_matrix_reader_finds_the_targets():
    text = 'jobs:\n  footprint:\n    matrix:\n      target:\n        - "a or b"\n        - "c and d"\n    steps:\n      - run: x\n'
    assert workflow_targets(text) == ["a or b", "c and d"]
