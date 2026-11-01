"""Differential tests: built-in vs official-SDK implementation (dev environment only, Req 18).

Everything here is marked ``differential`` and skips (never fails) when the SDK is not installed.
"""

from __future__ import annotations

import sys

import pytest

try:  # grab the real library at collection time, before other test modules stub it
    import fastmcp as _real_fastmcp
except ImportError:  # SDK not installed: the tests skip themselves
    _real_fastmcp = None

from tests.differential.fake_mcp_server import FakeMCPServer


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "tests/differential" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.differential)


@pytest.fixture(scope="session")
def mcp_server():
    with FakeMCPServer() as s:
        yield s


@pytest.fixture(autouse=True)
def _real_fastmcp_in_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Legacy unit tests assign ``sys.modules["fastmcp"] = MagicMock()`` at import and never undo it;
    differential tests must always see the real library."""
    if _real_fastmcp is not None:
        monkeypatch.setitem(sys.modules, "fastmcp", _real_fastmcp)
