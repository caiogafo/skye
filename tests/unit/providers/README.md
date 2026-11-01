# Provider Unit Tests

Unit tests for Nimbus provider implementations.

## Test Coverage

This directory contains tests for:
- **Provider implementations** - OpenAI, Bedrock, Anthropic, Azure, Google
- **Provider registry** - Registration and lookup
- **Provider transformations** - Message and capability transformations
- **Provider-specific logic** - API client configuration, error handling
- **Transformation encapsulation** - Ensuring provider-specific logic stays in providers

## Test Files

- `test_openai_provider.py` - Tests for OpenAI provider
- `test_bedrock_provider.py` - Tests for AWS Bedrock provider
- `test_anthropic_provider.py` - Tests for Anthropic provider
- `test_azure_provider.py` - Tests for Azure OpenAI provider
- `test_google_provider.py` - Tests for Google provider
- `test_provider_registry.py` - Tests for provider registration system

## Running Tests

```bash
# Run all provider tests
pytest tests/unit/providers/

# Run specific provider tests
pytest tests/unit/providers/test_openai_provider.py

# Run with coverage
pytest tests/unit/providers/ --cov=src/nimbus/models
```

## Testing Approach

Provider tests should:
- Mock external API calls
- Test transformation logic in isolation
- Verify error handling
- Test provider-specific features
