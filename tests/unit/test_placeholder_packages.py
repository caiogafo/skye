"""A placeholder package says it is planned, not available yet, when a user asks it for a name (decision D40, task 4.6)."""

import importlib

import pytest

PLACEHOLDERS = ["gateway", "teams", "policy", "observe", "guard"]


@pytest.mark.parametrize("name", PLACEHOLDERS)
def test_unknown_attribute_raises_a_clear_import_error(name):
    module = importlib.import_module(f"skye.{name}")
    with pytest.raises(ImportError, match=f"skye.{name} is planned, not available yet"):
        module.Something


@pytest.mark.parametrize("name", PLACEHOLDERS)
def test_from_import_gives_the_same_message(name):
    with pytest.raises(ImportError, match="planned, not available yet"):
        exec(f"from skye.{name} import Something")


@pytest.mark.parametrize("name", PLACEHOLDERS)
def test_import_machinery_attributes_still_work(name):
    module = importlib.import_module(f"skye.{name}")
    assert module.__name__ == f"skye.{name}"
    assert module.__all__ == []


def test_flows_is_no_longer_empty_but_still_says_what_is_planned():
    """`skye.flows` has `Flow` (it loads and checks a flow, task 8.4); the runtime is planned, and an unknown name says so."""
    module = importlib.import_module("skye.flows")
    assert module.__all__ == ["Flow"]
    with pytest.raises(ImportError, match="the flow runtime is planned, not available yet"):
        module.Something
    with pytest.raises(ImportError, match="planned, not available yet"):
        exec("from skye.flows import Something")
