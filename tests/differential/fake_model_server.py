"""Local fake model server: the OpenAI, Anthropic and Bedrock wire formats over ``http.server`` in a thread.

Both the vendor SDK (pointed at it with a base URL) and the built-in REST adapter talk to it, so the two can be compared
without credentials or a network. The model name picks the behavior: ``auth-error`` answers 401, ``rate-limited`` answers 429,
anything else answers a short text with fixed token usage.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

TEXT = "Paris is the capital of France."
PROMPT_TOKENS, COMPLETION_TOKENS = 9, 6
ERRORS = {"auth-error": (401, "authentication_error"), "rate-limited": (429, "rate_limit_error")}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a: Any) -> None:
        pass

    def _send(self, code: int, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        self.server.requests.append({"path": self.path, "body": payload})  # type: ignore[attr-defined]
        path = self.path.split("?")[0]
        if path.endswith("/chat/completions"):
            self._openai(payload)
        elif path.endswith("/v1/messages"):
            self._anthropic(payload)
        elif path.endswith("/converse"):
            self._bedrock(path)
        else:
            self._send(404, {"error": "unknown path"})

    def _fail(self, model: str, shape: str) -> bool:
        if model not in ERRORS:
            return False
        code, kind = ERRORS[model]
        if shape == "openai":
            self._send(code, {"error": {"message": kind, "type": kind, "code": kind}})
        elif shape == "anthropic":
            self._send(code, {"type": "error", "error": {"type": kind, "message": kind}})
        else:
            self._send(code, {"message": kind, "__type": "ThrottlingException" if code == 429 else "UnrecognizedClientException"})
        return True

    def _openai(self, p: dict[str, Any]) -> None:
        if self._fail(p.get("model", ""), "openai"):
            return
        self._send(200, {
            "id": "chatcmpl-1", "object": "chat.completion", "created": 1700000000, "model": p["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": TEXT}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": PROMPT_TOKENS, "completion_tokens": COMPLETION_TOKENS, "total_tokens": PROMPT_TOKENS + COMPLETION_TOKENS},
        })

    def _anthropic(self, p: dict[str, Any]) -> None:
        if self._fail(p.get("model", ""), "anthropic"):
            return
        self._send(200, {
            "id": "msg_1", "type": "message", "role": "assistant", "model": p["model"],
            "content": [{"type": "text", "text": TEXT}], "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": PROMPT_TOKENS, "output_tokens": COMPLETION_TOKENS},
        })

    def _bedrock(self, path: str) -> None:
        model = path.split("/model/")[1].split("/")[0]
        if self._fail(model, "bedrock"):
            return
        self._send(200, {
            "output": {"message": {"role": "assistant", "content": [{"text": TEXT}]}},
            "stopReason": "end_turn", "metrics": {"latencyMs": 1},
            "usage": {"inputTokens": PROMPT_TOKENS, "outputTokens": COMPLETION_TOKENS, "totalTokens": PROMPT_TOKENS + COMPLETION_TOKENS},
        })


class FakeModelServer:
    """Start with ``with FakeModelServer() as s``; ``s.url`` is the base URL, ``s.requests`` what it received."""

    def __enter__(self) -> FakeModelServer:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server.requests = []  # type: ignore[attr-defined]
        self.requests: list[dict[str, Any]] = self._server.requests  # type: ignore[attr-defined]
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
