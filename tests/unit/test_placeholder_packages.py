"""A placeholder package says it is planned, not available yet, when a user asks it for a name (decision D40, task 4.6)."""

import importlib

import pytest

PLACEHOLDERS = ["flows", "gateway", "teams", "policy", "observe", "guard"]


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
