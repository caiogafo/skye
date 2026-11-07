"""Sequence units into a defined order of steps.

Component: flows. Layer: runtime (3). :class:`Flow` loads and checks a ``flow`` block of a ``.skye`` file; running it is not built
yet (spec ``3-runtime-flows``).

Codename: stream.
"""

from skye.flows.flow import Flow

__all__ = ["Flow"]


def __getattr__(name: str) -> object:
    """Say that a name is planned, not available yet, instead of a bare AttributeError."""
    if name.startswith("_"):
        raise AttributeError(name)
    raise ImportError(f"skye.flows has no attribute {name!r}; the flow runtime is planned, not available yet")
