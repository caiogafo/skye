# Design Document: Capability Support

## Overview

The Capability Support feature provides a unified interface for registering, managing, and invoking tools/functions across different LLM providers. The design follows a provider-agnostic approach where capabilities are defined once and automatically converted to provider-specific formats. This enables developers to write agent code that works seamlessly across OpenAI, Anthropic, Bedrock, Azure, Vertex AI, and other providers.

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Developer Code                                                  │
│ - Define capabilities (local functions or remote APIs)          │
│ - Register in CapabilityRegistry                                │
│ - Pass to CompletionRequest                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Capability Management Layer                                     │
│ - CapabilityRegistry: Central registry for all capabilities     │
│ - CapabilitySchema: Unified schema definition                   │
│ - CapabilityInterface: Abstract interface for implementations   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Provider Transformation Layer                                   │
│ - ToolTransformer: Converts capabilities to provider formats    │
│ - Handles: OpenAI, Anthropic, Bedrock, Azure, Vertex, etc.     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Provider APIs                                                   │
│ - OpenAI: tools parameter with function calling format          │
│ - Anthropic: tools parameter with tool use format               │
│ - Bedrock: tools parameter in Converse API format               │
│ - Azure: tools parameter (OpenAI-compatible)                    │
│ - Vertex: tools parameter in Gemini format                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tool Call Processing                                            │
│ - Parse tool calls from provider responses                      │
│ - Validate against registered capabilities                      │
│ - Execute capabilities (local or remote)                        │
│ - Return results in provider-compatible format                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. CapabilitySchema (Pydantic Model)

Defines the structure of a capability with JSON Schema support.

```python
class CapabilitySchema(BaseModel):
    name: str                           # Unique capability name
    description: str                    # Human-readable description
    parameters: dict[str, Any]          # JSON Schema for parameters
    returns: dict[str, Any]             # JSON Schema for return type
```

**Key Features:**
- Immutable (frozen=True) for safety
- Validates non-empty name and description
- Supports full JSON Schema specification
- Provider-agnostic format

### 2. CapabilityInterface (Abstract Base Class)

Defines the contract for all capability implementations.

```python
class CapabilityInterface(ABC):
    @abstractmethod
    def get_schema(self) -> CapabilitySchema:
        """Return capability schema for LLM function calling."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute capability synchronously."""
        pass
    
    @abstractmethod
    async def aexecute(self, **kwargs: Any) -> Any:
        """Execute capability asynchronously."""
        pass
```

**Implementations:**
- `LocalFunctionCapability`: Wraps Python functions
- `RemoteAPICapability`: Wraps HTTP APIs
- Custom implementations for specialized use cases

### 3. CapabilityRegistry

Centralized registry for managing capabilities with namespace support.

```python
class CapabilityRegistry:
    def register(self, capability: CapabilityInterface) -> None:
        """Register a capability by name."""
        
    def get(self, name: str) -> CapabilityInterface | None:
        """Retrieve a capability by name."""
        
    def list_all(self) -> list[str]:
        """List all registered capability names."""
        
    def unregister(self, name: str) -> None:
        """Unregister a capability."""
```

**Features:**
- Namespace support (e.g., "weather.get_current", "database.query")
- Singleton pattern for global registry
- Thread-safe operations
- Validation on registration

### 4. ToolTransformer

Converts capabilities to provider-specific formats.

```python
class ToolTransformer:
    @staticmethod
    def to_openai_format(capabilities: list[CapabilityInterface]) -> list[dict]:
        """Convert to OpenAI function calling format."""
        
    @staticmethod
    def to_anthropic_format(capabilities: list[CapabilityInterface]) -> list[dict]:
        """Convert to Anthropic tool use format."""
        
    @staticmethod
    def to_bedrock_format(capabilities: list[CapabilityInterface]) -> list[dict]:
        """Convert to Bedrock Converse API format."""
        
    @staticmethod
    def to_vertex_format(capabilities: list[CapabilityInterface]) -> list[dict]:
        """Convert to Vertex AI Gemini format."""
```

**Provider-Specific Differences:**

| Provider | Format | Key Differences |
|----------|--------|-----------------|
| OpenAI | `{"type": "function", "function": {...}}` | Standard JSON Schema, supports parallel calls |
| Anthropic | `{"name": "...", "description": "...", "input_schema": {...}}` | Separate input_schema, tool use format |
| Bedrock | `{"toolSpec": {"name": "...", "description": "...", "inputSchema": {...}}}` | Nested toolSpec, inputSchema format |
| Azure | Same as OpenAI | OpenAI-compatible format |
| Vertex | `{"name": "...", "description": "...", "parameters": {...}}` | Gemini-specific format |

### 5. LocalFunctionCapability

Wraps Python functions as capabilities.

```python
class LocalFunctionCapability(CapabilityInterface):
    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
        schema_override: CapabilitySchema | None = None
    ):
        """Initialize with a Python function."""
        
    def get_schema(self) -> CapabilitySchema:
        """Extract schema from function signature."""
        
    def execute(self, **kwargs: Any) -> Any:
        """Call the function synchronously."""
        
    async def aexecute(self, **kwargs: Any) -> Any:
        """Call the function asynchronously."""
```

**Features:**
- Automatic schema extraction from type hints
- Support for both sync and async functions
- Custom schema override capability
- Argument validation against schema

### 6. RemoteAPICapability

Wraps HTTP APIs as capabilities.

```python
class RemoteAPICapability(CapabilityInterface):
    def __init__(
        self,
        name: str,
        description: str,
        url: str,
        method: str = "POST",
        schema: CapabilitySchema | None = None,
        headers: dict[str, str] | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float = 30.0
    ):
        """Initialize with HTTP API details."""
        
    def get_schema(self) -> CapabilitySchema:
        """Return the capability schema."""
        
    def execute(self, **kwargs: Any) -> Any:
        """Call the API synchronously."""
        
    async def aexecute(self, **kwargs: Any) -> Any:
        """Call the API asynchronously."""
```

**Features:**
- Support for GET, POST, PUT, DELETE, PATCH
- Authentication (basic auth, headers)
- Timeout configuration
- Error handling and retries
- Response parsing

### 7. MCPCapability (Optional - requires FastMCP)

Wraps MCP (Model Context Protocol) server tools as capabilities.

```python
class MCPCapability(CapabilityInterface):
    def __init__(
        self,
        mcp_tool: dict[str, Any],
        server_name: str | None = None,
        cache_schema: bool = True
    ):
        """Initialize with MCP tool definition."""
        
    def get_schema(self) -> CapabilitySchema:
        """Convert MCP tool schema to CapabilitySchema."""
        
    def execute(self, **kwargs: Any) -> Any:
        """Call the MCP tool synchronously."""
        
    async def aexecute(self, **kwargs: Any) -> Any:
        """Call the MCP tool asynchronously."""
```

**Features:**
- Automatic schema conversion from MCP format
- Support for local and remote MCP servers
- OpenAPI-based tool support
- Schema caching for performance
- Lazy loading of FastMCP dependency
- Helpful error messages if FastMCP not installed

### 8. MCPServerClient

Manages connections to MCP servers and loads tools.

```python
class MCPServerClient:
    def __init__(
        self,
        server_name: str,
        server_config: dict[str, Any],
        auto_register: bool = False
    ):
        """Initialize MCP server client."""
        
    async def load_tools(self) -> list[MCPCapability]:
        """Load all tools from MCP server."""
        
    async def get_tool(self, name: str) -> MCPCapability | None:
        """Get a specific tool by name."""
        
    async def close(self) -> None:
        """Close connection to MCP server."""
```

**Features:**
- Connection pooling and reuse
- Tool caching
- Auto-registration to CapabilityRegistry
- Support for multiple MCP servers
- Async context manager support

### 7. ToolCallHandler

Processes tool calls from provider responses.

```python
class ToolCallHandler:
    def __init__(self, registry: CapabilityRegistry):
        """Initialize with capability registry."""
        
    def parse_tool_calls(
        self,
        response: CompletionResponse,
        provider: str
    ) -> list[ToolCall]:
        """Parse tool calls from provider response."""
        
    async def execute_tool_calls(
        self,
        tool_calls: list[ToolCall]
    ) -> list[ToolResult]:
        """Execute tool calls and return results."""
        
    def format_tool_results(
        self,
        results: list[ToolResult],
        provider: str
    ) -> list[dict]:
        """Format results for sending back to provider."""
```

**Data Models:**

```python
class ToolCall(BaseModel):
    id: str                             # Tool call ID from provider
    name: str                           # Capability name
    arguments: dict[str, Any]           # Parsed arguments
    
class ToolResult(BaseModel):
    tool_call_id: str                   # Corresponding tool call ID
    name: str                           # Capability name
    result: Any                         # Execution result
    error: str | None = None            # Error message if failed
```

## Data Models

### CompletionRequest Extension

```python
class CompletionRequest(BaseModel):
    # ... existing fields ...
    capabilities: list[CapabilityInterface] | None = None
    tool_choice: str | None = None      # "auto", "required", or specific tool name
```

### CompletionResponse Extension

```python
class CompletionResponse(BaseModel):
    # ... existing fields ...
    tool_calls: list[ToolCall] | None = None
    
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        
    async def execute_tool_calls(
        self,
        registry: CapabilityRegistry
    ) -> list[ToolResult]:
        """Execute tool calls using registry."""
```

## Error Handling

### Custom Exceptions

```python
class CapabilityError(SkyeError):
    """Base exception for capability-related errors."""
    pass

class CapabilityNotFoundError(CapabilityError):
    """Raised when a requested capability is not registered."""
    pass

class CapabilityExecutionError(CapabilityError):
    """Raised when capability execution fails."""
    pass

class CapabilityValidationError(CapabilityError):
    """Raised when capability schema validation fails."""
    pass

class ToolCallParsingError(CapabilityError):
    """Raised when tool call parsing fails."""
    pass
```

### Error Handling Strategy

1. **Registration Validation**: Validate schema on registration
2. **Execution Validation**: Validate arguments before execution
3. **Error Wrapping**: Wrap execution errors with context
4. **Logging**: Log all errors with correlation IDs
5. **Observability**: Emit error events for monitoring

## Testing Strategy

### Unit Tests

1. **CapabilitySchema Tests**
   - Valid schema creation
   - Invalid schema rejection
   - JSON Schema validation

2. **LocalFunctionCapability Tests**
   - Schema extraction from type hints
   - Sync and async execution
   - Argument validation
   - Error handling

3. **RemoteAPICapability Tests**
   - HTTP request construction
   - Response parsing
   - Error handling
   - Timeout handling

4. **ToolTransformer Tests**
   - Conversion to each provider format
   - Schema translation accuracy
   - Edge case handling

5. **ToolCallHandler Tests**
   - Tool call parsing from each provider
   - Tool execution
   - Result formatting
   - Error handling

6. **CapabilityRegistry Tests**
   - Registration and retrieval
   - Namespace support
   - Duplicate detection
   - Thread safety

### Integration Tests

1. **End-to-End Flows**
   - Define capability → Register → Use with provider → Execute
   - Multiple tool calls in single response
   - Tool call failures and recovery

2. **Provider-Specific Tests**
   - OpenAI function calling
   - Anthropic tool use
   - Bedrock tool invocation
   - Azure tool calling
   - Vertex AI tool calling

3. **Agentic Loop Tests**
   - Multiple rounds of tool calls
   - Tool call chains
   - Error recovery

## Implementation Phases

### Phase 1: Core Infrastructure
- CapabilitySchema model
- CapabilityInterface abstract class
- CapabilityRegistry implementation
- Basic error handling

### Phase 2: Capability Implementations
- LocalFunctionCapability
- RemoteAPICapability
- Schema extraction utilities

### Phase 3: Provider Integration
- ToolTransformer for each provider
- Tool call parsing for each provider
- ToolCallHandler implementation

### Phase 4: CompletionRequest/Response Integration
- Extend CompletionRequest with capabilities
- Extend CompletionResponse with tool_calls
- Integration with existing providers

### Phase 5: Observability and Documentation
- Logging and event emission
- Examples and documentation
- Integration tests

## Key Design Decisions

### 1. Provider-Agnostic Schema
**Decision**: Use a unified schema format that's converted to provider-specific formats.
**Rationale**: Allows developers to define capabilities once and use across providers.
**Alternative**: Provider-specific schema definitions (rejected - too complex).

### 2. Registry Pattern
**Decision**: Use a centralized CapabilityRegistry for managing capabilities.
**Rationale**: Enables discovery, validation, and lifecycle management.
**Alternative**: Pass capabilities directly to requests (rejected - no discovery).

### 3. Separate Capability Classes
**Decision**: Create LocalFunctionCapability and RemoteAPICapability as separate classes.
**Rationale**: Each has different initialization and execution patterns.
**Alternative**: Single Capability class with type parameter (rejected - less clear).

### 4. Automatic Schema Extraction
**Decision**: Extract schema from function signatures for LocalFunctionCapability.
**Rationale**: Reduces boilerplate and keeps schema in sync with implementation.
**Alternative**: Require manual schema definition (rejected - error-prone).

### 5. Async Support
**Decision**: Provide both sync and async execution paths.
**Rationale**: Supports both blocking and non-blocking use cases.
**Alternative**: Async-only (rejected - breaks sync workflows).

## Security Considerations

1. **Input Validation**: All arguments validated against schema before execution
2. **API Key Management**: Support secure credential handling for remote APIs
3. **Timeout Protection**: Configurable timeouts prevent hanging requests
4. **Error Messages**: Sanitize error messages to avoid leaking sensitive info
5. **Audit Logging**: Log all tool calls for security auditing

## Performance Considerations

1. **Schema Caching**: Cache extracted schemas to avoid repeated introspection
2. **Lazy Loading**: Load remote API clients only when needed
3. **Parallel Execution**: Support parallel tool calls when provider allows
4. **Connection Pooling**: Reuse HTTP connections for remote APIs
5. **Batch Operations**: Support batch tool execution for efficiency

## Extensibility

1. **Custom Capability Classes**: Developers can extend CapabilityInterface
2. **Custom Transformers**: Support for new provider formats
3. **Custom Validators**: Pluggable validation logic
4. **Custom Executors**: Alternative execution strategies

## Migration Path

1. **Phase 1**: Introduce capability interfaces without breaking existing code
2. **Phase 2**: Add optional capabilities parameter to CompletionRequest
3. **Phase 3**: Integrate with existing providers
4. **Phase 4**: Deprecate old tool calling patterns (if any)
5. **Phase 5**: Full migration to new capability system
