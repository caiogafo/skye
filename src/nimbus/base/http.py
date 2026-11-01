"""Minimal stdlib HTTP helper (``urllib.request`` + ``json``), shared by ``models`` and ``tools``.

Pure standard library: no third-party import. ``models.transport.http`` re-exports the
JSON helpers; ``tools.remote_api`` uses :func:`request`.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from nimbus.base.exceptions import ProviderError


def _build(url: str, payload: Any, headers: dict[str, str] | None, method: str) -> urllib.request.Request:
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    return urllib.request.Request(url, data=body, headers=hdrs, method=method)


def _wrap(e: Exception, provider: str) -> ProviderError:
    if isinstance(e, urllib.error.HTTPError):
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")
        except Exception:  # pragma: no cover - best effort
            pass
        err = ProviderError(f"HTTP {e.code}: {detail or e.reason}", provider=provider, status_code=e.code)
    else:
        err = ProviderError(f"Transport error: {e}", provider=provider)
    err.__cause__ = e
    return err


def request_json(
    url: str,
    payload: Any = None,
    *,
    headers: dict[str, str] | None = None,
    method: str = "POST",
    timeout: float = 60.0,
    provider: str = "http",
) -> Any:
    """Send a JSON request and return the decoded JSON response."""
    req = _build(url, payload, headers, method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read()
    except (urllib.error.URLError, OSError) as e:
        raise _wrap(e, provider) from e
    return json.loads(raw.decode("utf-8")) if raw else None


def stream_lines(
    url: str,
    payload: Any = None,
    *,
    headers: dict[str, str] | None = None,
    method: str = "POST",
    timeout: float = 60.0,
    provider: str = "http",
) -> Iterator[bytes]:
    """Send a request and yield raw response lines (feed to ``parse_sse``)."""
    req = _build(url, payload, headers, method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)  # noqa: S310
    except (urllib.error.URLError, OSError) as e:
        raise _wrap(e, provider) from e
    with resp:
        yield from resp


@dataclass(frozen=True)
class HttpResponse:
    """Status code and decoded body of a completed request."""

    status_code: int
    text: str

    def json(self) -> Any:
        """Decode the body as JSON (raises ``ValueError`` when it is not JSON)."""
        return json.loads(self.text)


def request(
    url: str,
    method: str = "GET",
    *,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    headers: dict[str, str] | None = None,
    auth: tuple[str, str] | None = None,
    timeout: float = 30.0,
    provider: str = "http",
) -> HttpResponse:
    """Send a request (query ``params`` and/or a JSON body) and return the raw response.

    Raises :class:`ProviderError` (with ``status_code``) on an HTTP error status or a
    transport failure.
    """
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    hdrs = dict(headers or {})
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode("ascii")
        hdrs.setdefault("Authorization", f"Basic {token}")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            status = getattr(resp, "status", 200)
            text = resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        raise _wrap(e, provider) from e
    return HttpResponse(status_code=status, text=text)
