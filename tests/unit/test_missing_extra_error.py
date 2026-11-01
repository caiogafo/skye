"""Unit tests for MissingExtraError and the base missing_extra helper."""

import pytest

from nimbus.base.exceptions import MissingExtraError, NimbusError
from nimbus.base.lazy_import import missing_extra


def test_is_nimbus_error_and_names_extra():
    err = MissingExtraError(extra="tools", missing="mcp")
    assert isinstance(err, NimbusError)
    assert err.extra == "tools"
    assert err.details["extra"] == "tools"
    assert "nimbus[tools]" in str(err)


def test_missing_extra_wraps_original_import_error():
    with pytest.raises(MissingExtraError) as exc_info:
        missing_extra("nonexistent_module_xyz", extra="tools")
    assert isinstance(exc_info.value.__cause__, ModuleNotFoundError)
    assert exc_info.value.extra == "tools"


def test_missing_extra_returns_present_module():
    import json

    assert missing_extra("json", extra="x") is json
