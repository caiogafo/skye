# tools

What you learn: capabilities and MCP. Read in this order:

1. `mcp_fastmcp.py`: MCP client implementations: built-in vs ``fastmcp`` (Live, ``fastmcp`` branch guarded)
2. `mcp_prompts_and_resources.py`: MCP prompts and resources through the built-in client (Live, guarded where empty)
3. `registry.py`: Capability registry: register, discover and execute capabilities (Live)

Run: `python examples/tools/mcp_fastmcp.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
