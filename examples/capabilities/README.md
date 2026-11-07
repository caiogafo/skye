# capabilities

What you learn: capabilities. Read in this order:

1. `local_function.py`: Local Python functions as capabilities
2. `capability_agent.py`: A small agent on low-level capabilities: ask, run the calls the model requests, feed the results back, repeat
3. `mcp_client.py`: MCP client: list and call the tools of an MCP server over HTTP
4. `mcp_server.py`: Use the tools of an MCP server as capabilities of a model (needs a running server)
5. `remote_api.py`: Remote HTTP APIs as capabilities

Run: `python examples/capabilities/local_function.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
