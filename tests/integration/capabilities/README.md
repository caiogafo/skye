# Capability Integration Tests

Integration tests for end-to-end capability functionality.

## Test Coverage

This directory contains tests for:
- **End-to-end capability execution** - Full workflow from registration to execution
- **MCP integration** - Model Context Protocol capability integration
- **Capability with providers** - Capabilities working with different LLM providers
- **Async capability execution** - Asynchronous capability workflows
- **Error handling** - Error propagation and handling across components

## Test Files

- `test_capability_execution.py` - End-to-end capability execution tests
- `test_mcp_integration.py` - MCP capability integration tests
- `test_capability_with_providers.py` - Capabilities with different providers

## Running Tests

```bash
# Run all capability integration tests
pytest tests/integration/capabilities/

# Run specific test file
pytest tests/integration/capabilities/test_capability_execution.py
```

## Testing Approach

Integration tests should:
- Use real capability implementations
- Test with real provider interactions (mocked API calls)
- Verify complete workflows
- Test error handling across component boundaries
