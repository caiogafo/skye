"""AWS authentication on the standard library: SigV4, Bedrock API keys, credential sources.

Credential sources, in order: explicit arguments, environment variables, a named profile's
static keys in ``~/.aws/credentials``, the ECS/container credentials endpoint, EC2 instance
metadata (IMDSv2). Profiles with SSO or assume-role are out of scope. Imports only ``base``.
"""

from __future__ import annotations

import configparser
import datetime as _dt
import json
import os
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from skye.auth.sigv4 import sign_request
from skye.base import http
from skye.base.exceptions import ConfigurationError

_IMDS = "http://169.254.169.254"
_ECS_HOST = "http://169.254.170.2"
_REFRESH_MARGIN = _dt.timedelta(minutes=5)


@dataclass(frozen=True)
class AwsCredentials:
    """A resolved AWS credential set; ``expires_at`` is None for static keys."""

    access_key: str
    secret_key: str
    session_token: str | None = None
    expires_at: _dt.datetime | None = None

    def expired(self, now: _dt.datetime | None = None) -> bool:
        """True when within the refresh margin of expiry."""
        if self.expires_at is None:
            return False
        return (now or _dt.datetime.now(_dt.timezone.utc)) >= self.expires_at - _REFRESH_MARGIN


def _parse_expiry(value: str | None) -> _dt.datetime | None:
    if not value:
        return None
    return _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _from_json(data: Mapping[str, str]) -> AwsCredentials:
    return AwsCredentials(
        access_key=data["AccessKeyId"],
        secret_key=data["SecretAccessKey"],
        session_token=data.get("Token") or data.get("SessionToken"),
        expires_at=_parse_expiry(data.get("Expiration")),
    )


def _get(url: str, headers: dict[str, str] | None = None, method: str = "GET", timeout: float = 2.0) -> str:
    return http.send_bytes(url, None, headers=headers, method=method, timeout=timeout, provider="aws").decode("utf-8")


def _env_credentials(env: Mapping[str, str]) -> AwsCredentials | None:
    key, secret = env.get("AWS_ACCESS_KEY_ID"), env.get("AWS_SECRET_ACCESS_KEY")
    if key and secret:
        return AwsCredentials(key, secret, env.get("AWS_SESSION_TOKEN") or None)
    return None


def _profile_credentials(profile: str, env: Mapping[str, str]) -> AwsCredentials | None:
    path = Path(env.get("AWS_SHARED_CREDENTIALS_FILE") or Path.home() / ".aws" / "credentials")
    parser = configparser.ConfigParser()
    try:
        parser.read(path)
    except (OSError, configparser.Error):
        return None
    if not parser.has_section(profile):
        return None
    sect = parser[profile]
    key, secret = sect.get("aws_access_key_id"), sect.get("aws_secret_access_key")
    if key and secret:
        return AwsCredentials(key, secret, sect.get("aws_session_token"))
    return None


def _container_credentials(env: Mapping[str, str]) -> AwsCredentials | None:
    rel, full = env.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"), env.get("AWS_CONTAINER_CREDENTIALS_FULL_URI")
    if not (rel or full):
        return None
    url = full or f"{_ECS_HOST}{rel}"
    headers: dict[str, str] = {}
    token = env.get("AWS_CONTAINER_AUTHORIZATION_TOKEN")
    token_file = env.get("AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE")
    if not token and token_file:
        token = Path(token_file).read_text(encoding="utf-8").strip()
    if token:
        headers["Authorization"] = token
    return _from_json(json.loads(_get(url, headers)))


def _imds_credentials() -> AwsCredentials | None:
    try:
        token = _get(f"{_IMDS}/latest/api/token", {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}, "PUT")
        hdrs = {"X-aws-ec2-metadata-token": token}
        base = f"{_IMDS}/latest/meta-data/iam/security-credentials/"
        role = _get(base, hdrs).strip().splitlines()[0]
        return _from_json(json.loads(_get(base + role, hdrs)))
    except Exception:  # noqa: BLE001 - not on EC2: fall through to the "not found" error
        return None


class CredentialProvider:
    """Resolve credentials once and refresh them shortly before they expire."""

    def __init__(
        self,
        *,
        access_key: str | None = None,
        secret_key: str | None = None,
        session_token: str | None = None,
        profile_name: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._explicit = AwsCredentials(access_key, secret_key, session_token) if access_key and secret_key else None
        self._profile = profile_name
        self._env = env
        self._cached: AwsCredentials | None = None
        self._lock = threading.Lock()

    def get(self) -> AwsCredentials:
        """Return valid credentials, resolving or refreshing as needed."""
        with self._lock:
            if self._cached is None or self._cached.expired():
                self._cached = self._resolve()
            return self._cached

    def _resolve(self) -> AwsCredentials:
        if self._explicit:
            return self._explicit
        env = self._env if self._env is not None else os.environ
        found = _env_credentials(env)
        if not found and self._profile:
            found = _profile_credentials(self._profile, env)
            if not found:
                raise ConfigurationError(
                    f"AWS profile {self._profile!r} has no static keys in ~/.aws/credentials; "
                    "profiles using SSO or assume-role are not supported, pass explicit keys or use "
                    "environment variables, container or instance-role credentials"
                )
        found = found or _container_credentials(env) or _imds_credentials()
        if not found:
            raise ConfigurationError(
                "No AWS credentials found: pass access_key/secret_key, set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY, or run with a container or EC2 instance role"
            )
        return found


class SigV4Authenticator:
    """Authentication Port implementation that signs requests with SigV4."""

    def __init__(
        self,
        region: str,
        service: str,
        credentials: CredentialProvider | Callable[[], AwsCredentials] | AwsCredentials | None = None,
    ) -> None:
        self.region = region
        self.service = service
        if credentials is None:
            credentials = CredentialProvider()
        if isinstance(credentials, AwsCredentials):
            static = credentials
            self._get: Callable[[], AwsCredentials] = lambda: static
        elif isinstance(credentials, CredentialProvider):
            self._get = credentials.get
        else:
            self._get = credentials

    def apply(self, method: str, url: str, headers: Mapping[str, str], body: bytes = b"") -> dict[str, str]:
        creds = self._get()
        return sign_request(
            method,
            url,
            region=self.region,
            service=self.service,
            access_key=creds.access_key,
            secret_key=creds.secret_key,
            session_token=creds.session_token,
            headers=dict(headers),
            payload=body,
        )


class BedrockApiKeyAuthenticator:
    """Bearer-token authentication with a Bedrock API key (``AWS_BEARER_TOKEN_BEDROCK``)."""

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
        if not self._key:
            raise ConfigurationError("No Bedrock API key: pass api_key or set AWS_BEARER_TOKEN_BEDROCK")

    def apply(self, method: str, url: str, headers: Mapping[str, str], body: bytes = b"") -> dict[str, str]:
        return {**headers, "Authorization": f"Bearer {self._key}"}


def bedrock_authenticator(
    region: str,
    *,
    api_key: str | None = None,
    profile_name: str | None = None,
    access_key: str | None = None,
    secret_key: str | None = None,
    session_token: str | None = None,
) -> SigV4Authenticator | BedrockApiKeyAuthenticator:
    """API key when given or in the environment (and no explicit keys), else SigV4 (``bedrock``)."""
    if api_key or (not access_key and os.environ.get("AWS_BEARER_TOKEN_BEDROCK")):
        return BedrockApiKeyAuthenticator(api_key)
    provider = CredentialProvider(
        access_key=access_key, secret_key=secret_key, session_token=session_token, profile_name=profile_name
    )
    return SigV4Authenticator(region, "bedrock", provider)


__all__ = [
    "AwsCredentials",
    "CredentialProvider",
    "SigV4Authenticator",
    "BedrockApiKeyAuthenticator",
    "bedrock_authenticator",
]
