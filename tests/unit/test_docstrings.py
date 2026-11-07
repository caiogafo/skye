"""The first docstring a user reads runs (Requirement 15.9; task 6.2 of the uxui spec).

``doctest`` runs on the package docstring and on each Port module docstring. A line that needs a network, a key or an object the
text only names carries ``# doctest: +SKIP``; everything else is a real, offline call.
"""

from __future__ import annotations

import doctest
import importlib
import inspect

import pytest

import skye
import skye.interfaces as interfaces
from skye.utils.validation import port_methods

NOT_PORTS = {"CapabilitySchema", "Decision", "DecisionResult", "EventType", "MemoryEntryLike", "RoutingStrategy", "SafetyResult"}

MODULES = ["skye"] + sorted(
    {
        getattr(interfaces, name).__module__
        for name in interfaces.__all__
        if name not in NOT_PORTS and inspect.isclass(getattr(interfaces, name)) and port_methods(getattr(interfaces, name))
    }
)


@pytest.mark.parametrize("module", MODULES)
def test_module_docstring_examples_run(module: str):
    mod = importlib.import_module(module)
    test = doctest.DocTestParser().get_doctest(mod.__doc__ or "", vars(mod).copy(), module, None, 0)
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    out: list[str] = []
    runner.run(test, out=out.append)
    assert runner.failures == 0, "".join(out)


def test_package_docstring_does_not_use_removed_names():
    assert "response.text" not in (skye.__doc__ or "")
    assert "skyeai[bedrock]" not in (skye.__doc__ or "")
