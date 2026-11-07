"""Use the tools of an MCP server as capabilities of a model (needs a running server).

Connect with FastMCP, list the server's tools, wrap each one as an ``MCPCapability``, hand them to the model, run the calls it asks for
and send the results back. Set MCP_SERVER_URL (for example http://localhost:8000/sse) and install ``pip install skyeai[mcp]``. Without a
server the example says how to start one and stops. With OPENAI_API_KEY set the model is real, otherwise a scripted client answers.
"""

import asyncio
import os
import sys
from pathlib import Path

from skye import UserMessage
from skye.tools import MCPCapability

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402

SERVER_URL = os.getenv("MCP_SERVER_URL")


async def main() -> None:
    if not SERVER_URL:
        print("MCP_SERVER_URL not set: start an MCP server and set its address, then run again")
        return
    try:
        from fastmcp import Client
    except ImportError:
        print("FastMCP is not installed: pip install skyeai[mcp]")
        return

    model = get_client("openai")
    question = [UserMessage(content="Use the available tools to help me")]
    try:
        async with Client(SERVER_URL) as mcp:
            tools = await mcp.list_tools()
            print(f"{len(tools)} tool(s):", ", ".join(tool["name"] for tool in tools))
            capabilities = [MCPCapability(mcp_tool=tool, server_name="mcp_server", cache_schema=True) for tool in tools]

            response = model.complete(messages=question, model="gpt-4", capabilities=capabilities)
            if not response.has_capability_calls():
                print(response.content)
                return
            for call in response.capability_calls:
                print(f"the model asks for: {call.name}({call.arguments})")
            results = await response.aexecute_capability_calls()
            final = model.complete(messages=[*question, response.to_message(), *results], model="gpt-4", capabilities=capabilities)
            print(final.content)
    except OSError as error:
        print(f"Could not reach the MCP server at {SERVER_URL}: {error}")


if __name__ == "__main__":
    asyncio.run(main())
