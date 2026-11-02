"""A fake ``urllib.request.urlopen`` that answers every provider the library talks to with a plausible reply.

The examples call real providers. To check that they still match the library without credentials or a network, the tests patch
``urllib.request.urlopen`` (which the whole standard-library transport uses) with this fake: it reads the URL and returns a body
in the shape of that provider's API (chat, streaming, embeddings, token endpoints).
"""

from __future__ import annotations

import io
import json
import struct
import urllib.error
import zlib
from typing import Any
from unittest.mock import patch

TEXT = "Paris is the capital of France."


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, status: int = 200, headers: dict[str, str] | None = None) -> None:
        super().__init__(body)
        self.status = status
        self.headers = headers or {"Content-Type": "application/json"}

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _sse(events: list[dict[str, Any]], done: bool = True) -> bytes:
    out = "".join(f"data: {json.dumps(e)}\n\n" for e in events)
    return (out + ("data: [DONE]\n\n" if done else "")).encode()


def _find_schema(node: Any) -> dict[str, Any]:
    """The JSON schema inside a `response_format`, wherever the adapter nests it."""
    if isinstance(node, dict):
        if "properties" in node:
            return node
        for value in node.values():
            found = _find_schema(value)
            if found:
                return found
    return {}


def _fill(schema: dict[str, Any], root: dict[str, Any] | None = None) -> Any:
    """A value that satisfies a simple JSON schema: strings, numbers, booleans, lists, objects and ``$ref`` to ``$defs``."""
    root = root or schema
    if "$ref" in schema:
        return _fill(root.get("$defs", {}).get(schema["$ref"].rsplit("/", 1)[-1], {}), root)
    kind = schema.get("type")
    if "properties" in schema or kind == "object":
        return {name: _fill(sub, root) for name, sub in schema.get("properties", {}).items()}
    if kind == "array":
        return [_fill(schema.get("items", {}), root)]
    if kind == "integer":
        return 1
    if kind == "number":
        return 0.5
    if kind == "boolean":
        return True
    if "enum" in schema:
        return schema["enum"][0]
    return "example"


def _openai_chat(payload: dict[str, Any]) -> bytes:
    model = payload.get("model", "gpt-4")
    if payload.get("stream"):
        words = TEXT.split(" ")
        events = [{"id": "c1", "created": 1700000000, "model": model, "choices": [{"index": 0, "delta": {"content": w + " "}, "finish_reason": None}]} for w in words]
        events.append({"id": "c1", "created": 1700000000, "model": model, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 9, "completion_tokens": 6, "total_tokens": 15}})
        return _sse(events)
    message: dict[str, Any] = {"role": "assistant", "content": TEXT}
    if payload.get("tools") and "weather" in json.dumps(payload.get("messages", [])).lower():
        tool = payload["tools"][0]
        name = tool.get("function", {}).get("name", "tool")
        message = {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": name, "arguments": "{\"location\": \"Paris\"}"}}]}
    if payload.get("response_format"):
        message["content"] = json.dumps(_fill(_find_schema(payload["response_format"])))
    return json.dumps({"id": "c1", "object": "chat.completion", "created": 1700000000, "model": model, "choices": [{"index": 0, "message": message, "finish_reason": "tool_calls" if message.get("tool_calls") else "stop"}], "usage": {"prompt_tokens": 9, "completion_tokens": 6, "total_tokens": 15}}).encode()


def _anthropic(payload: dict[str, Any]) -> bytes:
    if payload.get("stream"):
        events = [{"type": "message_start", "message": {"id": "m1", "model": payload.get("model", "claude"), "usage": {"input_tokens": 9, "output_tokens": 0}}},
                  {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
                  {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": TEXT}},
                  {"type": "content_block_stop", "index": 0},
                  {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 6}},
                  {"type": "message_stop"}]
        return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode()
    return json.dumps({"id": "m1", "type": "message", "role": "assistant", "model": payload.get("model", "claude"), "content": [{"type": "text", "text": TEXT}], "stop_reason": "end_turn", "usage": {"input_tokens": 9, "output_tokens": 6}}).encode()


def _eventstream_frame(event_type: str, payload: dict[str, Any]) -> bytes:
    """One AWS eventstream message (prelude, headers, JSON body, CRCs), as Bedrock streams a response."""

    def header(name: str, value: str) -> bytes:
        n, v = name.encode(), value.encode()
        return bytes([len(n)]) + n + b"\x07" + struct.pack(">H", len(v)) + v

    headers = header(":message-type", "event") + header(":event-type", event_type) + header(":content-type", "application/json")
    body = json.dumps(payload).encode()
    prelude = struct.pack(">II", 16 + len(headers) + len(body), len(headers))
    prelude += struct.pack(">I", zlib.crc32(prelude) & 0xFFFFFFFF)
    message = prelude + headers + body
    return message + struct.pack(">I", zlib.crc32(message) & 0xFFFFFFFF)


def _bedrock(url: str, payload: dict[str, Any]) -> bytes:
    if url.endswith("/converse-stream"):
        return b"".join(
            [
                _eventstream_frame("contentBlockDelta", {"contentBlockIndex": 0, "delta": {"text": TEXT}}),
                _eventstream_frame("messageStop", {"stopReason": "end_turn"}),
                _eventstream_frame("metadata", {"usage": {"inputTokens": 9, "outputTokens": 6, "totalTokens": 15}}),
            ]
        )
    if url.endswith("/invoke"):
        return json.dumps({"embedding": [0.1] * 8, "inputTextTokenCount": 3, "embeddingsByType": {"float": [0.1] * 8}}).encode()
    return json.dumps({"output": {"message": {"role": "assistant", "content": [{"text": TEXT}]}}, "stopReason": "end_turn", "usage": {"inputTokens": 9, "outputTokens": 6, "totalTokens": 15}, "metrics": {"latencyMs": 5}}).encode()


def _google(url: str, payload: dict[str, Any]) -> bytes:
    if ":predict" in url or ":embedContent" in url or ":batchEmbedContents" in url:
        return json.dumps({"predictions": [{"embeddings": {"values": [0.1] * 8}}], "embedding": {"values": [0.1] * 8}, "embeddings": [{"values": [0.1] * 8}]}).encode()
    body = {"candidates": [{"content": {"role": "model", "parts": [{"text": TEXT}]}, "finishReason": "STOP"}], "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 6, "totalTokenCount": 15}}
    if "streamGenerateContent" in url:
        return _sse([body], done=False)
    return json.dumps(body).encode()


def _embeddings_openai(payload: dict[str, Any]) -> bytes:
    inputs = payload.get("input", [""])
    n = len(inputs) if isinstance(inputs, list) else 1
    return json.dumps({"object": "list", "data": [{"object": "embedding", "index": i, "embedding": [0.1] * 8} for i in range(n)], "model": payload.get("model", "m"), "usage": {"prompt_tokens": 3, "total_tokens": 3}}).encode()


def answer(url: str, data: bytes | None) -> bytes:
    try:
        payload = json.loads(data) if data else {}
    except (ValueError, TypeError):
        payload = {}
    low = url.lower()
    if "oauth" in low or "/token" in low:
        return json.dumps({"access_token": "t", "token_type": "Bearer", "expires_in": 3600}).encode()
    if "bedrock" in low or "/converse" in low or low.endswith("/invoke"):
        return _bedrock(url, payload)
    if "anthropic" in low or "/v1/messages" in low:
        return _anthropic(payload)
    if "googleapis" in low or "generativelanguage" in low or "aiplatform" in low or ":generatecontent" in low or ":streamgeneratecontent" in low or ":predict" in low:
        return _google(url, payload)
    if "cohere" in low:
        return json.dumps({"id": "e1", "embeddings": {"float": [[0.1] * 8]}, "texts": ["x"], "meta": {"billed_units": {"input_tokens": 3}}}).encode()
    if "/embeddings" in low:
        return _embeddings_openai(payload)
    if "/chat/completions" in low:
        return _openai_chat(payload)
    if "/mcp" in low or payload.get("jsonrpc"):
        method = payload.get("method")
        result: dict[str, Any] = {}
        if method == "initialize":
            result = {"protocolVersion": "2025-03-26", "capabilities": {}, "serverInfo": {"name": "fake", "version": "1"}}
        elif method == "tools/list":
            result = {"tools": [{"name": "echo", "description": "Echo", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}]}
        elif method == "tools/call":
            result = {"content": [{"type": "text", "text": "ok"}]}
        return json.dumps({"jsonrpc": "2.0", "id": payload.get("id"), "result": result}).encode()
    return json.dumps({"ok": True}).encode()


def fake_urlopen(req: Any, timeout: float | None = None, **_: Any) -> FakeResponse:
    url = req.full_url if hasattr(req, "full_url") else str(req)
    if "169.254.169.254" in url or "metadata.google.internal" in url:
        raise urllib.error.URLError("no metadata service in tests")
    return FakeResponse(answer(url, getattr(req, "data", None)))


def patched():
    return patch("urllib.request.urlopen", fake_urlopen)
