"""The ``.skye`` router fixtures of ``tests/fixtures/sample_configs.py`` are valid, except the one
that is meant to be invalid.
"""

from __future__ import annotations

import pytest

from skye.base.dsl import check_text
from tests.fixtures import sample_configs

VALID = [
    name
    for name in dir(sample_configs)
    if name.endswith("_CONFIG_SKYE") and not name.startswith("INVALID")
]


@pytest.mark.parametrize("name", VALID)
def test_the_sample_router_text_passes_the_checker(name):
    assert check_text(getattr(sample_configs, name), name) == []


def test_there_are_samples_and_the_invalid_one_fails():
    assert len(VALID) == 5
    assert check_text(sample_configs.INVALID_ROUTER_CONFIG_SKYE, "invalid") != []
