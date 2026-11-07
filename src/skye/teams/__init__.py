"""Coordinate multiple units toward a shared objective; owns the team-role concept.

Component: teams. Layer: runtime (3). Declared-but-minimal; content belongs to the teams spec.

Codename: front.
"""

__all__: list[str] = []


def __getattr__(name: str) -> object:
    """Say that this package is planned, not available yet, instead of a bare AttributeError."""
    if name.startswith("_"):
        raise AttributeError(name)
    raise ImportError(f"skye.teams is planned, not available yet (no attribute {name!r})")
