# Router Integration Tests

Integration tests for router functionality with real configurations and workflows.

## Test Coverage

This directory contains tests for:
- **`.skye` configuration loading** - Loading and using `.skye` router configurations
- **Fallback chain execution** - Testing fallback chains end-to-end
- **Rate limiting integration** - Rate limiting with real request patterns
- **Multi-provider routing** - Routing across multiple providers
- **Health tracking** - Model health monitoring in real scenarios

## Test Files

- `test_skye_routing.py` - `.skye` configuration and routing tests
- `test_fallback_chains.py` - Fallback chain execution tests
- `test_rate_limit_integration.py` - Rate limiting integration tests
- `test_multi_provider_routing.py` - Multi-provider routing tests

## Running Tests

```bash
# Run all router integration tests
pytest tests/integration/routes/

# Run specific test file
pytest tests/integration/routes/test_skye_routing.py
```

## Testing Approach

Router integration tests should:
- Use real .skye configurations
- Test complete routing workflows
- Verify fallback chains execute correctly
- Test rate limiting with realistic request patterns
- Verify health tracking state transitions
- Test error recovery and retry logic
