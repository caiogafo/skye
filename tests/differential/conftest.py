"""Differential tests: built-in vs official-SDK implementation (dev environment only, Requirement 14).

Everything here is marked ``differential`` and skips (never fails) when the SDK is not installed.
"""

from __future__ import annotations

import pytest

from tests.differential.fake_mcp_server import FakeMCPServer


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "tests/differential" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.differential)


@pytest.fixture(scope="session")
def mcp_server():
    with FakeMCPServer() as s:
        yield s
