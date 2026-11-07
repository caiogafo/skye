"""Every Port module states its contract (Requirement 16.8; task 3.7 of the uxui spec).

The module docstring of each exported Port ends with three labelled lines: ``Raises:``, ``Missing:`` and ``Concurrency:``.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

import skye.interfaces as interfaces
from skye.utils.validation import port_methods

NOT_PORTS = {"CapabilitySchema", "Decision", "DecisionResult", "EventType", "MemoryEntryLike", "RoutingStrategy", "SafetyResult"}
LABELS = ("Raises:", "Missing:", "Concurrency:")

PORT_MODULES = sorted(
    {
        getattr(interfaces, name).__module__
        for name in interfaces.__all__
        if name not in NOT_PORTS and inspect.isclass(getattr(interfaces, name)) and port_methods(getattr(interfaces, name))
    }
)


@pytest.mark.parametrize("module", PORT_MODULES)
def test_port_module_docstring_has_the_contract_footer(module: str):
    doc = importlib.import_module(module).__doc__ or ""
    missing = [label for label in LABELS if f"\n{label}" not in doc]
    assert not missing, f"{module} docstring lacks {missing}"
