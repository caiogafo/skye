"""What `import nimbus` must not do, checked in every normal test run.

No network, a few subprocesses. Module count, time and memory are checked in a clean
core-only environment instead (test_footprint_budget.py), because this environment has
the development libraries installed and would inflate them.
"""

from __future__ import annotations

import sys

from tests.budget.measure import load_budgets, load_metrics


def test_import_loads_no_optional_dependency() -> None:
    budget = load_budgets()["load"]
    forbidden, known = set(budget["forbidden_at_import"]), set(budget["known_leaks"])
    loaded = set(load_metrics(sys.executable, runs=1)["loaded"])

    leaked = sorted((forbidden & loaded) - known)
    assert not leaked, (
        f"`import nimbus` now imports {leaked}. Provider SDKs and optional libraries must stay "
        "behind LazyImporter so a cold start only pays for what the application uses."
    )

    fixed = sorted(known - loaded)
    assert not fixed, (
        f"`import nimbus` no longer imports {fixed} (or they are not installed here). If it is "
        "fixed, remove them from known_leaks in budgets.toml."
    )
