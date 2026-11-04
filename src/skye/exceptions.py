"""The `SkyeError` hierarchy (public path of `skye.base.exceptions`).

The code lives in `skye.base.exceptions`; import from here (or from `skye` for the commonest names).
"""

from skye.base.exceptions import (
    CapabilityExecutionError,
    ConfigurationError,
    MissingExtraError,
    ProviderError,
    SkyeError,
    ValidationError,
)

__all__ = [
    "CapabilityExecutionError",
    "ConfigurationError",
    "MissingExtraError",
    "ProviderError",
    "SkyeError",
    "ValidationError",
]
