"""An extra is named after what it enables, and an extra named after a provider installs no provider SDK (Requirement 7.13).

Each provider has a built-in REST adapter (Requirement 9.3), so `anthropic`, `bedrock`, `cohere`, `google` and `azure` are empty extras that
exist only to keep old install commands working. Exact token counts live in the extra `tokens` (`tiktoken`), named for its function (decision D33); `openai` is an empty extra.
The list of known debt is empty and may not grow.
"""

from __future__ import annotations

from tests.budget.measure import pyproject

PROVIDERS = {"openai", "anthropic", "bedrock", "azure", "google", "cohere"}
KNOWN_PROVIDER_EXTRAS_WITH_A_LIBRARY: set[str] = set()


def _extras() -> dict[str, list[str]]:
    return pyproject()["project"]["optional-dependencies"]


def test_an_extra_named_after_a_provider_declares_no_library():
    bad = [
        f"{name} declares {libs}"
        for name, libs in _extras().items()
        if name in PROVIDERS and libs and name not in KNOWN_PROVIDER_EXTRAS_WITH_A_LIBRARY
    ]
    assert not bad, "an extra named after a provider must not install a library (the provider has a built-in adapter): " + "; ".join(bad)


def test_the_known_debt_is_not_stale():
    extras = _extras()
    stale = sorted(name for name in KNOWN_PROVIDER_EXTRAS_WITH_A_LIBRARY if not extras.get(name))
    assert not stale, f"remove from KNOWN_PROVIDER_EXTRAS_WITH_A_LIBRARY (the extra was renamed or emptied): {stale}"
