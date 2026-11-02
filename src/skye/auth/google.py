"""Non-interactive Google authenticators (standard library only).

Each class implements :class:`~skye.base.interfaces.authentication.AuthenticationInterface`:

- :class:`GoogleBearerAuth`: OAuth2 access token (explicit, from the environment, or from a
  user-supplied token provider callable).
- :class:`GoogleMetadataAuth`: token from the GCE / Cloud Run / GKE metadata server, cached
  until shortly before it expires.
- :class:`GoogleApiKeyAuth`: ``x-goog-api-key`` header.

:func:`resolve_google_auth` picks one. Service-account JWT signing (needs the ``rsa`` library)
and Workload Identity Federation belong to the authentication milestone and are not supported
yet.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from skye.base.exceptions import ProviderError
from skye.base.interfaces.authentication import AuthenticationInterface

METADATA_TOKEN_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
)
TOKEN_ENV_VARS = ("GOOGLE_OAUTH_ACCESS_TOKEN", "CLOUDSDK_AUTH_ACCESS_TOKEN")
API_KEY_ENV_VAR = "GOOGLE_API_KEY"
_EXPIRY_SKEW = 60.0


class GoogleAuthError(ProviderError):
    """Raised when no usable Google credentials can be obtained."""

    def __init__(self, message: str) -> None:
        super().__init__(message, provider="google")


class GoogleBearerAuth:
    """``Authorization: Bearer`` from a token string or a callable returning one."""

    def __init__(self, token: str | Callable[[], str] | None = None) -> None:
        self._token = token

    def _resolve(self) -> str:
        token = self._token
        if callable(token):
            token = token()
        if not token:
            for name in TOKEN_ENV_VARS:
                token = os.environ.get(name)
                if token:
                    break
        if not token:
            raise GoogleAuthError(
                "No Google access token: pass one or set " + " or ".join(TOKEN_ENV_VARS)
            )
        return token

    def apply(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> dict[str, str]:
        out = dict(headers)
        out["Authorization"] = f"Bearer {self._resolve()}"
        return out


class GoogleMetadataAuth:
    """Bearer token from the metadata server, cached until it is about to expire."""

    def __init__(
        self,
        url: str = METADATA_TOKEN_URL,
        timeout: float = 3.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = url
        self._timeout = timeout
        self._clock = clock
        self._token: str | None = None
        self._expires_at = 0.0
        self._lock = threading.Lock()

    def _fetch(self) -> tuple[str, float]:
        req = urllib.request.Request(self._url, headers={"Metadata-Flavor": "Google"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
        except (OSError, ValueError) as e:
            raise GoogleAuthError(f"Metadata server token request failed: {e}") from e
        try:
            return data["access_token"], float(data.get("expires_in", 300))
        except (KeyError, TypeError, ValueError) as e:
            raise GoogleAuthError("Metadata server returned an unexpected token response") from e

    def token(self) -> str:
        with self._lock:
            now = self._clock()
            if self._token is None or now >= self._expires_at - _EXPIRY_SKEW:
                token, ttl = self._fetch()
                self._token, self._expires_at = token, now + ttl
            return self._token

    def apply(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> dict[str, str]:
        out = dict(headers)
        out["Authorization"] = f"Bearer {self.token()}"
        return out


class GoogleApiKeyAuth:
    """``x-goog-api-key`` header."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get(API_KEY_ENV_VAR)
        if not key:
            raise GoogleAuthError(f"No Google API key: pass one or set {API_KEY_ENV_VAR}")
        self._key = key

    def apply(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> dict[str, str]:
        out = dict(headers)
        out["x-goog-api-key"] = self._key
        return out


def _metadata_server_available(timeout: float = 1.0) -> bool:
    req = urllib.request.Request(
        "http://metadata.google.internal/", headers={"Metadata-Flavor": "Google"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return resp.headers.get("Metadata-Flavor") == "Google"
    except OSError:
        return False


def resolve_google_auth(credentials: Any = None) -> AuthenticationInterface:
    """Pick an authenticator.

    Order: an :class:`AuthenticationInterface` or token string/callable passed explicitly, an
    access token in the environment, an API key in the environment, the metadata server.
    """
    if credentials is not None:
        if isinstance(credentials, AuthenticationInterface):
            return credentials
        if isinstance(credentials, str) or callable(credentials):
            return GoogleBearerAuth(credentials)
        raise GoogleAuthError(
            f"Unsupported credentials type {type(credentials).__name__}; pass an "
            "AuthenticationInterface, an access token or a token provider callable"
        )
    if any(os.environ.get(n) for n in TOKEN_ENV_VARS):
        return GoogleBearerAuth()
    if os.environ.get(API_KEY_ENV_VAR):
        return GoogleApiKeyAuth()
    if _metadata_server_available():
        return GoogleMetadataAuth()
    hint = ""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        hint = (
            " GOOGLE_APPLICATION_CREDENTIALS points at a service account file, but service "
            "account JWT and Workload Identity are not supported yet (authentication "
            "milestone); use an access token, e.g. GOOGLE_OAUTH_ACCESS_TOKEN from "
            "`gcloud auth print-access-token`."
        )
    raise GoogleAuthError("No Google credentials available." + hint)


__all__ = [
    "GoogleAuthError",
    "GoogleBearerAuth",
    "GoogleMetadataAuth",
    "GoogleApiKeyAuth",
    "resolve_google_auth",
    "METADATA_TOKEN_URL",
]
