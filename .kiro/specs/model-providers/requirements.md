# Requirements Document: Model Providers

## Introduction

The Model Providers component implements the ModelInterface and VectorEncoderInterface from skye-core to provide concrete integrations with LLM and embedding providers. This component enables developers to use various AI models (text generation, embeddings, multimodal) through a unified interface while maintaining modularity - providers can be installed independently, and even within a provider, heavy dependencies are optional (e.g., using Bedrock in AWS Lambda without installing boto3).

The design follows the patterns established by litellm and llmio, providing a clean abstraction layer over multiple providers while supporting advanced features like streaming, structured outputs, multimodal inputs, and provider-specific optimizations.

## Glossary

- **ModelProvider**: A concrete implementation of ModelInterface for a specific LLM service (OpenAI, Bedrock, Anthropic, etc.)
- **EmbeddingProvider**: A concrete implementation of VectorEncoderInterface for embedding models
- **MultimodalModel**: A model that can process multiple input types (text, images, audio, video)
- **StructuredOutput**: Type-safe model responses validated against Pydantic schemas
- **StreamingResponse**: Real-time token-by-token response delivery
- **ProviderAdapter**: A transformation layer that converts skye requests to provider-specific formats
- **LazyImport**: Deferred dependency loading that only imports libraries when actually used
- **ProviderRegistry**: A central registry for discovering and instantiating model providers
- **TokenCounter**: A utility for calculating token usage across different tokenizers
- **CostCalculator**: A utility for estimating API costs based on token usage
- **ProviderClient**: The underlying SDK client for a specific provider (e.g., OpenAI client, boto3 client)
- **RequestTransformer**: Converts CompletionRequest to provider-specific request format
- **ResponseTransformer**: Converts provider-specific responses to CompletionResponse format
- **ImageInput**: Multimodal input containing image data (URL, base64, or file path)
- **AudioInput**: Multimodal input containing audio data
- **VideoInput**: Multimodal input containing video data
- **ToolCall**: A request from the model to execute a capability/function
- **FunctionSchema**: JSON Schema definition of a callable function for the model

## Requirements

### Requirement 1: Modular Provider Architecture

**User Story:** As a developer, I want to install only the providers I need without pulling in unnecessary dependencies, so that my application remains lightweight and deployment-friendly.

#### Acceptance Criteria

1. THE skye library SHALL support installing individual providers via extras (e.g., `skyeai[bedrock]`, `skyeai[openai]`)
2. WHEN a provider extra is installed, THE skye library SHALL only install the minimum required dependencies for that provider
3. THE skye library SHALL use lazy imports to defer loading provider SDKs until they are actually instantiated
4. WHEN running in an environment with pre-installed SDKs (e.g., AWS Lambda with boto3), THE skye library SHALL use the existing SDK without requiring it as a dependency
5. THE skye library SHALL raise a clear ImportError with installation instructions WHEN a provider is used without its dependencies installed

### Requirement 2: Unified LLM Interface Implementation

**User Story:** As an application developer, I want to use different LLM providers through the same interface, so that I can switch providers without changing my code.

#### Acceptance Criteria

1. THE skye library SHALL implement ModelInterface for OpenAI, Anthropic, AWS Bedrock, Azure OpenAI, and Google Vertex AI
2. THE skye library SHALL support synchronous completion via the complete() method for all providers
3. THE skye library SHALL support asynchronous completion via the acomplete() method for all providers
4. THE skye library SHALL support streaming via the stream() method for all providers
5. THE skye library SHALL support async streaming via the astream() method for all providers

### Requirement 3: Embedding Model Support

**User Story:** As a developer building RAG applications, I want to generate embeddings using various providers through a unified interface, so that I can easily switch embedding models.

#### Acceptance Criteria

1. THE skye library SHALL implement VectorEncoderInterface for OpenAI embeddings, Bedrock Titan embeddings, Cohere embeddings, and Vertex AI embeddings
2. THE skye library SHALL support single text encoding via the encode() method
3. THE skye library SHALL support batch encoding via the encode_batch() method with automatic batching optimization
4. THE skye library SHALL support async encoding via aencode() and aencode_batch() methods
5. THE skye library SHALL return the vector dimension via get_vector_dimension() for each embedding model

### Requirement 4: Multimodal Input Support

**User Story:** As a developer building vision-enabled applications, I want to send images, audio, and video to multimodal models, so that I can build rich AI experiences.

#### Acceptance Criteria

1. THE skye library SHALL support image inputs in UserMessage content via URLs, base64 encoding, and file paths
2. THE skye library SHALL support audio inputs for models that accept audio (e.g., Gemini, GPT-4o)
3. THE skye library SHALL support video inputs for models that accept video (e.g., Gemini)
4. WHEN a provider does not support multimodal inputs, THE skye library SHALL raise a clear ProviderError indicating the limitation
5. THE skye library SHALL automatically detect and convert image formats to provider-specific requirements

### Requirement 5: Structured Output Implementation

**User Story:** As a developer, I want models to return structured, type-safe data validated against Pydantic schemas, so that I can reliably parse model outputs.

#### Acceptance Criteria

1. WHEN a CompletionRequest includes a response_schema, THE skye library SHALL configure the provider to return structured output
2. THE skye library SHALL use native structured output APIs when available (e.g., OpenAI's response_format)
3. WHEN native structured output is not available, THE skye library SHALL use function calling or prompt engineering with post-validation
4. THE skye library SHALL parse and validate the response against the provided Pydantic schema
5. WHEN validation fails, THE skye library SHALL raise a ValidationError with details about the mismatch

### Requirement 6: Function/Tool Calling Support

**User Story:** As a developer building agentic applications, I want models to call functions/tools defined in my application, so that agents can take actions.

#### Acceptance Criteria

1. THE skye library SHALL convert CapabilityInterface schemas to provider-specific function/tool definitions
2. THE skye library SHALL support function calling for OpenAI, Anthropic (tool use), Bedrock (tool use), and Vertex AI
3. WHEN a model requests a function call, THE skye library SHALL return the function name and arguments in a standardized format
4. THE skye library SHALL support parallel function calling when the provider supports it
5. THE skye library SHALL handle function call results and format them appropriately for the next model invocation

### Requirement 7: Provider-Specific Optimizations

**User Story:** As a developer, I want to leverage provider-specific features and optimizations, so that I can get the best performance and capabilities from each provider.

#### Acceptance Criteria

1. THE skye library SHALL support provider-specific parameters via the metadata field in CompletionRequest
2. THE skye library SHALL support Anthropic's thinking/reasoning features when available
3. THE skye library SHALL support OpenAI's o1/o3 reasoning models with appropriate parameter handling
4. THE skye library SHALL support Bedrock's Converse API for unified multi-model access
5. THE skye library SHALL support Vertex AI's safety settings and grounding features

### Requirement 8: Token Counting and Cost Estimation

**User Story:** As a product manager, I want accurate token counts and cost estimates for each API call, so that I can monitor and optimize spending.

#### Acceptance Criteria

1. THE skye library SHALL calculate token usage for all completion requests using provider-specific tokenizers
2. THE skye library SHALL estimate costs based on current provider pricing when pricing data is available
3. THE skye library SHALL include token usage in CompletionResponse metadata
4. THE skye library SHALL support custom pricing configurations for private or fine-tuned models
5. THE skye library SHALL provide a utility to calculate token counts before making API calls

### Requirement 9: Error Handling and Retry Logic

**User Story:** As a developer, I want robust error handling with automatic retries for transient failures, so that my application is resilient to temporary issues.

#### Acceptance Criteria

1. THE skye library SHALL wrap all provider-specific errors in ProviderError with context
2. THE skye library SHALL implement exponential backoff retry logic for rate limits and transient errors
3. THE skye library SHALL respect provider-specific retry-after headers
4. WHEN max retries are exceeded, THE skye library SHALL raise the final error with retry history
5. THE skye library SHALL log all retry attempts with appropriate severity levels

### Requirement 10: Provider Registry and Discovery

**User Story:** As a developer, I want to discover available providers and instantiate them dynamically, so that I can build flexible, configuration-driven applications.

#### Acceptance Criteria

1. THE skye library SHALL provide a ProviderRegistry that lists all installed providers
2. THE skye library SHALL support instantiating providers by name (e.g., "openai", "bedrock")
3. THE skye library SHALL validate provider configuration at instantiation time
4. WHEN a provider is not installed, THE skye library SHALL raise a clear error with installation instructions
5. THE skye library SHALL support registering custom provider implementations

### Requirement 11: Streaming Response Handling

**User Story:** As a developer building interactive applications, I want to stream model responses token-by-token, so that users see results immediately.

#### Acceptance Criteria

1. THE skye library SHALL yield StreamChunk objects for each token in streaming mode
2. THE skye library SHALL include finish_reason in the final StreamChunk
3. THE skye library SHALL support streaming function calls as they are generated
4. THE skye library SHALL handle streaming errors gracefully and yield error information
5. THE skye library SHALL support both sync and async streaming iterators

### Requirement 12: Lazy Dependency Loading

**User Story:** As a platform engineer deploying to AWS Lambda, I want to use Bedrock without installing boto3 as a dependency, so that I can leverage the pre-installed runtime libraries.

#### Acceptance Criteria

1. THE skye library SHALL use lazy imports for all provider SDKs
2. WHEN a provider SDK is already available in the environment, THE skye library SHALL use it without requiring installation
3. THE skye library SHALL only import provider SDKs when the provider is instantiated
4. WHEN a required SDK is missing, THE skye library SHALL raise ImportError with clear installation instructions
5. THE skye library SHALL document which dependencies are optional for each deployment environment

### Requirement 13: Request and Response Transformation

**User Story:** As a maintainer, I want clean separation between skye models and provider-specific formats, so that adding new providers is straightforward.

#### Acceptance Criteria

1. THE skye library SHALL implement RequestTransformer for each provider to convert CompletionRequest to provider format
2. THE skye library SHALL implement ResponseTransformer for each provider to convert provider responses to CompletionResponse
3. THE skye library SHALL handle provider-specific message format differences (e.g., Anthropic's separate system parameter)
4. THE skye library SHALL normalize provider-specific error codes to standard error types
5. THE skye library SHALL support bidirectional transformation for all message types

### Requirement 14: Multimodal Embedding Support

**User Story:** As a developer building multimodal search, I want to generate embeddings for images and text together, so that I can perform cross-modal retrieval.

#### Acceptance Criteria

1. THE skye library SHALL support multimodal embeddings for providers that offer them (e.g., Vertex AI multimodalembedding)
2. THE skye library SHALL accept image inputs in embedding requests
3. THE skye library SHALL return embeddings in the same format regardless of input modality
4. WHEN a provider does not support multimodal embeddings, THE skye library SHALL raise a clear error
5. THE skye library SHALL document which providers support multimodal embeddings

### Requirement 15: Provider Health and Monitoring

**User Story:** As an SRE, I want to monitor provider health and performance metrics, so that I can detect and respond to issues quickly.

#### Acceptance Criteria

1. THE skye library SHALL track success rate, latency, and error rate for each provider
2. THE skye library SHALL emit metrics via the ObserverInterface when configured
3. THE skye library SHALL include provider health information in error messages
4. THE skye library SHALL support health check endpoints for each provider
5. THE skye library SHALL log provider performance metrics at configurable intervals
