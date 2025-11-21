# Router Unit Tests

Unit tests for Nimbus routing functionality.

## Test Coverage

This directory contains tests for:
- **Model router** - Route selection and request routing
- **Routing strategies** - Round-robin, least-busy, rate-limit-aware, cost-based
- **Rate limiting** - TPM/RPM tracking and enforcement
- **Health tracking** - Model health monitoring and cooldowns
- **Fallback chains** - Fallback execution logic
- **YAML configuration** - Router configuration from YAML files

## Test Files

- `test_model_router.py` - Tests for core router functionality
- `test_routing_strategies.py` - Tests for different routing strategies
- `test_rate_limiting.py` - Tests for rate limit enforcement
- `test_health_tracking.py` - Tests for model health monitoring
- `test_fallback_chains.py` - Tests for fallback logic

## Running Tests

```bash
# Run all router tests
pytest tests/unit/routes/

# Run specific test file
pytest tests/unit/routes/test_model_router.py

# Run with coverage
pytest tests/unit/routes/ --cov=src/nimbus/routes
```

## Testing Approach

Router tests should:
- Mock provider calls
- Test routing logic in isolation
- Verify rate limit calculations
- Test health tracking state transitions
- Verify fallback chain execution order
