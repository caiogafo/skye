"""MCP client: list and call the tools of an MCP server over HTTP.

``create_mcp_client(target)`` returns the built-in client (standard library, JSON-RPC over HTTP, consume-only, no extra to install).
The optional ``fastmcp`` client is chosen only explicitly, with ``impl="fastmcp"`` (extra ``mcp``).

Set MCP_SERVER_URL to the address of a server (default: http://localhost:8000/mcp).
"""

import asyncio
import os

from skye.tools import create_mcp_client


async def main() -> None:
    url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
    client = create_mcp_client(url)  # impl="builtin" is the default

    tools = await client.list_tools()
    print(f"{len(tools)} tool(s) on {url}")
    for tool in tools:
        print(" -", tool.get_schema().name)

    if tools:
        result = await client.call_tool(tools[0].get_schema().name, {})
        print("result:", result)


if __name__ == "__main__":
    asyncio.run(main())
