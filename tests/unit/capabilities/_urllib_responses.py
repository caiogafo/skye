"""Tiny stand-in for the ``responses`` library, mocking ``urllib.request.urlopen``.

RemoteAPICapability uses the stdlib transport, which ``responses`` (a ``requests`` mock)
cannot intercept. Only the subset used by the remote API tests is implemented:
``activate``, ``add``, ``add_callback``, ``calls`` and the method constants.
"""

from __future__ import annotations

import functools
import io
import json as _json
import urllib.error
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

GET, POST, PUT, DELETE, PATCH = "GET", "POST", "PUT", "DELETE", "PATCH"

_registry: list[dict[str, Any]] = []
calls: list[SimpleNamespace] = []


class _Headers(dict):
    def get(self, key: str, default: Any = None) -> Any:  # case-insensitive
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        return default

    def __contains__(self, key: object) -> bool:
        return any(k.lower() == str(key).lower() for k in self)


class _Resp(io.BytesIO):
    def __init__(self, body: bytes, status: int) -> None:
        super().__init__(body)
        self.status = status

    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def add(method: str, url: str, json: Any = None, body: str | None = None, status: int = 200, **_: Any) -> None:
    text = _json.dumps(json) if json is not None else (body or "")
    _registry.append({"method": method, "url": url, "response": (status, text)})


def add_callback(method: str, url: str, callback: Any, **_: Any) -> None:
    _registry.append({"method": method, "url": url, "callback": callback})


def _urlopen(req: Any, timeout: float | None = None) -> _Resp:
    full = req.full_url
    base = full.split("?", 1)[0]
    request = SimpleNamespace(url=full, body=req.data, headers=_Headers(req.header_items()), method=req.get_method())
    calls.append(SimpleNamespace(request=request))
    matches = [r for r in _registry if r["method"] == request.method and r["url"] == base]
    if not matches:
        raise urllib.error.URLError(f"no mocked response for {request.method} {full}")
    entry = matches[0]
    if len(matches) > 1:
        _registry.remove(entry)
    if "callback" in entry:
        status, _headers, text = entry["callback"](request)
    else:
        status, text = entry["response"]
    if status >= 400:
        raise urllib.error.HTTPError(full, status, "error", {}, io.BytesIO(text.encode()))  # type: ignore[arg-type]
    return _Resp(text.encode(), status)


def activate(fn: Any) -> Any:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _registry.clear()
        calls.clear()
        with patch("urllib.request.urlopen", _urlopen):
            return fn(*args, **kwargs)

    return wrapper
