"""Environment-variable scope (structure Req 27): exactly three Nimbus-prefixed variables.

Provider credentials come from each provider's standard variables, never from a
Nimbus-prefixed one. No variable selects an implementation (Req 24, 25).
"""

import re

from tests.budget.measure import ROOT

ALLOWED = {"NIMBUS_LOG_LEVEL", "NIMBUS_CONFIG", "NIMBUS_ENABLE_TELEMETRY"}


def test_src_references_only_the_three_nimbus_variables() -> None:
    found: dict[str, list[str]] = {}
    for path in sorted((ROOT / "src" / "nimbus").rglob("*.py")):
        for name in set(re.findall(r"NIMBUS_[A-Z][A-Z_]*", path.read_text(encoding="utf-8"))):
            if name not in ALLOWED:
                found.setdefault(name, []).append(str(path.relative_to(ROOT)))
    assert not found, f"Nimbus-prefixed variables outside the allowed three: {found}"
