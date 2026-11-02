# Capability Examples

This directory contains examples demonstrating how to use capabilities (tools/functions) with Skye.

## What are Capabilities?

Capabilities are functions or tools that language models can invoke to perform actions. They enable models to:
- Call external APIs
- Execute computations
- Access databases
- Perform real-world actions

Skye uses the term "Capability" instead of "Tool" to better represent this concept.

## Examples

### `function_calling_example.py`
Demonstrates how to define and use capabilities with different providers.

**Topics covered:**
- Defining capabilities with JSON schema
- Handling capability calls from models
- Multi-turn conversations with capability results
- Provider-specific implementations (OpenAI, Anthropic, Bedrock)

**Run:**
```bash
python examples/capabilities/function_calling_example.py
```

### `local_function.py`
Using local Python functions as capabilities.

**Topics covered:**
- Wrapping Python functions as capabilities using the `@capability` decorator
- Automatic schema generation from function signatures
- Executing capabilities locally
- Returning results to the model
- Both synchronous and asynchronous functions
- Multi-turn conversations with capability results

**Run:**
```bash
python examples/capabilities/local_function.py
```

**Key Features:**
- `@capability` decorator for easy function wrapping
- Automatic type hint to JSON Schema conversion
- Support for both sync and async functions
- Automatic parameter validation

### `remote_api.py`
Calling remote HTTP APIs through capabilities.

**Topics covered:**
- Wrapping HTTP APIs as capabilities using `RemoteAPICapability`
- Handling different HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Custom headers and authentication
- Error handling and API responses
- Both synchronous and asynchronous execution
- Concurrent API calls

**Run:**
```bash
python examples/capabilities/remote_api.py
```

**Key Features:**
- Support for all HTTP methods
- Basic authentication support
- Custom headers configuration
- Configurable timeouts
- Automatic JSON parsing

### `mcp_server.py`
Using Model Context Protocol (MCP) servers as capabilities.

**Topics covered:**
- Overview of MCP (Model Context Protocol)
- Creating MCPCapability instances from MCP tool definitions
- Automatic schema conversion from MCP to Skye format
- Using MCP capabilities with language models
- Error handling and best practices
- Performance optimization with schema caching

**Run:**
```bash
python examples/capabilities/mcp_server.py
```

**Requirements:**
- FastMCP library: `pip install skyeai[mcp]` or `pip install fastmcp>=0.1.0`

**Key Features:**
- Automatic MCP to Skye schema conversion
- Schema caching for performance
- Support for complex MCP tool definitions
- OpenAPI-based tool support

## Running All Examples

```bash
# Run all capability examples
python examples/capabilities/function_calling_example.py
python examples/capabilities/local_function.py
python examples/capabilities/remote_api.py
python examples/capabilities/mcp_server.py
```

## Key Concepts

- **CapabilityInterface**: Interface for defining capabilities
- **CapabilityCall**: Represents a capability invocation request
- **CapabilityResult**: Represents the result of executing a capability
- **CapabilityCallHandler**: Handles capability execution
- **CapabilityRegistry**: Manages available capabilities

## Capability Definition

Capabilities are defined using JSON Schema:

```python
capability = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["location"]
        }
    }
}
```

## Provider Support

Capabilities work across all supported providers:
- **OpenAI**: Function calling
- **Anthropic**: Tool use
- **AWS Bedrock**: Tool use via Converse API
- **Azure OpenAI**: Function calling

Skye handles the differences transparently!

## Next Steps

After understanding capabilities, explore:
- `examples/providers/` - Provider-specific features
- `examples/routing/` - Load balancing with capabilities
- `examples/advanced/` - Advanced capability patterns

## MCP client

`mcp_client.py` lists and calls the tools of an MCP server with the built-in client (`create_mcp_client(url)`: standard library, JSON-RPC over HTTP, no extra to install). The optional `fastmcp` client is chosen only with `impl="fastmcp"` (extra `mcp`); `mcp_server.py` shows it. Set `MCP_SERVER_URL` to the server address.
