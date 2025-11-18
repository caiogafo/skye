# Implementation Plan: Model Providers

## Overview

This implementation plan breaks down the development of the Model Providers component into discrete, incremental tasks. The plan follows a bottom-up approach: utilities first, then base classes, then concrete provider implementations, and finally embeddings.

## Task List

- [x] 1. Set up provider package structure
  - Create src/nimbus/providers/ directory structure
  - Create __init__.py files for all subdirectories
  - Update pyproject.toml with provider-specific optional dependencies
  - Add openai, anthropic, bedrock, azure, vertex, cohere extras
  - Configure optional dependencies to not require installation in specific environments
  - Create tests/unit/providers/ and tests/integration/providers/ directories
  - Create tests/fixtures/mock_responses.py for test data
  - Update Makefile to include provider tests
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement lazy import system
  - [x] 2.1 Create LazyImporter utility
    - Implement import_module() with helpful error messages
    - Implement is_available() to check module availability
    - Handle ImportError with installation instructions
    - Support package_name and install_extra parameters
    - Write unit test in tests/unit/test_lazy_import.py
    - Test successful imports, missing modules, and error messages
    - Run with `uv run pytest tests/unit/test_lazy_import.py -v`
    - Verify with `uv run python -c "from nimbus.providers.lazy_import import LazyImporter; print('OK')"`
    - _Requirements: 1.3, 1.4, 1.5, 12.1, 12.2, 12.3, 12.4_
  
  - [x] 2.2 Test lazy loading in Lambda-like environment
    - Create test that simulates boto3 pre-installed environment
    - Test that Bedrock provider works without boto3 in dependencies
    - Test that other providers fail gracefully without their SDKs
    - Run with `uv run pytest tests/unit/test_lazy_import.py::test_lambda_environment -v`
    - _Requirements: 12.2, 12.5_

- [x] 3. Implement message transformers
  - [x] 3.1 Create MessageTransformer class
    - Implement to_openai_format() for OpenAI message conversion
    - Implement to_anthropic_format() with separate system message
    - Implement to_bedrock_format() for Converse API
    - Implement to_vertex_format() for Gemini
    - Handle all message types: User, Assistant, System, Capability
    - Write unit test in tests/unit/test_transformers.py
    - Test each transformation with various message combinations
    - Test capability/tool call transformations
    - Run with `uv run pytest tests/unit/test_transformers.py::test_message_transformer -v`
    - _Requirements: 13.1, 13.3, 13.5_
  
  - [x] 3.2 Test message transformation edge cases
    - Test empty messages
    - Test messages with metadata
    - Test multimodal messages with images
    - Test function call messages
    - Run with `uv run pytest tests/unit/test_transformers.py::test_edge_cases -v`
    - _Requirements: 13.1, 13.3_

- [x] 4. Implement multimodal support
  - [x] 4.1 Create ImageHandler utility
    - Implement process_image() for URL, file path, base64, bytes
    - Implement _get_mime_type() for file extension detection
    - Implement to_openai_format() for OpenAI image format
    - Implement to_anthropic_format() for Anthropic image format
    - Implement to_bedrock_format() for Bedrock image format
    - Write unit test in tests/unit/test_image_handler.py
    - Test all input types (URL, path, base64, bytes)
    - Test format conversions for each provider
    - Create test fixtures with sample images
    - Run with `uv run pytest tests/unit/test_image_handler.py -v`
    - _Requirements: 4.1, 4.5_
  
  - [ ]* 4.2 Create AudioHandler and VideoHandler utilities
    - Implement AudioHandler for audio inputs
    - Implement VideoHandler for video inputs
    - Support provider-specific formats
    - Write unit tests for audio and video handling
    - Run with `uv run pytest tests/unit/test_multimodal.py -v`
    - _Requirements: 4.2, 4.3_

- [ ] 5. Implement token counting and cost estimation
  - [x] 5.1 Create TokenCounter utility
    - Implement count_tokens() using provider-specific tokenizers
    - Implement count_message_tokens() for message lists
    - Implement _get_tokenizer() with lazy loading
    - Implement _get_message_overhead() for per-message tokens
    - Implement _approximate_tokenizer() as fallback
    - Support tiktoken for OpenAI models
    - Support anthropic tokenizer for Claude models
    - Write unit test in tests/unit/test_token_counter.py
    - Test token counting for various models
    - Test message overhead calculations
    - Test fallback tokenizer
    - Run with `uv run pytest tests/unit/test_token_counter.py -v`
    - Verify with `uv run python -c "from nimbus.providers.token_counter import TokenCounter; print(TokenCounter.count_tokens('hello', 'gpt-4'))"`
    - _Requirements: 8.1, 8.5_
  
  - [x] 5.2 Create CostCalculator utility
    - Implement calculate_cost() with pricing data
    - Implement add_custom_pricing() for custom models
    - Add pricing data for major models (GPT-4, Claude, etc.)
    - Support custom pricing overrides
    - Write unit test in tests/unit/test_cost_calculator.py
    - Test cost calculations for various models
    - Test custom pricing
    - Test unknown models (should return 0.0)
    - Run with `uv run pytest tests/unit/test_cost_calculator.py -v`
    - _Requirements: 8.2, 8.3, 8.4_

- [x] 6. Implement provider registry
  - [x] 6.1 Create ProviderRegistry class
    - Implement register_model_provider() for registration
    - Implement register_embedding_provider() for embeddings
    - Implement get_model_provider() with error handling
    - Implement get_embedding_provider() with error handling
    - Implement list_model_providers() and list_embedding_providers()
    - Write unit test in tests/unit/test_provider_registry.py
    - Test provider registration and retrieval
    - Test error messages for missing providers
    - Test listing available providers
    - Run with `uv run pytest tests/unit/test_provider_registry.py -v`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 7. Implement base provider classes
  - [x] 7.1 Create BaseModelProvider abstract class
    - Implement __init__ with config storage
    - Implement client property with lazy loading
    - Define abstract _initialize_client() method
    - Define abstract _transform_request() method
    - Define abstract _transform_response() method
    - Define abstract _transform_stream_chunk() method
    - Implement complete() with error handling
    - Implement stream() with error handling
    - Implement default acomplete() and astream()
    - Define abstract _call_provider() method
    - Define abstract _call_provider_stream() method
    - Write unit test in tests/unit/providers/test_base_provider.py
    - Create mock provider implementation for testing
    - Test lazy client initialization
    - Test error wrapping in ProviderError
    - Run with `uv run pytest tests/unit/providers/test_base_provider.py -v`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 9.1, 9.2, 9.3, 9.4_
  
  - [x] 7.2 Create BaseEmbeddingProvider abstract class
    - Implement __init__ with model and config
    - Implement client property with lazy loading
    - Define abstract _initialize_client() method
    - Implement encode() using encode_batch()
    - Define abstract encode_batch() method
    - Implement aencode() using aencode_batch()
    - Implement default aencode_batch() using sync version
    - Define abstract get_vector_dimension() method
    - Write unit test in tests/unit/providers/test_base_embedding_provider.py
    - Create mock embedding provider for testing
    - Test single and batch encoding
    - Test async methods
    - Run with `uv run pytest tests/unit/providers/test_base_embedding_provider.py -v`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 8. Implement OpenAI provider
  - [x] 8.1 Create OpenAIProvider class
    - Implement __init__ with api_key, api_base, organization
    - Implement _initialize_client() with lazy OpenAI import
    - Implement _transform_request() for OpenAI format
    - Handle structured outputs with response_format
    - Handle function calling with tools parameter
    - Handle provider-specific metadata
    - Implement _transform_response() from OpenAI to CompletionResponse
    - Parse structured outputs from response
    - Extract tool calls from response
    - Implement _transform_stream_chunk() for streaming
    - Implement _call_provider() for sync calls
    - Implement _call_provider_stream() for streaming
    - Implement acomplete() with AsyncOpenAI client
    - Implement get_model_info() with capabilities
    - Write unit test in tests/unit/providers/test_openai_provider.py
    - Mock OpenAI SDK to avoid actual API calls
    - Test request transformation
    - Test response transformation
    - Test streaming
    - Test structured outputs
    - Test function calling
    - Run with `uv run pytest tests/unit/providers/test_openai_provider.py -v`
    - Verify with `uv run python -c "from nimbus.providers.openai_provider import OpenAIProvider; print('OK')"`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 8.2 Write OpenAI integration tests
    - Create integration test with real OpenAI API (requires API key)
    - Test actual completion requests
    - Test streaming responses
    - Test function calling
    - Test structured outputs
    - Test multimodal inputs (images)
    - Mark tests with pytest.mark.integration
    - Skip if OPENAI_API_KEY not set
    - Run with `uv run pytest tests/integration/test_openai_integration.py -v -m integration`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 5.1, 6.1_

- [ ] 9. Implement Anthropic provider
  - [x] 9.1 Create AnthropicProvider class
    - Implement __init__ with api_key
    - Implement _initialize_client() with lazy Anthropic import
    - Implement _transform_request() for Anthropic format
    - Handle separate system parameter
    - Handle tool use format (different from OpenAI)
    - Handle thinking/reasoning features
    - Implement _transform_response() from Anthropic to CompletionResponse
    - Parse tool use from response
    - Implement _transform_stream_chunk() for streaming
    - Implement _call_provider() for sync calls
    - Implement _call_provider_stream() for streaming
    - Implement acomplete() with AsyncAnthropic client
    - Implement get_model_info() with capabilities
    - Write unit test in tests/unit/providers/test_anthropic_provider.py
    - Mock Anthropic SDK
    - Test request transformation with system message separation
    - Test response transformation
    - Test tool use format
    - Run with `uv run pytest tests/unit/providers/test_anthropic_provider.py -v`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.2_
  
  - [ ]* 9.2 Write Anthropic integration tests
    - Create integration test with real Anthropic API
    - Test completion requests
    - Test streaming
    - Test tool use
    - Test thinking features
    - Mark with pytest.mark.integration
    - Run with `uv run pytest tests/integration/test_anthropic_integration.py -v -m integration`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 7.2_

- [x] 10. Implement Bedrock provider
  - [x] 10.1 Create BedrockProvider class
    - Implement __init__ with region_name, profile_name
    - Implement _initialize_client() with optional boto3
    - Check for pre-installed boto3 in environment
    - Fall back to lazy import if not found
    - Implement _transform_request() for Bedrock Converse API
    - Handle tool configuration format
    - Handle inference config parameters
    - Implement _transform_response() from Bedrock to CompletionResponse
    - Parse tool use from response
    - Implement _transform_stream_chunk() for streaming
    - Implement _call_provider() using converse()
    - Implement _call_provider_stream() using converse_stream()
    - Implement get_model_info() with capabilities
    - Write unit test in tests/unit/providers/test_bedrock_provider.py
    - Mock boto3 client
    - Test optional boto3 import
    - Test request transformation for Converse API
    - Test response transformation
    - Test tool use format
    - Run with `uv run pytest tests/unit/providers/test_bedrock_provider.py -v`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.4, 12.1, 12.2_
  
  - [ ]* 10.2 Write Bedrock integration tests
    - Create integration test with real Bedrock API
    - Test completion with various models (Claude, Titan, Llama)
    - Test streaming
    - Test tool use
    - Test multimodal inputs
    - Mark with pytest.mark.integration
    - Run with `uv run pytest tests/integration/test_bedrock_integration.py -v -m integration`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 6.1, 7.4_

- [x] 11. Implement Azure OpenAI provider
  - [x] 11.1 Create AzureOpenAIProvider class
    - Implement __init__ with azure_endpoint, api_key, api_version, deployment_name
    - Implement _initialize_client() with lazy Azure SDK import
    - Implement _transform_request() (similar to OpenAI)
    - Handle Azure-specific parameters
    - Implement _transform_response() from Azure to CompletionResponse
    - Implement _transform_stream_chunk() for streaming
    - Implement _call_provider() for sync calls
    - Implement _call_provider_stream() for streaming
    - Implement get_model_info() with capabilities
    - Write unit test in tests/unit/providers/test_azure_provider.py
    - Mock Azure SDK
    - Test Azure-specific configuration
    - Test request/response transformation
    - Run with `uv run pytest tests/unit/providers/test_azure_provider.py -v`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 11.2 Write Azure integration tests
    - Create integration test with real Azure OpenAI
    - Test completion requests
    - Test streaming
    - Test function calling
    - Mark with pytest.mark.integration
    - Run with `uv run pytest tests/integration/test_azure_integration.py -v -m integration`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.1_

- [x] 12. Implement Vertex AI provider
  - [x] 12.1 Create VertexAIProvider class
    - Implement __init__ with project_id, location, credentials
    - Implement _initialize_client() with lazy Vertex SDK import
    - Implement _transform_request() for Gemini format
    - Handle safety settings
    - Handle grounding features
    - Implement _transform_response() from Vertex to CompletionResponse
    - Implement _transform_stream_chunk() for streaming
    - Implement _call_provider() for sync calls
    - Implement _call_provider_stream() for streaming
    - Implement get_model_info() with capabilities
    - Write unit test in tests/unit/providers/test_vertex_provider.py
    - Mock Vertex SDK
    - Test request transformation for Gemini
    - Test safety settings handling
    - Run with `uv run pytest tests/unit/providers/test_vertex_provider.py -v`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.2, 4.3, 7.5_
  
  - [ ]* 12.2 Write Vertex AI integration tests
    - Create integration test with real Vertex AI
    - Test Gemini models
    - Test multimodal inputs (images, video)
    - Test safety settings
    - Mark with pytest.mark.integration
    - Run with `uv run pytest tests/integration/test_vertex_integration.py -v -m integration`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.2, 4.3, 7.5_

- [x] 13. Implement embedding providers
  - [x] 13.1 Create OpenAIEmbeddingProvider class
    - Implement __init__ with model, api_key
    - Implement _initialize_client() with lazy OpenAI import
    - Implement encode_batch() using OpenAI embeddings API
    - Implement aencode_batch() with AsyncOpenAI
    - Implement get_vector_dimension() with model dimensions
    - Support text-embedding-3-small, text-embedding-3-large, ada-002
    - Write unit test in tests/unit/providers/test_openai_embeddings.py
    - Mock OpenAI SDK
    - Test batch encoding
    - Test async encoding
    - Test vector dimensions
    - Run with `uv run pytest tests/unit/providers/test_openai_embeddings.py -v`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 13.2 Create BedrockEmbeddingProvider class
    - Implement __init__ with model, region_name
    - Implement _initialize_client() with optional boto3
    - Implement encode_batch() using Bedrock embeddings
    - Support Titan embeddings models
    - Implement get_vector_dimension() for Titan models
    - Write unit test in tests/unit/providers/test_bedrock_embeddings.py
    - Mock boto3 client
    - Test batch encoding
    - Test optional boto3 import
    - Run with `uv run pytest tests/unit/providers/test_bedrock_embeddings.py -v`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 12.1, 12.2_
  
  - [x] 13.3 Create CohereEmbeddingProvider class
    - Implement __init__ with model, api_key
    - Implement _initialize_client() with lazy Cohere import
    - Implement encode_batch() using Cohere embeddings API
    - Support embed-english-v3, embed-multilingual-v3
    - Implement get_vector_dimension() for Cohere models
    - Write unit test in tests/unit/providers/test_cohere_embeddings.py
    - Mock Cohere SDK
    - Test batch encoding
    - Run with `uv run pytest tests/unit/providers/test_cohere_embeddings.py -v`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 13.4 Create VertexEmbeddingProvider class
    - Implement __init__ with model, project_id, location
    - Implement _initialize_client() with lazy Vertex SDK import
    - Implement encode_batch() using Vertex embeddings API
    - Support text-embedding-004, text-multilingual-embedding-002
    - Implement get_vector_dimension() for Vertex models
    - Write unit test in tests/unit/providers/test_vertex_embeddings.py
    - Mock Vertex SDK
    - Test batch encoding
    - Run with `uv run pytest tests/unit/providers/test_vertex_embeddings.py -v`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 13.5 Create VertexMultimodalEmbeddingProvider class
    - Implement __init__ with project_id, location
    - Implement encode_batch() supporting text and images
    - Support multimodalembedding@001 model
    - Handle image inputs via ImageHandler
    - Implement get_vector_dimension() (returns 1408)
    - Write unit test in tests/unit/providers/test_vertex_multimodal_embeddings.py
    - Mock Vertex SDK
    - Test text encoding
    - Test image encoding
    - Test mixed text/image encoding
    - Run with `uv run pytest tests/unit/providers/test_vertex_multimodal_embeddings.py -v`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 14.1, 14.2, 14.3, 14.4, 14.5_
  
  - [ ]* 13.6 Write embedding integration tests
    - Create integration tests for all embedding providers
    - Test actual API calls with real providers
    - Test batch encoding performance
    - Test async encoding
    - Test multimodal embeddings
    - Mark with pytest.mark.integration
    - Run with `uv run pytest tests/integration/test_embeddings_integration.py -v -m integration`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 14.1, 14.2, 14.3_

- [x] 14. Implement error handling and retry logic
  - [x] 14.1 Add retry decorator to base provider
    - Install tenacity for retry logic: add to dependencies
    - Implement retry decorator with exponential backoff
    - Configure retry for rate limits, timeouts, server errors
    - Configure max retries (default 3)
    - Configure backoff multiplier and min/max wait times
    - Write unit test in tests/unit/providers/test_retry_logic.py
    - Test retry behavior with mock failures
    - Test exponential backoff timing
    - Test max retries exceeded
    - Run with `uv run pytest tests/unit/providers/test_retry_logic.py -v`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x] 14.2 Implement provider-specific error handling
    - Add error handling for OpenAI errors (RateLimitError, APIError)
    - Add error handling for Anthropic errors
    - Add error handling for Bedrock errors (ClientError)
    - Add error handling for Azure errors
    - Add error handling for Vertex errors
    - Wrap all errors in ProviderError with context
    - Include retry_after, status_code, error_type in context
    - Write unit test in tests/unit/providers/test_error_handling.py
    - Test each provider's error wrapping
    - Test error context preservation
    - Run with `uv run pytest tests/unit/providers/test_error_handling.py -v`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 15. Implement provider health monitoring
  - [x] 15.1 Add health tracking to base provider
    - Implement success/failure counters
    - Implement latency tracking
    - Implement error rate calculation
    - Implement get_health_metrics() method
    - Store metrics in provider instance
    - Write unit test in tests/unit/providers/test_health_monitoring.py
    - Test metric tracking
    - Test health calculations
    - Run with `uv run pytest tests/unit/providers/test_health_monitoring.py -v`
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_
  
  - [ ]* 15.2 Integrate with ObserverInterface
    - Emit metrics via ObserverInterface when configured
    - Log provider performance at configurable intervals
    - Include provider health in error messages
    - Write unit test for observer integration
    - Run with `uv run pytest tests/unit/providers/test_observer_integration.py -v`
    - _Requirements: 15.2, 15.3, 15.5_

- [x] 16. Register providers and create exports
  - [x] 16.1 Auto-register providers on import
    - Register OpenAIProvider in openai_provider.py module
    - Register AnthropicProvider in anthropic_provider.py module
    - Register BedrockProvider in bedrock_provider.py module
    - Register AzureOpenAIProvider in azure_provider.py module
    - Register VertexAIProvider in vertex_provider.py module
    - Register all embedding providers
    - Use ProviderRegistry.register_model_provider() at module level
    - Use ProviderRegistry.register_embedding_provider() at module level
    - Write unit test in tests/unit/test_provider_registration.py
    - Test that providers are auto-registered on import
    - Test that registry lists all providers
    - Run with `uv run pytest tests/unit/test_provider_registration.py -v`
    - _Requirements: 10.1, 10.2, 10.5_
  
  - [x] 16.2 Configure package exports
    - Export ProviderRegistry from nimbus.providers
    - Export all provider classes
    - Export utility classes (TokenCounter, CostCalculator, ImageHandler)
    - Export LazyImporter
    - Define __all__ in __init__.py
    - Write unit test in tests/unit/test_provider_exports.py
    - Test that all expected symbols are importable
    - Test that __all__ is properly defined
    - Run with `uv run pytest tests/unit/test_provider_exports.py -v`
    - Verify with `uv run python -c "from nimbus.providers import ProviderRegistry, OpenAIProvider; print('OK')"`
    - _Requirements: All_

- [x] 17. Write documentation and examples
  - [x] 17.1 Update README with provider usage
    - Add installation instructions for each provider
    - Add basic usage examples for LLM providers
    - Add basic usage examples for embedding providers
    - Add multimodal usage examples
    - Add structured output examples
    - Add function calling examples
    - Document lazy loading behavior
    - Document Lambda deployment (boto3 optional)
    - Reference MCP usage patterns where applicable
    - No unit test required (documentation)
    - _Requirements: All_
  
  - [x] 17.2 Create example scripts
    - Create examples/providers/openai_example.py
    - Create examples/providers/bedrock_example.py
    - Create examples/providers/anthropic_example.py
    - Create examples/providers/embeddings_example.py
    - Create examples/providers/multimodal_example.py
    - Create examples/providers/structured_output_example.py
    - Create examples/providers/function_calling_example.py
    - Test that examples run with `uv run python examples/providers/openai_example.py`
    - _Requirements: All_
  
  - [x] 17.3 Add type hints verification
    - Run mypy on all provider code with `uv run mypy src/nimbus/providers --strict`
    - Fix any type hint issues
    - Add mypy to Makefile check target for providers
    - Create test script tests/test_provider_type_hints.sh
    - Run with `uv run mypy src/nimbus/providers --strict`
    - _Requirements: All_

- [ ]* 18. Write comprehensive integration tests
  - [ ]* 18.1 Create end-to-end provider tests
    - Test switching between providers with same code
    - Test fallback scenarios
    - Test cost tracking across providers
    - Test multimodal inputs across providers
    - Test structured outputs across providers
    - Mark with pytest.mark.integration
    - Run with `uv run pytest tests/integration/test_provider_e2e.py -v -m integration`
    - _Requirements: All_
  
  - [ ]* 18.2 Create performance benchmarks
    - Benchmark token counting performance
    - Benchmark request transformation overhead
    - Benchmark lazy import overhead
    - Create benchmarks/provider_benchmarks.py
    - Run with `uv run python benchmarks/provider_benchmarks.py`
    - _Requirements: All_

## Implementation Notes

### UV Usage

All Python commands should be run using UV:
- **Testing**: `uv run pytest tests/unit/providers/ -v`
- **Integration tests**: `uv run pytest tests/integration/providers/ -v -m integration`
- **Type checking**: `uv run mypy src/nimbus/providers --strict`
- **Linting**: `uv run ruff check src/nimbus/providers tests/`
- **Formatting**: `uv run black src/nimbus/providers tests/`
- **Quick validation**: `uv run python -c "from nimbus.providers import ProviderRegistry; print(ProviderRegistry.list_model_providers())"`
- **Running examples**: `uv run python examples/providers/openai_example.py`

### MCP Reference Implementation

When implementing providers, reference MCP patterns:
- **LiteLLM MCP**: Check transformation patterns for request/response conversion
- **LangChain MCP**: Check callback and tool patterns for function calling
- **SDK-Python MCP**: Check Python SDK structure and async patterns

Access MCP documentation via the MCP tools for specific patterns.

### Testing Strategy

**Unit Tests (Required)**:
- Mock all provider SDKs to avoid actual API calls
- Test request/response transformations
- Test error handling and retry logic
- Test lazy loading behavior
- Focus on transformation logic and error handling

**Integration Tests (Optional, marked with *)**:
- Require actual API keys
- Test real API calls
- Skip if API keys not available
- Mark with `pytest.mark.integration`
- Run separately from unit tests

**Test Execution**:
```bash
# Run unit tests only
uv run pytest tests/unit/providers/ -v

# Run integration tests (requires API keys)
uv run pytest tests/integration/providers/ -v -m integration

# Run all tests
uv run pytest tests/ -v

# Run specific provider tests
uv run pytest tests/unit/providers/test_openai_provider.py -v
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
export COHERE_API_KEY="..."
```

### Dependencies

**Base Dependencies** (always installed with nimbus):
- pydantic>=2.0
- pyyaml>=6.0
- tenacity>=8.0 (for retry logic)

**Provider-Specific Dependencies** (optional):
```toml
[project.optional-dependencies]
openai = ["openai>=1.0", "tiktoken>=0.5"]
anthropic = ["anthropic>=0.25"]
bedrock = ["boto3>=1.28"]  # Optional in Lambda
azure = ["azure-ai-inference>=1.0.0b1", "azure-identity>=1.15"]
vertex = ["google-cloud-aiplatform>=1.38"]
cohere = ["cohere>=5.0"]

# Convenience bundles
llm-providers = ["openai>=1.0", "anthropic>=0.25", "boto3>=1.28"]
embedding-providers = ["openai>=1.0", "cohere>=5.0"]
all-providers = ["openai>=1.0", "anthropic>=0.25", "boto3>=1.28", "azure-ai-inference>=1.0.0b1", "google-cloud-aiplatform>=1.38", "cohere>=5.0", "tiktoken>=0.5"]
```

### Code Quality

- All code must have complete type hints
- All public APIs must have docstrings
- Follow PEP 8 style guidelines (enforced by black and ruff)
- Maintain test coverage above 80% for non-optional tests
- Run `uv run mypy src/nimbus/providers --strict` before committing
- Use `uv run black src/nimbus/providers tests/` to format code
- Use `uv run ruff check src/nimbus/providers tests/` to lint code

### Quick Validation Commands

After implementing each task, use these UV commands to validate:

```bash
# Import validation
uv run python -c "from nimbus.providers import ProviderRegistry, OpenAIProvider; print('OK')"

# Type checking
uv run mypy src/nimbus/providers --strict

# Run tests
uv run pytest tests/unit/providers/ -v

# Code formatting
uv run black src/nimbus/providers tests/ --check

# Linting
uv run ruff check src/nimbus/providers tests/

# Full validation
uv run pytest tests/unit/providers/ && uv run mypy src/nimbus/providers --strict && uv run ruff check src/nimbus/providers tests/
```

### Lambda Deployment Notes

For AWS Lambda deployment:
1. boto3 is pre-installed in Lambda runtime
2. Do NOT include boto3 in deployment package
3. BedrockProvider will detect and use pre-installed boto3
4. Test with: `LazyImporter.is_available("boto3")`

### Task Dependencies

- Task 1 must complete before all other tasks
- Tasks 2-6 (utilities) can be done in parallel
- Task 7 (base classes) depends on tasks 2-6
- Tasks 8-12 (LLM providers) depend on task 7
- Task 13 (embeddings) depends on task 7
- Task 14 (error handling) can be done alongside provider implementation
- Task 15 (monitoring) depends on task 7
- Task 16 (registration) depends on tasks 8-13
- Task 17 (documentation) should be done last
- Task 18 (integration tests) can be done incrementally

### Testing Requirements Summary

**IMPORTANT**: For each implementation task, you MUST:

1. **Write the unit test FIRST** in the appropriate test file
2. **Mock external dependencies** (provider SDKs) to avoid actual API calls
3. **Implement the code** to make the test pass
4. **Run the test** using the specified `uv run pytest` command
5. **Verify** the implementation works as expected

**Test File Organization**:
- `tests/unit/providers/test_*.py` - Provider-specific unit tests
- `tests/unit/test_*.py` - Utility unit tests
- `tests/integration/test_*_integration.py` - Integration tests (optional)
- `tests/fixtures/mock_responses.py` - Mock API responses

**Test Execution Pattern**:
```bash
# Run specific test
uv run pytest tests/unit/providers/test_openai_provider.py::test_transform_request -v

# Run all tests in a file
uv run pytest tests/unit/providers/test_openai_provider.py -v

# Run all provider tests
uv run pytest tests/unit/providers/ -v

# Run with coverage
uv run pytest tests/unit/providers/ --cov=src/nimbus/providers --cov-report=term-missing
```

**Test Quality Standards**:
- Each test should be focused on a single behavior
- Use descriptive test names (test_openai_transforms_user_message_correctly)
- Use pytest.mark.parametrize for testing multiple cases
- Use pytest.mark.asyncio for async tests
- Mock all external API calls
- Test both success and failure cases
- Aim for 80%+ code coverage on core functionality
