# Skye Test Suite

This directory contains the comprehensive test suite for the Skye library. Tests are organized into three main categories to ensure clarity and maintainability.

## Test Organization

### Unit Tests (`unit/`)

Fast, isolated tests that verify individual components in isolation. Unit tests should:
- Run quickly (< 1 second per test)
- Mock external dependencies
- Focus on business logic
- Test one component at a time

**Subdirectories:**
- `capabilities/` - Tests for capability system (registration, execution, schemas)
- `providers/` - Tests for individual provider implementations
- `routes/` - Tests for routing logic and strategies
- `config/` - Tests for configuration loading and validation
- `utils/` - Tests for utility functions

### Integration Tests (`integration/`)

Multi-component tests that verify interactions between different parts of the system. Integration tests should:
- Test component interactions
- Use real implementations where possible
- Verify end-to-end workflows
- Test configuration loading from multiple sources

**Subdirectories:**
- `capabilities/` - End-to-end capability execution tests
- `providers/` - Provider integration tests with real API calls (when configured)
- `routes/` - Router integration tests with multiple providers

### Stress Tests (`stress/`)

Performance and load tests that verify the library handles high-load scenarios correctly. Stress tests should:
- Test concurrent request handling
- Verify rate limiting under load
- Test failover scenarios
- Measure and report performance metrics

**Test Files:**
- `test_concurrent_routing.py` - Concurrent request handling
- `test_rate_limiting.py` - Rate limit enforcement under load
- `test_capability_load.py` - Capability execution under concurrent load
- `test_failover.py` - Router failover behavior

### Fixtures (`fixtures/`)

Shared test fixtures and mock data used across all test categories.

**Files:**
- `mock_responses.py` - Mock API responses for testing
- `sample_configs.py` - YAML configuration fixtures
- `sample_config.json` - JSON configuration example
- `sample_config.yaml` - YAML configuration example
- `images/` - Sample images for multimodal testing

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Stress tests only
pytest tests/stress/
```

### Run Tests for Specific Module
```bash
# Capability tests
pytest tests/unit/tools/

# Router tests
pytest tests/unit/router/

# Provider tests
pytest tests/unit/models/
```

### Run with Coverage
```bash
pytest tests/ --cov=src/skye --cov-report=html
```

### Run in Parallel
```bash
pytest tests/ -n auto
```

## Test Coverage Goals

- **Core functionality**: 80%+ coverage
- **Capabilities module**: 80%+ coverage
- **Router module**: 80%+ coverage
- **Provider module**: 80%+ coverage

## Writing Tests

### Unit Test Example
```python
import pytest
from skye.tools import CapabilityCall

def test_capability_call_creation():
    """Test creating a capability call."""
    call = CapabilityCall(
        id="test-1",
        name="get_weather",
        arguments={"location": "San Francisco"}
    )
    assert call.id == "test-1"
    assert call.name == "get_weather"
    assert call.arguments["location"] == "San Francisco"
```

### Integration Test Example
```python
import pytest
from skye.router import ModelRouter

@pytest.mark.integration
def test_router_with_yaml_config():
    """Test router loading from YAML configuration."""
    router = ModelRouter.from_yaml("tests/fixtures/sample_config.yaml")
    assert router is not None
    # Test routing behavior
```

### Stress Test Example
```python
import pytest
import asyncio
from skye.router import ModelRouter

@pytest.mark.stress
async def test_concurrent_routing():
    """Test router with 100+ concurrent requests."""
    router = ModelRouter.from_yaml("tests/fixtures/sample_config.yaml")
    
    async def make_request():
        return await router.aroute_request(request)
    
    # Create 100 concurrent requests
    tasks = [make_request() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 100
    assert all(r is not None for r in results)
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_functionality():
    pass

@pytest.mark.integration
def test_integration_functionality():
    pass

@pytest.mark.stress
def test_stress_functionality():
    pass

@pytest.mark.slow
def test_slow_functionality():
    pass
```

## Environment Variables for Testing

Some tests require environment variables to be set:

```bash
# For provider integration tests
export OPENAI_API_KEY="your-key"
export AZURE_API_KEY="your-key"
export AZURE_API_BASE="your-endpoint"
export ANTHROPIC_API_KEY="your-key"

# For AWS Bedrock tests
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
```

## Continuous Integration

Tests are automatically run on:
- Every pull request
- Every commit to main branch
- Nightly builds (including stress tests)

## Contributing

When adding new tests:
1. Place tests in the appropriate directory (unit/integration/stress)
2. Follow existing naming conventions
3. Add docstrings explaining what is being tested
4. Ensure tests are deterministic and don't depend on external state
5. Mock external dependencies in unit tests
6. Update this README if adding new test categories

## Test Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`
- Fixtures: Use descriptive names without `test_` prefix

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Skye Architecture Guidelines](../.kiro/steering/00-rules.md)
- [Python Standards](../.kiro/steering/00-rules.md)
