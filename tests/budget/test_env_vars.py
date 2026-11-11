"""Environment-variable scope (structure Requirement 23): only the allowed Skye-prefixed variables.

Two since decision D106 removed the ``enable_telemetry`` key and the variable that set it.

Provider credentials come from each provider's standard variables, never from a
Skye-prefixed one. No variable selects an implementation (Requirements 20, 21).
"""

import re

from tests.budget.measure import ROOT

ALLOWED = {"SKYE_LOG_LEVEL", "SKYE_CONFIG"}


def test_src_references_only_the_allowed_skye_variables() -> None:
    found: dict[str, list[str]] = {}
    for path in sorted((ROOT / "src" / "skye").rglob("*.py")):
        for name in set(re.findall(r"SKYE_[A-Z][A-Z_]*", path.read_text(encoding="utf-8"))):
            if name not in ALLOWED:
                found.setdefault(name, []).append(str(path.relative_to(ROOT)))
    assert not found, f"Skye-prefixed variables outside the allowed ones: {found}"
