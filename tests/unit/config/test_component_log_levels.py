"""A log level per component through ``SkyeConfig`` (Requirement 18.3)."""

import logging

import pytest

from skye.base.config import ConfigLoader, SkyeConfig
from skye.base.exceptions import ConfigurationError, ValidationError


def test_a_component_uses_its_own_level_else_the_global_one():
    config = SkyeConfig(log_level="info", component_log_levels={"router": "debug"})
    assert config.level_for("router") == "DEBUG"
    assert config.level_for("models") == "INFO"


def test_an_unknown_level_is_rejected():
    with pytest.raises(ValidationError):
        SkyeConfig(component_log_levels={"router": "LOUD"})


def test_the_loader_reads_levels_from_overrides_and_rejects_bad_ones():
    config = ConfigLoader.load(overrides={"component_log_levels": {"tools": "ERROR"}})
    assert config.level_for("tools") == "ERROR"
    with pytest.raises(ConfigurationError):
        ConfigLoader.load(overrides={"component_log_levels": {"tools": "LOUD"}})


def test_apply_log_levels_sets_the_loggers():
    saved = {name: logging.getLogger(name).level for name in ("skye", "skye.router", "skye.models")}
    try:
        SkyeConfig(log_level="WARNING", component_log_levels={"router": "DEBUG"}).apply_log_levels()
        assert logging.getLogger("skye").level == logging.WARNING
        assert logging.getLogger("skye.router").level == logging.DEBUG
        assert logging.getLogger("skye.models").level == saved["skye.models"]
    finally:
        for name, level in saved.items():
            logging.getLogger(name).setLevel(level)
