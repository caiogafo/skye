"""What `import skye` must not do, checked in every normal test run.

No network, a few subprocesses. Module count, time and memory are checked in a clean
core-only environment instead (test_footprint_budget.py), because this environment has
the development libraries installed and would inflate them.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile

from tests.budget.measure import load_budgets, load_metrics

# Runtime orchestrators that are optional (empty) extras: `import skye` curates only the
# four base modules, so it must never pull their implementation packages into sys.modules.
# Spec: .kiro/specs/skye-structure (Requirement 7).
OPTIONAL_RUNTIME_MODULES = ("skye.teams", "skye.flows")

_SUBMODULE_PROBE = """
import json, sys
import skye
targets = {targets!r}
print(json.dumps(sorted(m for m in sys.modules if m in targets)))
"""


def test_import_loads_no_optional_dependency() -> None:
    budget = load_budgets()["load"]
    forbidden, known = set(budget["forbidden_at_import"]), set(budget["known_leaks"])
    loaded = set(load_metrics(sys.executable, runs=1)["loaded"])

    leaked = sorted((forbidden & loaded) - known)
    assert not leaked, (
        f"`import skye` now imports {leaked}. Provider SDKs and optional libraries must stay "
        "behind LazyImporter so a cold start only pays for what the application uses."
    )

    fixed = sorted(known - loaded)
    assert not fixed, (
        f"`import skye` no longer imports {fixed} (or they are not installed here). If it is "
        "fixed, remove them from known_leaks in budgets.toml."
    )


def test_import_does_not_pull_teams_or_flows() -> None:
    """`import skye` must not eagerly import the teams/flows implementation modules.

    teams and flows are optional (empty) runtime extras; the curated public API re-exports
    only the four base modules, so neither orchestrator package may appear in sys.modules
    after a fresh `import skye`. Checked in a fresh interpreter so no earlier import in the
    test session can mask an eager import. Spec: Requirement 7.
    """
    probe = _SUBMODULE_PROBE.format(targets=list(OPTIONAL_RUNTIME_MODULES))
    loaded = json.loads(
        subprocess.check_output([sys.executable, "-c", probe], text=True, cwd=tempfile.gettempdir())
    )
    assert not loaded, (
        f"`import skye` eagerly imports {loaded}. teams and flows are optional runtime "
        "orchestrators; keep them out of the curated public API so a core import never pulls them."
    )
