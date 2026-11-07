"""MCP gateway, toolset per operation.

Component: gateway. Layer: runtime (3). Declared-but-minimal; content belongs to the gateway spec.

Codename: horizon.
"""

__all__: list[str] = []


def __getattr__(name: str) -> object:
    """Say that this package is planned, not available yet, instead of a bare AttributeError."""
    if name.startswith("_"):
        raise AttributeError(name)
    raise ImportError(f"skye.gateway is planned, not available yet (no attribute {name!r})")
