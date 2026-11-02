# Test Fixtures

Shared test fixtures and mock data used across all test categories.

## Purpose

This directory contains reusable test data, mock responses, and configuration fixtures that can be shared across unit, integration, and stress tests.

## Files

### `mock_responses.py`
Mock API responses for testing provider implementations without making real API calls.

**Contents:**
- Mock OpenAI responses
- Mock Bedrock responses
- Mock Anthropic responses
- Mock error responses
- Mock streaming responses

**Usage:**
```python
from tests.fixtures.mock_responses import MOCK_OPENAI_RESPONSE

def test_provider(mock_api):
    mock_api.return_value = MOCK_OPENAI_RESPONSE
    # Test provider logic
```

### `sample_configs.py`
YAML configuration strings and dictionaries for testing configuration loading and router setup.

**Contents:**
- `BASIC_ROUTER_CONFIG_YAML` - Simple single-route configuration
- `ENV_VAR_ROUTER_CONFIG_YAML` - Configuration with environment variables
- `MULTI_PROVIDER_ROUTER_CONFIG_YAML` - Multi-provider configuration with fallbacks
- `FALLBACK_ROUTER_CONFIG_YAML` - Configuration with fallback chains
- `INVALID_ROUTER_CONFIG_YAML` - Invalid configuration for error testing
- `ALL_STRATEGIES_ROUTER_CONFIG_YAML` - Configuration with all routing strategies
- Configuration dictionaries for programmatic testing
- Sample model target configurations

**Usage:**
```python
from tests.fixtures.sample_configs import BASIC_ROUTER_CONFIG_YAML
import tempfile

def test_yaml_loading():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        f.write(BASIC_ROUTER_CONFIG_YAML)
        f.flush()
        router = ModelRouter.from_yaml(f.name)
        assert router is not None
```

### `sample_config.json`
Example JSON configuration file for testing JSON configuration loading.

**Usage:**
```python
from skye.base.config import load_config

config = load_config("tests/fixtures/sample_config.json")
```

### `sample_config.yaml`
Example YAML configuration file for testing YAML configuration loading.

**Usage:**
```python
from skye.router import ModelRouter

router = ModelRouter.from_yaml("tests/fixtures/sample_config.yaml")
```

### `images/`
Sample images for testing multimodal functionality.

**Contents:**
- Test images in various formats (PNG, JPEG)
- Images of different sizes
- Images for testing encoding and processing

**Usage:**
```python
from pathlib import Path

image_path = Path("tests/fixtures/images/test_image.png")
# Test image handling
```

## Creating New Fixtures

When adding new fixtures:

1. **Keep fixtures simple** - Fixtures should be minimal and focused
2. **Document usage** - Add examples to this README
3. **Make fixtures reusable** - Design for use across multiple tests
4. **Use descriptive names** - Names should clearly indicate purpose
5. **Avoid hardcoded secrets** - Use placeholders like "test-key-123"

## Fixture Organization

### Mock Responses
- Group by provider (OpenAI, Bedrock, etc.)
- Include both success and error responses
- Include streaming response examples

### Configuration Fixtures
- Provide both valid and invalid examples
- Include examples for all major features
- Use environment variable placeholders

### Test Data
- Keep test data minimal
- Use realistic but simple examples
- Avoid sensitive or real data

## Best Practices

1. **Immutable fixtures** - Fixtures should not be modified by tests
2. **Self-contained** - Fixtures should not depend on external state
3. **Well-documented** - Include docstrings and usage examples
4. **Version controlled** - All fixtures should be in git
5. **No secrets** - Never commit real API keys or credentials

## Using Fixtures in Tests

### Pytest Fixtures

```python
import pytest
from tests.fixtures.mock_responses import MOCK_OPENAI_RESPONSE

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = Mock()
    client.chat.completions.create.return_value = MOCK_OPENAI_RESPONSE
    return client

def test_with_fixture(mock_openai_client):
    # Use fixture in test
    pass
```

### Direct Import

```python
from tests.fixtures.sample_configs import BASIC_ROUTER_CONFIG_DICT

def test_config_loading():
    config = RouterConfig(**BASIC_ROUTER_CONFIG_DICT)
    assert config is not None
```

### File-Based Fixtures

```python
from pathlib import Path

def test_yaml_loading():
    config_path = Path("tests/fixtures/sample_config.yaml")
    router = ModelRouter.from_yaml(str(config_path))
    assert router is not None
```

## Related Documentation

- [Main Test README](../README.md)
- [Unit Tests](../unit/README.md)
- [Integration Tests](../integration/README.md)
- [Stress Tests](../stress/README.md)
