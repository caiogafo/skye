"""Dev-validated reference versions of the selectable vendor SDKs (Req 17.9, 18.6).

One small table, informational only: it is never a gate (Req 17.5). Importing this module
imports nothing. ``version=None`` means "not recorded yet" (the SDKs are in the dev dependency
group since task 15.2; these versions are the ones resolved and validated there); no mismatch
warning is emitted for an entry without a recorded version.
"""

from __future__ import annotations

from typing import NamedTuple


class SdkRef(NamedTuple):
    """The importable ``module``, its pip ``dist`` name, the owning Extra and the reference version."""

    module: str
    dist: str
    extra: str
    version: str | None


SDK_REFERENCE: dict[str, SdkRef] = {
    "mcp": SdkRef("fastmcp", "fastmcp", "tools", "4.1.4"),
    "openai": SdkRef("openai", "openai", "openai", "2.8.1"),
    "anthropic": SdkRef("anthropic", "anthropic", "anthropic", "0.73.0"),
    "bedrock": SdkRef("boto3", "boto3", "bedrock", "1.40.75"),
    "google": SdkRef("vertexai", "google-cloud-aiplatform", "google", "1.127.0"),
}

__all__ = ["SDK_REFERENCE", "SdkRef"]
