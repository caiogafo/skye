"""REST helpers shared by the built-in model adapters (standard library only).

An adapter builds a JSON request dict, :func:`post_json` sends it (optionally authenticated
through an :class:`~skye.base.interfaces.authentication.AuthenticationInterface`) and returns
a :class:`JsonObject`; :func:`stream_sse_json` yields one :class:`JsonObject` per SSE event.
``JsonObject`` gives attribute access over decoded JSON so the response transformers read
``response.choices[0].message.content`` without a vendor SDK type.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from typing import Any

from skye.base import http
from skye.base.interfaces.authentication import AuthenticationInterface
from skye.models.transport.streaming import parse_sse


class JsonObject:
    """Read-only attribute view over decoded JSON (dict -> JsonObject, list -> list)."""

    __slots__ = ("_d",)

    def __init__(self, data: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_d", dict(data))

    def __getattr__(self, name: str) -> Any:
        try:
            return wrap(self._d[name])
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("JsonObject is read-only")

    def __getitem__(self, key: str) -> Any:
        return wrap(self._d[key])

    def __contains__(self, key: object) -> bool:
        return key in self._d

    def get(self, key: str, default: Any = None) -> Any:
        return wrap(self._d[key]) if key in self._d else default

    def to_dict(self) -> dict[str, Any]:
        """The underlying plain dict."""
        return self._d

    def __repr__(self) -> str:
        return f"JsonObject({self._d!r})"


def wrap(value: Any) -> Any:
    """Wrap dicts as :class:`JsonObject` and lists element-wise; leave scalars alone."""
    if isinstance(value, dict):
        return JsonObject(value)
    if isinstance(value, list):
        return [wrap(v) for v in value]
    return value


def prepare(
    method: str,
    url: str,
    payload: Any,
    headers: Mapping[str, str] | None,
    authenticator: AuthenticationInterface | None,
) -> tuple[bytes, dict[str, str]]:
    """Serialise ``payload`` once and return ``(body, headers)``, authenticated when asked."""
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload is not None else b""
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    if authenticator is not None:
        hdrs = authenticator.apply(method, url, hdrs, body)
    return body, hdrs


def post_json(
    url: str,
    payload: Any,
    *,
    headers: Mapping[str, str] | None = None,
    authenticator: AuthenticationInterface | None = None,
    timeout: float = 60.0,
    provider: str = "http",
) -> JsonObject:
    """POST a JSON body, return the decoded JSON response as a :class:`JsonObject`."""
    body, hdrs = prepare("POST", url, payload, headers, authenticator)
    raw = http.send_bytes(url, body, headers=hdrs, method="POST", timeout=timeout, provider=provider)
    return JsonObject(json.loads(raw.decode("utf-8")) if raw else {})


def stream_sse_json(
    url: str,
    payload: Any,
    *,
    headers: Mapping[str, str] | None = None,
    authenticator: AuthenticationInterface | None = None,
    timeout: float = 60.0,
    provider: str = "http",
    done_marker: str = "[DONE]",
) -> Iterator[JsonObject]:
    """POST and yield each SSE ``data`` payload decoded as JSON (stops at ``done_marker``)."""
    body, hdrs = prepare("POST", url, payload, headers, authenticator)
    resp = http.open_stream(url, body, headers=hdrs, method="POST", timeout=timeout, provider=provider)
    with resp:
        for event in parse_sse(resp):
            if event.data == done_marker:
                return
            yield JsonObject(json.loads(event.data))


__all__ = ["JsonObject", "wrap", "prepare", "post_json", "stream_sse_json"]
