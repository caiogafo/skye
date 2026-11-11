"""Shared fixtures for every test.

``skye.load_config`` applies the log levels it reads (D106), and an example run in-process (``examples/basic/configuration.py``
sets ``log_level`` to ``ERROR``) leaves the ``skye`` logger at that level. A later test that reads log records through
``caplog`` would then miss the INFO and DEBUG ones, so each test gets the logger levels back as it found them.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _restore_skye_log_levels() -> Iterator[None]:
    loggers = {
        name: logger
        for name, logger in logging.Logger.manager.loggerDict.items()
        if isinstance(logger, logging.Logger) and (name == "skye" or name.startswith("skye."))
    }
    loggers.setdefault("skye", logging.getLogger("skye"))
    saved = {name: logger.level for name, logger in loggers.items()}
    yield
    for name, level in saved.items():
        logging.getLogger(name).setLevel(level)
    for name, logger in list(logging.Logger.manager.loggerDict.items()):
        if isinstance(logger, logging.Logger) and name.startswith("skye.") and name not in saved:
            logger.setLevel(logging.NOTSET)
