# Provider Integration Tests

Integration tests for provider implementations with real or mocked API calls.

## Test Coverage

This directory contains tests for:
- **Provider API integration** - Testing with real API endpoints (when configured)
- **Multi-provider workflows** - Using multiple providers together
- **Provider-specific features** - Testing provider-specific functionality
- **Error handling** - Provider error handling and recovery
- **Streaming responses** - Testing streaming functionality

## Test Files

- `test_openai_integration.py` - OpenAI provider integration tests
- `test_bedrock_integration.py` - AWS Bedrock provider integration tests
- `test_anthropic_integration.py` - Anthropic provider integration tests
- `test_azure_integration.py` - Azure OpenAI provider integration tests
- `test_vertex_integration.py` - Google Vertex AI provider integration tests
- `test_multi_provider.py` - Multi-provider workflow tests

## Running Tests

```bash
# Run all provider integration tests
pytest tests/integration/providers/

# Run specific provider tests
pytest tests/integration/providers/test_openai_integration.py

# Skip tests requiring API keys
pytest tests/integration/providers/ -m "not requires_api_key"
```

## Environment Setup

Set environment variables for API access:

```bash
export OPENAI_API_KEY="your-key"
export AZURE_API_KEY="your-key"
export AZURE_API_BASE="your-endpoint"
export ANTHROPIC_API_KEY="your-key"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

## Testing Approach

Provider integration tests should:
- Use real API calls when possible (with rate limiting)
- Mock API calls for CI/CD pipelines
- Test provider-specific features
- Verify error handling with real error responses
- Test streaming and async functionality
