"""AWS assume-role (including cross-account) and web identity over STS, on the standard library.

``AssumeRole`` is signed with the SigV4 signer of ``sigv4.py``; ``AssumeRoleWithWebIdentity`` holds
the OIDC token and is not signed. Responses are XML, read with ``xml.etree`` (no network access
beyond one POST to STS).
"""

from __future__ import annotations

import datetime as _dt
import urllib.parse
import xml.etree.ElementTree as ET
from collections.abc import Callable

from skye.auth.sigv4 import sign_request
from skye.base import http
from skye.base.exceptions import ProviderError

STS_VERSION = "2011-06-15"
_FORM = "application/x-www-form-urlencoded; charset=utf-8"


def _endpoint(region: str, endpoint: str | None) -> str:
    return endpoint or f"https://sts.{region}.amazonaws.com/"


def _parse(xml_text: str) -> tuple[str, str, str, _dt.datetime]:
    """The ``(access key, secret key, session token, expiry)`` of an STS response."""
    try:
        root = ET.fromstring(xml_text)
        node = next(el for el in root.iter() if el.tag.rsplit("}", 1)[-1] == "Credentials")

        def text(name: str) -> str:
            found = next(el for el in node if el.tag.rsplit("}", 1)[-1] == name)
            return (found.text or "").strip()

        expires = _dt.datetime.fromisoformat(text("Expiration").replace("Z", "+00:00"))
        return text("AccessKeyId"), text("SecretAccessKey"), text("SessionToken"), expires
    except (ET.ParseError, StopIteration, ValueError) as error:
        raise ProviderError("STS returned an unexpected response", provider="aws") from error


def assume_role(
    role_arn: str,
    *,
    access_key: str,
    secret_key: str,
    session_token: str | None = None,
    session_name: str = "skye",
    region: str = "us-east-1",
    external_id: str | None = None,
    duration: int = 3600,
    endpoint: str | None = None,
    timeout: float = 10.0,
) -> tuple[str, str, str, _dt.datetime]:
    """Call STS ``AssumeRole`` with the given (source) keys; the role may be in another account.

    Returns:
        ``(access key, secret key, session token, expiry)`` of the role session.
    """
    form = {
        "Action": "AssumeRole",
        "Version": STS_VERSION,
        "RoleArn": role_arn,
        "RoleSessionName": session_name,
        "DurationSeconds": str(duration),
    }
    if external_id:
        form["ExternalId"] = external_id
    body = urllib.parse.urlencode(form).encode("utf-8")
    url = _endpoint(region, endpoint)
    headers = sign_request(
        "POST",
        url,
        region=region,
        service="sts",
        access_key=access_key,
        secret_key=secret_key,
        session_token=session_token,
        headers={"Content-Type": _FORM},
        payload=body,
    )
    raw = http.send_bytes(url, body, headers=headers, timeout=timeout, provider="aws")
    return _parse(raw.decode("utf-8"))


def assume_role_with_web_identity(
    role_arn: str,
    token: str | Callable[[], str],
    *,
    session_name: str = "skye",
    region: str = "us-east-1",
    duration: int = 3600,
    endpoint: str | None = None,
    timeout: float = 10.0,
) -> tuple[str, str, str, _dt.datetime]:
    """Call STS ``AssumeRoleWithWebIdentity`` with an OIDC token (read from a file by caller)."""
    form = {
        "Action": "AssumeRoleWithWebIdentity",
        "Version": STS_VERSION,
        "RoleArn": role_arn,
        "RoleSessionName": session_name,
        "WebIdentityToken": token() if callable(token) else token,
        "DurationSeconds": str(duration),
    }
    body = urllib.parse.urlencode(form).encode("utf-8")
    raw = http.send_bytes(
        _endpoint(region, endpoint),
        body,
        headers={"Content-Type": _FORM},
        timeout=timeout,
        provider="aws",
    )
    return _parse(raw.decode("utf-8"))
