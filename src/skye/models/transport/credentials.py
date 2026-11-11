"""The API key and the AWS region of a client: the one passed, or the standard environment variable.

The key variables are the ones ``skye.auth`` fixes (D18, Requirement 11.6): ``OPENAI_API_KEY``,
``ANTHROPIC_API_KEY``, ``COHERE_API_KEY``, ``AZURE_OPENAI_API_KEY``; never a prefixed variable. A
missing key or region raises ``ConfigurationError`` naming the variable, never a value.
"""

from __future__ import annotations

import os
from typing import Any

from skye.base.exceptions import ConfigurationError

#: The standard AWS variables that name the region, in the order they are read.
AWS_REGION_VARIABLES = ("AWS_REGION", "AWS_DEFAULT_REGION")


def resolve_api_key(api_key: str | None, env_var: str | None) -> str:
    """The key to use: ``api_key`` when given, else the value of ``env_var``.

    Args:
        api_key: The key passed by the caller, or ``None``.
        env_var: The provider-standard variable, or ``None`` when the provider has none (the key
            must be passed).

    Returns:
        The key.

    Raises:
        ConfigurationError: Neither is set; the message names the variable.
    """
    if api_key:
        return api_key
    if env_var:
        key = os.environ.get(env_var)
        if key:
            return key
        raise ConfigurationError(
            f"No API key: pass api_key or set {env_var}", details={"variable": env_var}
        )
    raise ConfigurationError("No API key: pass api_key", details={"variable": None})


def resolve_aws_region(region: str | None, authenticator: Any = None) -> str:
    """The AWS region: the one given, the authenticator's ``region``, then the standard variables.

    The variables are ``AWS_REGION``, then ``AWS_DEFAULT_REGION``.

    Raises:
        ConfigurationError: None is set; the message names the variables (no silent default).
    """
    if region:
        return region
    from_auth = getattr(authenticator, "region", None)
    if isinstance(from_auth, str) and from_auth:
        return from_auth
    for name in AWS_REGION_VARIABLES:
        value = os.environ.get(name)
        if value:
            return value
    raise ConfigurationError(
        "No AWS region: pass region_name (or region) or set AWS_REGION or AWS_DEFAULT_REGION",
        details={"variable": "AWS_REGION"},
    )


__all__ = ["AWS_REGION_VARIABLES", "resolve_api_key", "resolve_aws_region"]
