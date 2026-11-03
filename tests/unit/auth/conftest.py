"""A fake HTTP server for the credential and token endpoints (standard library, no real network)."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest


@dataclass
class Seen:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes

    def form(self) -> dict[str, str]:
        from urllib.parse import parse_qsl

        return dict(parse_qsl(self.body.decode("utf-8")))

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8"))


@dataclass
class FakeServer:
    url: str
    seen: list[Seen] = field(default_factory=list)
    handler: Callable[[Seen], tuple[int, Any]] = lambda seen: (200, {})

    def respond(self, handler: Callable[[Seen], tuple[int, Any]]) -> None:
        self.handler = handler


@pytest.fixture
def server() -> Iterator[FakeServer]:
    fake = FakeServer(url="")

    class Handler(BaseHTTPRequestHandler):
        def _handle(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            seen = Seen(
                self.command,
                self.path,
                {k.lower(): v for k, v in self.headers.items()},
                self.rfile.read(length),
            )
            fake.seen.append(seen)
            status, payload = fake.handler(seen)
            raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        do_GET = do_POST = do_PUT = _handle

        def log_message(self, *args: Any) -> None:
            pass

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    fake.url = f"http://127.0.0.1:{httpd.server_port}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield fake
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _der(tag: int, content: bytes) -> bytes:
    n = len(content)
    head = bytes([n]) if n < 0x80 else bytes([0x82]) + n.to_bytes(2, "big")
    return bytes([tag]) + head + content


@pytest.fixture(scope="session")
def rsa_pem() -> dict[str, str]:
    """One RSA key as PKCS#1 and PKCS#8 PEM (generating it takes a moment, so once per session)."""
    import base64

    rsa = pytest.importorskip("rsa")
    _, private = rsa.newkeys(1024)
    pkcs1 = private.save_pkcs1().decode()
    algorithm = _der(0x30, bytes.fromhex("06092a864886f70d0101010500"))
    der8 = _der(0x30, _der(0x02, b"\x00") + algorithm + _der(0x04, private.save_pkcs1("DER")))
    pkcs8 = (
        "-----BEGIN PRIVATE KEY-----\n"
        + base64.encodebytes(der8).decode()
        + "-----END PRIVATE KEY-----\n"
    )
    return {"pkcs1": pkcs1, "pkcs8": pkcs8}


def jwt_parts(jwt: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """The decoded header and payload of a JWT."""
    import base64

    def decode(part: str) -> dict[str, Any]:
        return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))

    header, payload, _ = jwt.split(".")
    return decode(header), decode(payload)
