# Configuration Unit Tests

Unit tests for Nimbus configuration loading and management.

## Test Coverage

This directory contains tests for:
- **Configuration loading** - Loading from YAML, JSON, environment variables
- **Environment variable substitution** - `${VAR_NAME}` syntax support
- **Configuration validation** - Pydantic model validation
- **Router configuration** - RouterConfig model and loading
- **Error handling** - Clear error messages for invalid configurations

## Test Files

- `test_config_loader.py` - Tests for configuration loading functions
- `test_env_var_substitution.py` - Tests for environment variable substitution
- `test_yaml_router_config.py` - Tests for YAML router configuration
- `test_config_models.py` - Tests for configuration Pydantic models

## Running Tests

```bash
# Run all config tests
pytest tests/unit/config/

# Run specific test file
pytest tests/unit/config/test_env_var_substitution.py

# Run with coverage
pytest tests/unit/config/ --cov=src/nimbus/base/config
```

## Testing Approach

Configuration tests should:
- Test valid and invalid configurations
- Verify environment variable substitution
- Test error messages are clear and helpful
- Verify configuration validation works correctly
- Test edge cases (missing files, malformed YAML, etc.)
