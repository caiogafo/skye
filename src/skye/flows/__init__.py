"""Sequence units into a defined order of steps.

Component: flows. Layer: runtime (3). Declared-but-minimal; content belongs to the flows spec.

Codename: stream.
"""

__all__: list[str] = []


def __getattr__(name: str) -> object:
    """Say that this package is planned, not available yet, instead of a bare AttributeError."""
    if name.startswith("_"):
        raise AttributeError(name)
    raise ImportError(f"skye.flows is planned, not available yet (no attribute {name!r})")
