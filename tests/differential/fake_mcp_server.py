"""Local fake MCP server: stdlib ``http.server`` in a thread, JSON-RPC over HTTP POST.

Stateless (no session id), enough for the built-in client and for the real ``fastmcp`` client
(``initialize`` handshake + ``notifications/initialized`` + the calls Skye makes).
"""

from __future__ import annotations

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

PROTOCOL = "2025-06-18"

TOOLS = [
    {
        "name": "add",
        "description": "Add two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
    },
    {"name": "echo", "description": "Echo text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}},
    {"name": "boom", "description": "Always fails", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "headers", "description": "Return the Authorization header received", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "timing", "description": "Return a measured duration", "inputSchema": {"type": "object", "properties": {}}},
]
PROMPTS = [
    {
        "name": "greet",
        "description": "Greeting prompt",
        "arguments": [{"name": "who", "description": "Whom to greet", "required": True}, {"name": "tone"}],
    }
]
RESOURCES = [
    {"uri": "file:///notes.txt", "name": "notes", "mimeType": "text/plain", "description": "Some notes"},
    {"uri": "file:///blob.bin", "name": "blob", "mimeType": "application/octet-stream"},
]
BLOB = b"\x00\x01\x02binary\xff"


def _text(s: str, **extra: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": s}], "isError": False, **extra}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a: Any) -> None:  # silence
        pass

    def _send(self, code: int, body: dict[str, Any] | None = None) -> None:
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        if body is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # no server-initiated SSE stream
        self._send(405)

    def do_DELETE(self) -> None:
        self._send(200)

    def do_POST(self) -> None:
        msg = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        self.server.seen.append({"method": msg.get("method"), "headers": dict(self.headers)})  # type: ignore[attr-defined]
        if "id" not in msg:  # notification
            return self._send(202)
        rid, method, p = msg["id"], msg["method"], msg.get("params") or {}
        try:
            result = self._dispatch(method, p)
        except KeyError as e:
            return self._send(200, {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": f"Unknown {e}"}})
        self._send(200, {"jsonrpc": "2.0", "id": rid, "result": result})

    def _dispatch(self, method: str, p: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            return {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
                "serverInfo": {"name": "fake", "version": "0"},
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": TOOLS}
        if method == "prompts/list":
            return {"prompts": PROMPTS}
        if method == "resources/list":
            return {"resources": RESOURCES}
        if method == "tools/call":
            name, args = p["name"], p.get("arguments") or {}
            if name == "add":
                total = args["a"] + args["b"]
                return _text(json.dumps({"result": total}), structuredContent={"result": total})
            if name == "echo":
                return _text(args.get("text", ""))
            if name == "boom":
                return {"content": [{"type": "text", "text": "kaboom"}], "isError": True}
            if name == "headers":
                return _text(self.headers.get("Authorization", ""))
            if name == "timing":
                return _text(json.dumps({"elapsed": 0.25}), structuredContent={"elapsed": 0.25})
            raise KeyError(name)
        if method == "prompts/get":
            if p["name"] != "greet":
                raise KeyError(p["name"])
            who = (p.get("arguments") or {}).get("who", "?")
            return {
                "description": "Greeting prompt",
                "messages": [
                    {"role": "user", "content": {"type": "text", "text": f"Say hello to {who}"}},
                    {"role": "assistant", "content": {"type": "text", "text": f"Hello {who}!"}},
                ],
            }
        if method == "resources/read":
            uri = p["uri"]
            if uri == "file:///notes.txt":
                return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": "hello notes"}]}
            if uri == "file:///blob.bin":
                return {"contents": [{"uri": uri, "mimeType": "application/octet-stream", "blob": base64.b64encode(BLOB).decode()}]}
            raise KeyError(uri)
        raise KeyError(method)


class FakeMCPServer:
    def __init__(self) -> None:
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._httpd.daemon_threads = True
        self._httpd.seen = []  # type: ignore[attr-defined]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def seen(self) -> list[dict[str, Any]]:
        return self._httpd.seen  # type: ignore[attr-defined,no-any-return]

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._httpd.server_address[1]}/mcp"

    def __enter__(self) -> "FakeMCPServer":
        self._thread.start()
        return self

    def __exit__(self, *a: Any) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
