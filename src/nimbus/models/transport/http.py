"""Minimal stdlib HTTP transport (``urllib.request`` + ``json``).

The implementation is pure standard library and lives in ``nimbus.base.http`` so that
``tools`` (which may import only ``base``) can share it; this module re-exports it.
"""

from __future__ import annotations

from nimbus.base import http as _impl

_build = _impl._build
_wrap = _impl._wrap
request_json = _impl.request_json
stream_lines = _impl.stream_lines

__all__ = ["_build", "_wrap", "request_json", "stream_lines"]
