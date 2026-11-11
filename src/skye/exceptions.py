"""The `SkyeError` hierarchy (public path of `skye.base.exceptions`).

The code lives in `skye.base.exceptions`; import from here (or from `skye` for the commonest names).
"""

from skye.base.exceptions import (
    AuthenticationError,
    BadRequestError,
    CapabilityChoiceError,
    CapabilityExecutionError,
    ConfigurationError,
    ContentPolicyError,
    MissingExtraError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
    ServerError,
    SkyeError,
    UnsupportedModalityError,
    ValidationError,
)

__all__ = [
    "AuthenticationError",
    "BadRequestError",
    "CapabilityChoiceError",
    "CapabilityExecutionError",
    "ConfigurationError",
    "ContentPolicyError",
    "MissingExtraError",
    "ProviderError",
    "ProviderTimeoutError",
    "RateLimitError",
    "ServerError",
    "SkyeError",
    "UnsupportedModalityError",
    "ValidationError",
]
