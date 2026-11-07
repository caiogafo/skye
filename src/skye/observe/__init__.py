"""Observability and telemetry (optional extra).

This module provides observability, logging, metrics, and tracing capabilities.
Available with skyeai[observe].

Component: observe. Layer: services (2). Declared-but-minimal.

Codename: radar.
"""

__all__ = []


def __getattr__(name: str) -> object:
    """Say that this package is planned, not available yet, instead of a bare AttributeError."""
    if name.startswith("_"):
        raise AttributeError(name)
    raise ImportError(f"skye.observe is planned, not available yet (no attribute {name!r})")
