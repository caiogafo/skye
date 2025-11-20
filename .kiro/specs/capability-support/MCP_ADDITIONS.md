# MCP (Model Context Protocol) Support - Additions to Capability Support Spec

## Overview

This document summarizes the additions made to the Capability Support spec to include MCP (Model Context Protocol) support via the FastMCP library. MCP support is optional and defaults to tools (local functions or remote APIs with OpenAPI).

## Key Features Added

### 1. MCPCapability Class
- Wraps MCP server tools as Nimbus capabilities
- Automatic schema conversion from MCP format to CapabilitySchema
- Support for OpenAPI-based MCP tools
- Schema caching for performance optimization
- Lazy loading of FastMCP dependency

### 2. MCPServerClient Class
- Manages connections to MCP servers
- Loads tools from MCP servers
- Connection pooling and reuse
- Tool caching
- Auto-registration to CapabilityRegistry
- Support for both local and remote MCP servers

### 3. MCP Configuration in CompletionRequest
- Optional `mcp_servers` field for specifying MCP server configurations
- Support for multiple MCP servers in a single request
- Automatic tool loading and registration

## Requirements Added

### Requirement 12: MCP Support (New)

**User Story:** As a developer, I want to use MCP servers as capabilities, so that I can leverage existing MCP tools without rewriting them.

**Acceptance Criteria:**
1. Support loading tools from MCP servers via FastMCP library
2. Provide MCPCapability class for wrapping MCP tools
3. Automatically convert MCP tool schemas to Nimbus CapabilitySchema format
4. Support both local and remote MCP servers
5. Make FastMCP an optional dependency (not required for base functionality)
6. Provide helpful error messages when FastMCP is not installed
7. Support OpenAPI-based MCP tools with automatic schema extraction
8. Cache MCP tool definitions to avoid repeated server calls

### Requirement 13: Documentation and Examples (Updated)

Added MCP-specific documentation requirements:
- Examples of using MCP servers as capabilities
- Documentation on how to set up and configure MCP servers

## Design Components Added

### MCPCapability
```python
class MCPCapability(CapabilityInterface):
    def __init__(
        self,
        mcp_tool: dict[str, Any],
        server_name: str | None = None,
        cache_schema: bool = True
    ):
        """Initialize with MCP tool definition."""
```

**Features:**
- Automatic schema conversion from MCP format
- Support for local and remote MCP servers
- OpenAPI-based tool support
- Schema caching for performance
- Lazy loading of FastMCP dependency
- Helpful error messages if FastMCP not installed

### MCPServerClient
```python
class MCPServerClient:
    def __init__(
        self,
        server_name: str,
        server_config: dict[str, Any],
        auto_register: bool = False
    ):
        """Initialize MCP server client."""
```

**Features:**
- Connection pooling and reuse
- Tool caching
- Auto-registration to CapabilityRegistry
- Support for multiple MCP servers
- Async context manager support

## Implementation Tasks Added

### Task 17: Implement MCP Support (3 subtasks)

1. **17.1 Create MCPCapability class**
   - Implement MCP tool wrapping
   - Schema conversion from MCP to CapabilitySchema
   - Lazy loading of FastMCP
   - Error handling for missing FastMCP

2. **17.2 Create MCPServerClient class**
   - Implement MCP server connection management
   - Tool loading and caching
   - Auto-registration support
   - Connection pooling

3. **17.3 Add MCP configuration support**
   - Extend CompletionRequest with mcp_servers field
   - Implement MCP server discovery
   - Support multiple MCP servers

## Optional Dependencies

### Installation Options

```bash
# Base capabilities (local functions, remote APIs)
pip install nimbus

# With MCP support
pip install nimbus[mcp]

# All capabilities
pip install nimbus[capabilities]
```

### pyproject.toml Configuration

```toml
[project.optional-dependencies]
mcp = ["fastmcp>=0.1.0"]
capabilities = ["requests>=2.31", "httpx>=0.24", "fastmcp>=0.1.0"]
```

## MCP-Specific Implementation Notes

### FastMCP Lazy Loading
- Import FastMCP only when MCPCapability is instantiated
- Provide helpful error message if FastMCP not installed
- Error message suggests: `pip install nimbus[mcp]`

### MCP Tool Schema Conversion
- Convert MCP tool format to CapabilitySchema
- Handle OpenAPI-based tool definitions
- Extract name, description, parameters from MCP format
- Map MCP parameter types to JSON Schema types

### MCP Server Configuration
- Support local MCP servers (stdio transport)
- Support remote MCP servers (SSE transport)
- Support server discovery and auto-registration
- Cache tool definitions to avoid repeated server calls

### MCP Tool Execution
- Execute MCP tools via FastMCP client
- Support both sync and async execution
- Handle MCP-specific error responses
- Preserve MCP tool metadata in results

### Default to Tools
- When MCP server provides tools, automatically wrap as MCPCapability
- Register tools in CapabilityRegistry with namespace (e.g., "mcp.server_name.tool_name")
- Support OpenAPI-based tools from MCP servers
- Support local function tools from MCP servers

## Integration with Existing Components

### CapabilityRegistry
- MCPCapability instances registered with namespace support
- Example: "mcp.weather_server.get_current_weather"
- Supports discovery of MCP tools alongside local functions and remote APIs

### ToolTransformer
- Handles MCPCapability conversion to provider-specific formats
- Converts MCP schemas to OpenAI, Anthropic, Bedrock, Azure, Vertex formats

### ToolCallHandler
- Executes MCPCapability instances
- Handles MCP-specific tool call formats
- Returns results in provider-compatible format

### CompletionRequest/Response
- Optional mcp_servers field for MCP configuration
- Automatic tool loading from MCP servers
- Tool calls from MCP tools handled same as local/remote tools

## Testing Strategy

### Unit Tests
- Mock FastMCP to avoid dependency requirement
- Test schema conversion from MCP format
- Test tool execution
- Test error handling when FastMCP not installed
- Test connection management and caching

### Integration Tests (Optional)
- Test with real MCP servers
- Test tool loading and execution
- Test auto-registration
- Test multiple MCP servers

## Backward Compatibility

- MCP support is completely optional
- No breaking changes to existing capability APIs
- FastMCP is lazy-loaded only when needed
- Helpful error messages guide users to install FastMCP if needed

## Future Enhancements

1. Support for MCP resources (not just tools)
2. MCP server discovery and auto-configuration
3. MCP server health monitoring
4. MCP tool versioning and updates
5. MCP server authentication and authorization
6. MCP server performance metrics

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Library](https://github.com/jlowin/fastmcp)
- [OpenAPI Specification](https://spec.openapis.org/)
