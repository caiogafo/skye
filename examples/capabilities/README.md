# Capability Examples

This directory contains examples demonstrating how to use capabilities (tools/functions) with Nimbus.

## What are Capabilities?

Capabilities are functions or tools that language models can invoke to perform actions. They enable models to:
- Call external APIs
- Execute computations
- Access databases
- Perform real-world actions

Nimbus uses the term "Capability" instead of "Tool" to better represent this concept.

## Examples

### `function_calling_example.py`
Demonstrates how to define and use capabilities with different providers.

**Topics covered:**
- Defining capabilities with JSON schema
- Handling capability calls from models
- Multi-turn conversations with capability results
- Provider-specific implementations (OpenAI, Anthropic, Bedrock)

### `local_function.py`
Using local Python functions as capabilities.

**Topics covered:**
- Wrapping Python functions as capabilities
- Executing capabilities locally
- Returning results to the model

### `remote_api.py`
Calling remote APIs through capabilities.

**Topics covered:**
- Defining capabilities for external APIs
- Handling API responses
- Error handling

### `mcp_server.py`
Using Model Context Protocol (MCP) servers as capabilities.

**Topics covered:**
- Connecting to MCP servers
- Discovering available capabilities
- Executing MCP capabilities

## Running the Examples

```bash
# Run function calling example
python examples/capabilities/function_calling_example.py

# Run local function example
python examples/capabilities/local_function.py

# Run remote API example
python examples/capabilities/remote_api.py

# Run MCP server example
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

Nimbus handles the differences transparently!

## Next Steps

After understanding capabilities, explore:
- `examples/providers/` - Provider-specific features
- `examples/routing/` - Load balancing with capabilities
- `examples/advanced/` - Advanced capability patterns
