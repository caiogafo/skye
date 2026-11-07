"""Policy engine.

Component: policy. Layer: services (2). Declared-but-minimal; content belongs to the policy spec.

Codename: isobar.
"""

__all__: list[str] = []


def __getattr__(name: str) -> object:
    """Say that this package is planned, not available yet, instead of a bare AttributeError."""
    if name.startswith("_"):
        raise AttributeError(name)
    raise ImportError(f"skye.policy is planned, not available yet (no attribute {name!r})")
