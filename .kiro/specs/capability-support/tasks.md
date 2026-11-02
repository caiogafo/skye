# Implementation Plan: Capability Support

## Overview

This implementation plan breaks down the development of Capability Support into discrete, incremental tasks. The plan follows a bottom-up approach: core models first, then registry, then capability implementations, then provider integration, and finally observability.

## Task List

- [x] 1. Set up capability package structure
  - Create src/skye/capabilities/ directory structure
  - Create __init__.py files for all subdirectories
  - Create tests/unit/capabilities/ and tests/integration/capabilities/ directories
  - Update Makefile to include capability tests
  - _Requirements: 1.1, 1.2_

- [x] 2. Implement core capability models and interfaces
  - [x] 2.1 Create CapabilitySchema Pydantic model
    - Define name, description, parameters, returns fields
    - Add validation for non-empty name and description
    - Make model frozen (immutable) for safety
    - Write unit test in tests/unit/capabilities/test_capability_schema.py
    - Test valid schema creation
    - Test invalid schema rejection
    - Test JSON Schema validation
    - Run with `uv run pytest tests/unit/capabilities/test_capability_schema.py -v`
    - _Requirements: 1.1_
  
  - [x] 2.2 Create CapabilityInterface abstract class
    - Define abstract methods: get_schema(), execute(), aexecute()
    - Add docstrings with examples
    - Write unit test in tests/unit/capabilities/test_capability_interface.py
    - Create mock implementation for testing
    - Test interface compliance
    - Run with `uv run pytest tests/unit/capabilities/test_capability_interface.py -v`
    - _Requirements: 1.1, 1.5_

- [x] 3. Implement CapabilityRegistry
  - [x] 3.1 Create CapabilityRegistry class
    - Implement register() method with validation
    - Implement get() method with error handling
    - Implement list_all() method
    - Implement unregister() method
    - Support namespace support (e.g., "weather.get_current")
    - Implement as singleton pattern
    - Ensure thread-safe operations
    - Write unit test in tests/unit/capabilities/test_capability_registry.py
    - Test registration and retrieval
    - Test namespace support
    - Test duplicate detection
    - Test thread safety
    - Run with `uv run pytest tests/unit/capabilities/test_capability_registry.py -v`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4. Implement LocalFunctionCapability
  - [x] 4.1 Create LocalFunctionCapability class
    - Implement __init__ with function, name, description, schema_override
    - Implement get_schema() with automatic extraction from type hints
    - Implement execute() for sync function calls
    - Implement aexecute() for async function calls
    - Support both sync and async functions
    - Add argument validation against schema
    - Write unit test in tests/unit/capabilities/test_local_function_capability.py
    - Test schema extraction from type hints
    - Test sync and async execution
    - Test argument validation
    - Test error handling
    - Test custom schema override
    - Run with `uv run pytest tests/unit/capabilities/test_local_function_capability.py -v`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 5. Implement RemoteAPICapability
  - [x] 5.1 Create RemoteAPICapability class
    - Implement __init__ with URL, method, schema, headers, auth, timeout
    - Implement get_schema() method
    - Implement execute() for sync HTTP calls
    - Implement aexecute() for async HTTP calls
    - Support GET, POST, PUT, DELETE, PATCH methods
    - Support basic auth and custom headers
    - Add timeout configuration
    - Write unit test in tests/unit/capabilities/test_remote_api_capability.py
    - Mock HTTP requests using responses library
    - Test all HTTP methods
    - Test authentication
    - Test timeout handling
    - Test error handling
    - Test response parsing
    - Run with `uv run pytest tests/unit/capabilities/test_remote_api_capability.py -v`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6. Implement ToolTransformer for provider conversion
  - [x] 6.1 Create ToolTransformer class
    - Implement to_openai_format() for OpenAI function calling
    - Implement to_anthropic_format() for Anthropic tool use
    - Implement to_bedrock_format() for Bedrock Converse API
    - Implement to_azure_format() for Azure (OpenAI-compatible)
    - Implement to_vertex_format() for Vertex AI Gemini
    - Handle provider-specific schema differences
    - Write unit test in tests/unit/capabilities/test_tool_transformer.py
    - Test conversion to each provider format
    - Test schema translation accuracy
    - Test edge cases (empty parameters, complex types)
    - Run with `uv run pytest tests/unit/capabilities/test_tool_transformer.py -v`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. Implement ToolCall and ToolResult models
  - [x] 7.1 Create ToolCall and ToolResult Pydantic models
    - Define ToolCall with id, name, arguments fields
    - Define ToolResult with tool_call_id, name, result, error fields
    - Add validation for required fields
    - Write unit test in tests/unit/capabilities/test_tool_models.py
    - Test model creation and validation
    - Test serialization/deserialization
    - Run with `uv run pytest tests/unit/capabilities/test_tool_models.py -v`
    - _Requirements: 6.1, 6.2_

- [x] 8. Implement ToolCallHandler
  - [x] 8.1 Create ToolCallHandler class
    - Implement parse_tool_calls() for each provider format
    - Implement execute_tool_calls() for executing capabilities
    - Implement format_tool_results() for provider-specific formatting
    - Support parsing from OpenAI, Anthropic, Bedrock, Azure, Vertex responses
    - Add error handling for missing capabilities
    - Add validation of arguments against schema
    - Write unit test in tests/unit/capabilities/test_tool_call_handler.py
    - Mock provider responses
    - Test tool call parsing from each provider
    - Test tool execution
    - Test result formatting
    - Test error handling
    - Run with `uv run pytest tests/unit/capabilities/test_tool_call_handler.py -v`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 9. Implement custom exceptions
  - [x] 9.1 Create capability-specific exceptions
    - Create CapabilityError base class
    - Create CapabilityNotFoundError
    - Create CapabilityExecutionError
    - Create CapabilityValidationError
    - Create ToolCallParsingError
    - Add proper error context and messages
    - Write unit test in tests/unit/capabilities/test_exceptions.py
    - Test exception creation and messages
    - Test error context preservation
    - Run with `uv run pytest tests/unit/capabilities/test_exceptions.py -v`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 10. Extend CompletionRequest with capabilities
  - [x] 10.1 Update CompletionRequest model
    - Add capabilities field (optional list of CapabilityInterface)
    - Add tool_choice field (optional string: "auto", "required", or tool name)
    - Update docstring with examples
    - Write unit test in tests/unit/test_completion_models.py
    - Test capabilities field validation
    - Test tool_choice validation
    - Run with `uv run pytest tests/unit/test_completion_models.py::test_completion_request_capabilities -v`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 11. Extend CompletionResponse with tool calls
  - [x] 11.1 Update CompletionResponse model
    - Add tool_calls field (optional list of ToolCall)
    - Add has_tool_calls() method
    - Add execute_tool_calls() async method
    - Update docstring with examples
    - Write unit test in tests/unit/test_completion_models.py
    - Test tool_calls field validation
    - Test has_tool_calls() method
    - Test execute_tool_calls() method
    - Run with `uv run pytest tests/unit/test_completion_models.py::test_completion_response_tool_calls -v`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 12. Integrate capabilities with OpenAI provider
  - [x] 12.1 Update OpenAIProvider for tool support
    - Convert capabilities to OpenAI format in _transform_request()
    - Handle tool_choice parameter
    - Parse tool calls from response in _transform_response()
    - Support parallel tool calls
    - Write unit test in tests/unit/providers/test_openai_provider.py
    - Test capability conversion
    - Test tool call parsing
    - Test tool_choice handling
    - Run with `uv run pytest tests/unit/providers/test_openai_provider.py::test_tool_calling -v`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 13. Integrate capabilities with Anthropic provider
  - [x] 13.1 Update AnthropicProvider for tool support
    - Convert capabilities to Anthropic format in _transform_request()
    - Handle tool_choice parameter
    - Parse tool use from response in _transform_response()
    - Write unit test in tests/unit/providers/test_anthropic_provider.py
    - Test capability conversion to Anthropic format
    - Test tool use parsing
    - Test tool_choice handling
    - Run with `uv run pytest tests/unit/providers/test_anthropic_provider.py::test_tool_calling -v`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 14. Integrate capabilities with Bedrock provider
  - [x] 14.1 Update BedrockProvider for tool support
    - Convert capabilities to Bedrock format in _transform_request()
    - Handle tool_choice parameter
    - Parse tool calls from response in _transform_response()
    - Write unit test in tests/unit/providers/test_bedrock_provider.py
    - Test capability conversion to Bedrock format
    - Test tool call parsing
    - Test tool_choice handling
    - Run with `uv run pytest tests/unit/providers/test_bedrock_provider.py::test_tool_calling -v`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 15. Integrate capabilities with Azure provider
  - [x] 15.1 Update AzureOpenAIProvider for tool support
    - Convert capabilities to Azure format in _transform_request()
    - Handle tool_choice parameter
    - Parse tool calls from response in _transform_response()
    - Write unit test in tests/unit/providers/test_azure_provider.py
    - Test capability conversion
    - Test tool call parsing
    - Test tool_choice handling
    - Run with `uv run pytest tests/unit/providers/test_azure_provider.py::test_tool_calling -v`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 16. Integrate capabilities with Vertex provider
  - [x] 16.1 Update VertexAIProvider for tool support
    - Convert capabilities to Vertex format in _transform_request()
    - Handle tool_choice parameter
    - Parse tool calls from response in _transform_response()
    - Write unit test in tests/unit/providers/test_vertex_provider.py
    - Test capability conversion to Vertex format
    - Test tool call parsing
    - Test tool_choice handling
    - Run with `uv run pytest tests/unit/providers/test_vertex_provider.py::test_tool_calling -v`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 17. Implement MCP (Model Context Protocol) support
  - [x] 17.1 Create MCPCapability class (optional - requires FastMCP)
    - Implement __init__ with MCP tool definition
    - Implement get_schema() with MCP to CapabilitySchema conversion
    - Implement execute() for sync MCP tool calls
    - Implement aexecute() for async MCP tool calls
    - Support OpenAPI-based MCP tools
    - Add schema caching for performance
    - Implement lazy loading of FastMCP dependency
    - Add helpful error messages if FastMCP not installed
    - Write unit test in tests/unit/capabilities/test_mcp_capability.py
    - Mock FastMCP to avoid dependency requirement
    - Test schema conversion from MCP format
    - Test tool execution
    - Test error handling when FastMCP not installed
    - Run with `uv run pytest tests/unit/capabilities/test_mcp_capability.py -v`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_
  
  - [x] 17.2 Create MCPServerClient class
    - Implement __init__ with server configuration
    - Implement load_tools() to fetch tools from MCP server
    - Implement get_tool() to retrieve specific tool
    - Implement close() for cleanup
    - Support connection pooling and reuse
    - Implement tool caching
    - Support auto-registration to CapabilityRegistry
    - Support async context manager protocol
    - Write unit test in tests/unit/capabilities/test_mcp_server_client.py
    - Mock MCP server responses
    - Test tool loading and caching
    - Test auto-registration
    - Test connection management
    - Run with `uv run pytest tests/unit/capabilities/test_mcp_server_client.py -v`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [x] 17.3 Add MCP configuration support
    - Support MCP server configuration in CompletionRequest
    - Add mcp_servers field to CompletionRequest (optional)
    - Implement MCP server discovery and loading
    - Support multiple MCP servers in single request
    - Write unit test in tests/unit/test_completion_models.py
    - Test MCP server configuration
    - Test tool loading from MCP servers
    - Run with `uv run pytest tests/unit/test_completion_models.py::test_mcp_configuration -v`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 18. Implement observability and logging
  - [ ]* 17.1 Add logging to capability operations
    - Log capability registration
    - Log tool calls with arguments
    - Log tool execution results and latency
    - Log tool execution errors
    - Emit structured events for observability
    - Support correlation IDs
    - Write unit test in tests/unit/capabilities/test_observability.py
    - Test logging output
    - Test event emission
    - Test correlation ID tracking
    - Run with `uv run pytest tests/unit/capabilities/test_observability.py -v`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 18. Create capability package exports
  - [x] 18.1 Configure package exports
    - Export CapabilityInterface from skye.capabilities
    - Export CapabilitySchema from skye.capabilities
    - Export CapabilityRegistry from skye.capabilities
    - Export LocalFunctionCapability from skye.capabilities
    - Export RemoteAPICapability from skye.capabilities
    - Export ToolCall and ToolResult from skye.capabilities
    - Export all exception classes
    - Define __all__ in __init__.py
    - Write unit test in tests/unit/test_capability_exports.py
    - Test that all expected symbols are importable
    - Test that __all__ is properly defined
    - Run with `uv run pytest tests/unit/test_capability_exports.py -v`
    - Verify with `uv run python -c "from skye.capabilities import CapabilityInterface, CapabilityRegistry; print('OK')"`
    - _Requirements: 1.1, 1.2_

- [ ]* 20. Write comprehensive integration tests
  - [ ]* 20.1 Create end-to-end capability tests
    - Test defining capability → registering → using with provider → executing
    - Test multiple tool calls in single response
    - Test tool call failures and recovery
    - Test agentic loops with multiple rounds
    - Test tool call chains
    - Mark with pytest.mark.integration
    - Run with `uv run pytest tests/integration/capabilities/test_e2e.py -v -m integration`
    - _Requirements: All_
  
  - [ ]* 20.2 Create provider-specific integration tests
    - Test OpenAI tool calling with real API (requires API key)
    - Test Anthropic tool use with real API
    - Test Bedrock tool calling with real API
    - Test Azure tool calling with real API
    - Test Vertex AI tool calling with real API
    - Mark with pytest.mark.integration
    - Skip if API keys not available
    - Run with `uv run pytest tests/integration/capabilities/test_provider_integration.py -v -m integration`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 21. Write documentation and examples
  - [ ]* 21.1 Create capability documentation
    - Document CapabilityInterface and CapabilitySchema
    - Document LocalFunctionCapability usage
    - Document RemoteAPICapability usage
    - Document CapabilityRegistry usage
    - Document tool call handling
    - No unit test required (documentation)
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ]* 21.2 Create example scripts
    - Create examples/capabilities/local_function_example.py
    - Create examples/capabilities/remote_api_example.py
    - Create examples/capabilities/agentic_loop_example.py
    - Create examples/capabilities/multi_provider_example.py
    - Test that examples run with `uv run python examples/capabilities/local_function_example.py`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ]* 21.3 Add type hints verification
    - Run mypy on all capability code with `uv run mypy src/skye/capabilities --strict`
    - Fix any type hint issues
    - Add mypy to Makefile check target for capabilities
    - Create test script tests/test_capability_type_hints.sh
    - Run with `uv run mypy src/skye/capabilities --strict`
    - _Requirements: All_

## Implementation Notes

### UV Usage

All Python commands should be run using UV:
- **Testing**: `uv run pytest tests/unit/capabilities/ -v`
- **Integration tests**: `uv run pytest tests/integration/capabilities/ -v -m integration`
- **Type checking**: `uv run mypy src/skye/capabilities --strict`
- **Linting**: `uv run ruff check src/skye/capabilities tests/`
- **Formatting**: `uv run black src/skye/capabilities tests/`
- **Quick validation**: `uv run python -c "from skye.capabilities import CapabilityRegistry; print('OK')"`
- **Running examples**: `uv run python examples/capabilities/local_function_example.py`

### Testing Strategy

**Unit Tests (Required)**:
- Mock all external dependencies (HTTP calls, provider APIs)
- Test capability schema extraction and validation
- Test tool call parsing and execution
- Test error handling and edge cases
- Focus on transformation logic and error handling

**Integration Tests (Optional, marked with *)**:
- Require actual API keys for provider testing
- Test real tool calls with actual providers
- Skip if API keys not available
- Mark with `pytest.mark.integration`
- Run separately from unit tests

**Test Execution**:
```bash
# Run unit tests only
uv run pytest tests/unit/capabilities/ -v

# Run integration tests (requires API keys)
uv run pytest tests/integration/capabilities/ -v -m integration

# Run all tests
uv run pytest tests/ -v

# Run specific capability tests
uv run pytest tests/unit/capabilities/test_local_function_capability.py -v
```

### Environment Variables for Integration Tests

Integration tests require API keys:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export AWS_PROFILE="default"  # or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY
export AZURE_OPENAI_ENDPOINT="https://..."
export AZURE_OPENAI_API_KEY="..."
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Dependencies

**Base Dependencies** (always installed with skye):
- pydantic>=2.0
- pyyaml>=6.0

**Optional Dependencies for Capabilities**:
- requests>=2.31 (for RemoteAPICapability)
- httpx>=0.24 (for async RemoteAPICapability)
- fastmcp>=0.1.0 (for MCPCapability - optional, lazy loaded)

**Installation**:
```bash
# Base capabilities (local functions, remote APIs)
pip install skyeai

# With MCP support
pip install skyeai[mcp]

# All capabilities
pip install skyeai[capabilities]
```

**pyproject.toml Configuration**:
```toml
[project.optional-dependencies]
mcp = ["fastmcp>=0.1.0"]
capabilities = ["requests>=2.31", "httpx>=0.24", "fastmcp>=0.1.0"]
```

**Test Dependencies**:
- pytest>=7.0
- pytest-asyncio>=0.21
- responses>=0.23 (for mocking HTTP requests)

### Code Quality

- All code must have complete type hints
- All public APIs must have docstrings
- Follow PEP 8 style guidelines (enforced by black and ruff)
- Maintain test coverage above 80% for non-optional tests
- Run `uv run mypy src/skye/capabilities --strict` before committing
- Use `uv run black src/skye/capabilities tests/` to format code
- Use `uv run ruff check src/skye/capabilities tests/` to lint code

### Quick Validation Commands

After implementing each task, use these UV commands to validate:

```bash
# Import validation
uv run python -c "from skye.capabilities import CapabilityRegistry, CapabilityInterface; print('OK')"

# Type checking
uv run mypy src/skye/capabilities --strict

# Run tests
uv run pytest tests/unit/capabilities/ -v

# Code formatting
uv run black src/skye/capabilities tests/ --check

# Linting
uv run ruff check src/skye/capabilities tests/

# Full validation
uv run pytest tests/unit/capabilities/ && uv run mypy src/skye/capabilities --strict && uv run ruff check src/skye/capabilities tests/
```

### Task Dependencies

- Task 1 must complete before all other tasks
- Tasks 2-5 (core models and implementations) can be done in parallel after task 1
- Task 6 (ToolTransformer) depends on tasks 2-5
- Task 7 (ToolCall/ToolResult models) depends on task 2
- Task 8 (ToolCallHandler) depends on tasks 2-7
- Task 9 (exceptions) can be done in parallel with tasks 2-8
- Tasks 10-11 (CompletionRequest/Response extension) depend on tasks 2-9
- Tasks 12-16 (provider integration) depend on tasks 10-11
- Task 17 (observability) can be done alongside tasks 12-16
- Task 18 (exports) depends on all previous tasks
- Tasks 19-20 (integration tests and documentation) depend on all previous tasks

### Provider-Specific Implementation Notes

**OpenAI**:
- Use `tools` parameter with `{"type": "function", "function": {...}}` format
- Support `tool_choice` parameter ("auto", "required", or specific tool name)
- Parse `tool_calls` from response with `id`, `function.name`, `function.arguments`

**Anthropic**:
- Use `tools` parameter with `{"name": "...", "input_schema": {...}}` format
- Support `tool_choice` parameter
- Parse `tool_use` blocks from response with `id`, `name`, `input`

**Bedrock**:
- Use `tools` parameter in Converse API with `{"toolSpec": {...}}` format
- Parse `toolUseBlock` from response with `toolUseId`, `name`, `input`

**Azure**:
- Same as OpenAI (OpenAI-compatible format)
- Use `tools` parameter with function calling format

**Vertex AI**:
- Use `tools` parameter with Gemini format `{"name": "...", "parameters": {...}}`
- Parse `toolCalls` from response with `id`, `function`, `args`

### Schema Extraction for LocalFunctionCapability

When extracting schema from function signatures:
1. Use function name as capability name (or override)
2. Use function docstring as description
3. Extract parameters from function signature
4. Use type hints to build JSON Schema
5. Support complex types (dict, list, nested objects)
6. Handle optional parameters (default values)
7. Support Union types for multiple allowed types

### Error Handling Strategy

1. **Registration**: Validate schema on registration, raise CapabilityValidationError
2. **Execution**: Validate arguments before execution, raise CapabilityValidationError
3. **Not Found**: Raise CapabilityNotFoundError when capability not in registry
4. **Execution Failure**: Wrap execution errors in CapabilityExecutionError
5. **Parsing**: Raise ToolCallParsingError for invalid tool call format
6. **Logging**: Log all errors with correlation IDs for tracing

### MCP-Specific Implementation Notes

**FastMCP Lazy Loading**:
- Import FastMCP only when MCPCapability is instantiated
- Provide helpful error message if FastMCP not installed
- Error message should suggest: `pip install skyeai[mcp]`

**MCP Tool Schema Conversion**:
- Convert MCP tool format to CapabilitySchema
- Handle OpenAPI-based tool definitions
- Extract name, description, parameters from MCP format
- Map MCP parameter types to JSON Schema types

**MCP Server Configuration**:
- Support local MCP servers (stdio transport)
- Support remote MCP servers (SSE transport)
- Support server discovery and auto-registration
- Cache tool definitions to avoid repeated server calls

**MCP Tool Execution**:
- Execute MCP tools via FastMCP client
- Support both sync and async execution
- Handle MCP-specific error responses
- Preserve MCP tool metadata in results

**Default to Tools**:
- When MCP server provides tools, automatically wrap as MCPCapability
- Register tools in CapabilityRegistry with namespace (e.g., "mcp.server_name.tool_name")
- Support OpenAPI-based tools from MCP servers
- Support local function tools from MCP servers
