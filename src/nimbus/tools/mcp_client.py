"""Tri-faceted MCP client in ``tools``: tools, prompts and resources behind one Port (Req 19).

* :class:`MCPClientPort` is the one Port. :class:`BuiltinMCPClient` (stdlib JSON-RPC over
  stateless HTTP, built on ``nimbus.base.http``) and ``FastMCPClient``
  (``nimbus.tools.mcp_fastmcp``, lazily imported) both implement it and return the same
  Nimbus types: ``CapabilityInterface``
  objects for tools, ``prompts`` message objects for prompts, :class:`Resource` for resources.
* Protocol shapes are converted in exactly one place, ``nimbus.tools.mcp_boundary``.
* Selection: :func:`create_mcp_client` (``impl="builtin"`` by default, ``"fastmcp"`` opt-in).
  Env/config wiring is task 15.1.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import re
from abc import ABC, abstractmethod
from typing import Any

from nimbus.base import http
from nimbus.base.backend_select import select_impl
from nimbus.base.exceptions import ConfigurationError, ProviderError, ValidationError
from nimbus.base.messages import NimbusMessage
from nimbus.tools import mcp_boundary as boundary
from nimbus.tools.exceptions import CapabilityExecutionError
from nimbus.tools.interface import CapabilityInterface
from nimbus.tools.mcp_boundary import MCPPrompt
from nimbus.tools.mcp_resource import Resource
from nimbus.tools.schema import CapabilitySchema

PROTOCOL_VERSION = "2025-06-18"


class MCPClientPort(ABC):
    """The MCP client Port: three facets, identical Nimbus return types in every implementation."""

    # tools
    @abstractmethod
    async def list_tools(self) -> list[CapabilityInterface]: ...

    @abstractmethod
    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any: ...

    # prompts
    @abstractmethod
    async def list_prompts(self) -> list[MCPPrompt]: ...

    @abstractmethod
    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> list[NimbusMessage]: ...

    # resources
    @abstractmethod
    async def list_resources(self) -> list[Resource]: ...

    @abstractmethod
    async def read_resource(self, uri: str) -> Resource: ...


class MCPToolCapability(CapabilityInterface):
    """A Nimbus capability backed by a tool on an MCP server (executes through the client)."""

    def __init__(self, schema: CapabilitySchema, client: MCPClientPort) -> None:
        self._schema = schema
        self._client = client

    def get_schema(self) -> CapabilitySchema:
        return self._schema

    async def aexecute(self, **kwargs: Any) -> Any:
        return await self._client.call_tool(self._schema.name, kwargs)

    def execute(self, **kwargs: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.aexecute(**kwargs))
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, self.aexecute(**kwargs)).result()


def _tool_value(name: str, raw: Any) -> Any:
    result = boundary.to_tool_result(raw)
    if result.is_error:
        raise CapabilityExecutionError(
            f"MCP tool '{name}' reported an error: {result.value}", capability_name=name
        )
    return result.value


class _ToolsFacet:
    def _capabilities(self, raws: list[Any]) -> list[CapabilityInterface]:
        return [MCPToolCapability(boundary.to_tool_schema(r), self) for r in raws]  # type: ignore[arg-type]


class BuiltinMCPClient(_ToolsFacet, MCPClientPort):
    """Standard-library MCP client: JSON-RPC 2.0 over stateless HTTP POST (no session)."""

    def __init__(
        self, url: str, *, headers: dict[str, str] | None = None, timeout: float = 30.0
    ) -> None:
        if not isinstance(url, str) or not url.strip():
            raise ConfigurationError("MCP server url cannot be empty")
        self._url = url
        self._headers = {
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
            **(headers or {}),
        }
        self._timeout = timeout
        self._next_id = 0

    def _rpc(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self._next_id += 1
        rid = self._next_id
        body: dict[str, Any] = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            body["params"] = params
        resp = http.request(
            self._url,
            "POST",
            json_body=body,
            headers=self._headers,
            timeout=self._timeout,
            provider="mcp",
        )
        msg = _decode_response(resp.text, rid)
        if "error" in msg:
            err = msg["error"] if isinstance(msg["error"], dict) else {}
            raise ProviderError(
                f"MCP error on {method}: {err.get('message', msg['error'])}",
                provider="mcp",
                code=err.get("code"),
            )
        if "result" not in msg:
            raise ValidationError(
                f"MCP {method}: field 'result' is required but absent",
                field=f"{method}.result",
                value=msg,
            )
        return msg["result"]

    async def _list(self, method: str, key: str) -> list[Any]:
        items: list[Any] = []
        cursor: str | None = None
        while True:
            result = await asyncio.to_thread(
                self._rpc, method, {"cursor": cursor} if cursor else None
            )
            page = result.get(key) if isinstance(result, dict) else None
            if not isinstance(page, list):
                raise ValidationError(
                    f"MCP {method}: field '{key}' must be a list",
                    field=f"{method}.{key}",
                    value=page,
                )
            items += page
            cursor = result.get("nextCursor")
            if not cursor:
                return items

    async def list_tools(self) -> list[CapabilityInterface]:
        return self._capabilities(await self._list("tools/list", "tools"))

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        raw = await asyncio.to_thread(
            self._rpc, "tools/call", {"name": name, "arguments": arguments or {}}
        )
        return _tool_value(name, raw)

    async def list_prompts(self) -> list[MCPPrompt]:
        return [boundary.to_prompt(r) for r in await self._list("prompts/list", "prompts")]

    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> list[NimbusMessage]:
        raw = await asyncio.to_thread(
            self._rpc, "prompts/get", {"name": name, "arguments": arguments or {}}
        )
        return boundary.to_prompt_messages(raw)

    async def list_resources(self) -> list[Resource]:
        return [boundary.to_resource(r) for r in await self._list("resources/list", "resources")]

    async def read_resource(self, uri: str) -> Resource:
        raw = await asyncio.to_thread(self._rpc, "resources/read", {"uri": uri})
        return boundary.to_read_resource(raw)


def _decode_response(text: str, rid: int) -> dict[str, Any]:
    """Body of a JSON-RPC reply: plain JSON, or an SSE stream carrying the reply with our id."""
    stripped = text.lstrip()
    try:
        if stripped.startswith(("event:", "data:", ":")):
            for block in re.split(r"\r?\n\r?\n", stripped):
                data = "\n".join(
                    ln[5:].lstrip() for ln in block.splitlines() if ln.startswith("data:")
                )
                if not data:
                    continue
                msg = json.loads(data)
                if isinstance(msg, dict) and msg.get("id") == rid:
                    return msg
            raise ValueError(f"no reply with id {rid} in event stream")
        msg = json.loads(stripped)
    except ValueError as e:
        raise ProviderError(f"MCP: malformed JSON-RPC response: {e}", provider="mcp") from e
    if not isinstance(msg, dict):
        raise ProviderError("MCP: JSON-RPC response must be an object", provider="mcp")
    return msg


IMPLEMENTATIONS = ("builtin", "fastmcp")


def create_mcp_client(
    target: Any,
    *,
    impl: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> MCPClientPort:
    """Build the MCP client for ``target`` (URL, or anything fastmcp accepts).

    ``impl=None`` (default) selects once via ``NIMBUS_MCP_IMPL`` / ``nimbus.yaml`` (``builtin`` |
    ``sdk``, builtin when unspecified; ``sdk`` means fastmcp, with a warning and built-in fallback
    if it cannot be imported). An explicit ``impl="builtin"|"fastmcp"|"sdk"`` argument is a
    code-level choice: it overrides env/config and never falls back (a missing fastmcp raises
    ``MissingExtraError``).
    """
    if impl is None:
        impl = "fastmcp" if select_impl("mcp").impl == "sdk" else "builtin"
    if impl == "builtin":
        return BuiltinMCPClient(target, headers=headers, timeout=timeout)
    if impl in ("fastmcp", "sdk"):
        from nimbus.tools.mcp_fastmcp import FastMCPClient

        return FastMCPClient(target, headers=headers, timeout=timeout)
    raise ConfigurationError(
        f"Unknown MCP client implementation {impl!r}; expected one of {IMPLEMENTATIONS}"
    )
