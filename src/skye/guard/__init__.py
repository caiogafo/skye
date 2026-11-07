"""Safety filters and guardrails (optional extra).

This module provides safety filters and guardrails for input/output validation.
Available with skyeai[guard].

Component: guard. Layer: services (2). Declared-but-minimal.

Codename: halo.
"""

__all__ = []


def __getattr__(name: str) -> object:
    """Say that this package is planned, not available yet, instead of a bare AttributeError."""
    if name.startswith("_"):
        raise AttributeError(name)
    raise ImportError(f"skye.guard is planned, not available yet (no attribute {name!r})")
