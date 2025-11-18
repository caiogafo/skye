# Implementation Plan: nimbus

## Overview

This implementation plan breaks down the development of nimbus (base package) into discrete, incremental tasks. Each task builds on previous work and focuses on implementing specific interfaces, models, or functionality. The plan follows a bottom-up approach: foundational models and exceptions first, then interfaces, and finally configuration and utilities.

## Task List

- [x] 1. Set up project structure and dependencies
  - Create pyproject.toml with uv/PEP 621 configuration
  - Define Python 3.10+ requirement
  - Add base dependencies: pydantic >=2.0, pyyaml >=6.0
  - Add optional dependencies for extras (boto3, openai, anthropic, redis, etc.)
  - Configure [project.optional-dependencies] for all optional components
  - Add dev dependencies in [dependency-groups]: pytest, pytest-asyncio, pytest-cov, black, ruff, mypy
  - Create src/nimbus package structure with __init__.py files
  - Create directories for optional extras (providers/, agents/, memory/, etc.)
  - Set up tests/ directory structure
  - Create Makefile with check target using UV commands: `uv run pytest`, `uv run mypy`, `uv run ruff check`, `uv run black --check`
  - _Requirements: All requirements (foundational setup)_

- [x] 2. Implement core exception hierarchy
  - [x] 2.1 Create base NimbusError exception class
    - Implement __init__ with message and details dict
    - Add proper string representation
    - _Requirements: 6.1, 6.4_
  
  - [x] 2.2 Create specific exception types
    - Implement ProviderError with provider context
    - Implement ConfigurationError
    - Implement ValidationError with field information
    - Implement CapabilityExecutionError
    - _Requirements: 6.2, 6.3_
  
  - [x] 2.3 Add exception logging integration
    - Implement logging in exception __init__
    - Add severity level mapping
    - _Requirements: 6.5_

- [x] 3. Implement message types and models
  - [x] 3.1 Create NimbusMessage base class
    - Define Pydantic model with content, role, metadata, id, timestamp
    - Implement to_dict() method
    - Implement from_dict() class method
    - Implement format_for_provider() method
    - _Requirements: 1.1, 4.1, 4.5_
  
  - [x] 3.2 Create specific message types
    - Implement UserMessage
    - Implement AssistantMessage with capability_calls
    - Implement SystemMessage
    - Implement CapabilityMessage with capability_id and capability_name
    - Override format_for_provider() for provider-specific formatting
    - _Requirements: 1.1, 4.1_
  
  - [x] 3.3 Create ContentChunk model
    - Define Pydantic model with text, metadata, chunk_id, source
    - Implement __str__ method
    - _Requirements: 1.1_

- [x] 4. Implement completion request/response models
  - [x] 4.1 Create TokenUsage model
    - Define Pydantic model with prompt_tokens, completion_tokens, total_tokens
    - _Requirements: 4.2, 7.1_
  
  - [x] 4.2 Create CompletionRequest model
    - Define Pydantic model with messages, model, temperature, max_tokens, etc.
    - Add response_format and response_schema fields for structured outputs
    - Add capabilities field (renamed from tools)
    - Add validation for temperature range (0.0-2.0)
    - Add validation for top_p range (0.0-1.0)
    - _Requirements: 2.3, 4.1, 10.2_
  
  - [x] 4.3 Create CompletionResponse model
    - Define Pydantic model with id, model, provider, content, usage, etc.
    - Add structured_output field for parsed structured responses
    - Implement get_output() method
    - _Requirements: 2.5, 4.1, 4.2, 4.3, 7.3_
  
  - [x] 4.4 Create StreamChunk model
    - Define Pydantic model for streaming response chunks
    - _Requirements: 2.4, 4.4_

- [x] 5. Implement configuration models
  - [x] 5.1 Create rate limiting configuration
    - Implement RateLimitConfig Pydantic model
    - Add requests_per_minute, tokens_per_minute fields
    - Add requests_per_day, tokens_per_day fields
    - Write unit test in tests/unit/test_config_models.py
    - Test field validation and default values
    - Run with `uv run pytest tests/unit/test_config_models.py::test_rate_limit_config -v`
    - _Requirements: 3.1, 8.5_
  
  - [x] 5.2 Create retry configuration
    - Implement RetryConfig Pydantic model
    - Add max_retries, retry_after_seconds fields
    - Add exponential_backoff flag
    - Add retry_on_errors list
    - Write unit test in tests/unit/test_config_models.py
    - Test default values and validation
    - Run with `uv run pytest tests/unit/test_config_models.py::test_retry_config -v`
    - _Requirements: 3.3_
  
  - [x] 5.3 Create cooldown configuration
    - Implement CooldownConfig Pydantic model
    - Add enabled flag, allowed_fails_per_minute
    - Add cooldown_duration_seconds
    - Write unit test in tests/unit/test_config_models.py
    - Test cooldown logic and validation
    - Run with `uv run pytest tests/unit/test_config_models.py::test_cooldown_config -v`
    - _Requirements: 3.3_
  
  - [x] 5.4 Create ModelConfig
    - Implement comprehensive ModelConfig Pydantic model
    - Add basic fields: model_id, provider, api_key, api_base
    - Add rate_limits, retry_config, cooldown_config
    - Add fallback_models list
    - Add weight, priority, tags for routing
    - Add cost tracking fields
    - Write unit test in tests/unit/test_config_models.py
    - Test all fields, nested configs, and validation
    - Run with `uv run pytest tests/unit/test_config_models.py::test_model_config -v`
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 7.4_
  
  - [x] 5.5 Create NimbusConfig
    - Implement global configuration model
    - Add log_level, enable_telemetry fields
    - Add models dict, plugins dict
    - Add router configuration fields
    - Write unit test in tests/unit/test_config_models.py
    - Test global config with nested model configs
    - Run with `uv run pytest tests/unit/test_config_models.py::test_nimbus_config -v`
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [x] 6. Implement configuration loading system
  - [x] 6.1 Create ConfigLoader class
    - Implement load() method with multi-source support
    - Load from YAML/JSON files
    - Load from environment variables (NIMBUS_ prefix)
    - Apply code overrides
    - Implement precedence: code > environment > file
    - Write unit test in tests/unit/test_config_loader.py
    - Test loading from each source (file, env, code)
    - Test precedence order with multiple sources
    - Create test fixtures in tests/fixtures/ (sample_config.yaml, sample_config.json)
    - Run with `uv run pytest tests/unit/test_config_loader.py::test_config_loader -v`
    - Verify with `uv run python -c "from nimbus.config import ConfigLoader; print(ConfigLoader.load())"`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [x] 6.2 Add configuration validation
    - Validate all config values using Pydantic
    - Raise ConfigurationError for invalid values
    - Write unit test in tests/unit/test_config_loader.py
    - Test validation errors for invalid configs
    - Test that ConfigurationError is raised with proper context
    - Run with `uv run pytest tests/unit/test_config_loader.py::test_config_validation -v`
    - _Requirements: 8.5_

- [x] 7. Implement core interfaces
  - [x] 7.1 Create ModelInterface
    - Define abstract base class with ABC
    - Add complete() method signature
    - Add stream() method signature
    - Add acomplete() async method signature
    - Add astream() async method signature
    - Add get_model_info() method signature
    - Reference MCP server patterns for interface design (see ~/.kiro/settings/mcp.json)
    - Write unit test in tests/unit/test_interfaces.py
    - Create mock implementation to test interface compliance
    - Test that all abstract methods are defined
    - Test that incomplete implementations raise TypeError
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_model_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.model import ModelInterface; print(ModelInterface.__abstractmethods__)"`
    - _Requirements: 1.1, 2.1, 2.3, 2.4_
  
  - [x] 7.2 Create PromptBuilderInterface
    - Define abstract base class
    - Add render() method signature
    - Add register_template() method signature
    - Add get_template() method signature
    - Check Promptify MCP for prompt template patterns
    - Reference Promptify's Pipeline and Prompter design
    - Write unit test in tests/unit/test_interfaces.py
    - Create mock implementation to test interface
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_prompt_builder_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.prompt import PromptBuilderInterface; print(PromptBuilderInterface.__abstractmethods__)"`
    - _Requirements: 1.2_
  
  - [x] 7.3 Create CapabilityInterface
    - Define abstract base class
    - Create CapabilitySchema Pydantic model
    - Add get_schema() method signature
    - Add execute() method signature
    - Add aexecute() async method signature
    - Reference LangChain's tool/function calling patterns
    - Write unit test in tests/unit/test_interfaces.py
    - Test CapabilitySchema model validation
    - Create mock capability implementation
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_capability_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.capability import CapabilityInterface; print(CapabilityInterface.__abstractmethods__)"`
    - _Requirements: 1.3_
  
  - [x] 7.4 Create MemoryInterface
    - Define abstract base class
    - Create MemoryEntry Pydantic model
    - Add store() method signature
    - Add retrieve() method signature
    - Add get_by_id() method signature
    - Add delete() method signature
    - Write unit test in tests/unit/test_interfaces.py
    - Test MemoryEntry model validation
    - Create mock memory implementation
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_memory_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.memory import MemoryInterface; print(MemoryInterface.__abstractmethods__)"`
    - _Requirements: 1.4_
  
  - [x] 7.5 Create SafetyFilterInterface
    - Define abstract base class
    - Create SafetyResult Pydantic model
    - Add validate_input() method signature
    - Add validate_output() method signature
    - Add get_policies() method signature
    - Write unit test in tests/unit/test_interfaces.py
    - Test SafetyResult model validation
    - Create mock safety filter implementation
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_safety_filter_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.safety import SafetyFilterInterface; print(SafetyFilterInterface.__abstractmethods__)"`
    - _Requirements: 1.5_
  
  - [x] 7.6 Create ObserverInterface
    - Define abstract base class
    - Create EventType enum
    - Add log_event() method signature
    - Add record_metric() method signature
    - Add start_trace() method signature
    - Add end_trace() method signature
    - Reference OpenTelemetry patterns for tracing
    - Write unit test in tests/unit/test_interfaces.py
    - Test EventType enum values
    - Create mock observer implementation
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_observer_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.observer import ObserverInterface; print(ObserverInterface.__abstractmethods__)"`
    - _Requirements: 5.2, 9.1, 9.2, 9.3_
  
  - [x] 7.7 Create StorageAdapterInterface
    - Define abstract base class
    - Add save() method signature
    - Add query() method signature
    - Add vector_search() method signature
    - Add delete() method signature
    - Write unit test in tests/unit/test_interfaces.py
    - Create mock storage adapter implementation
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_storage_adapter_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.storage import StorageAdapterInterface; print(StorageAdapterInterface.__abstractmethods__)"`
    - _Requirements: 5.3_
  
  - [x] 7.8 Create PluginInterface
    - Define abstract base class
    - Add initialize() method signature
    - Add shutdown() method signature
    - Add get_metadata() method signature
    - Reference MCP server lifecycle patterns (initialize/shutdown)
    - Write unit test in tests/unit/test_interfaces.py
    - Create mock plugin implementation
    - Test plugin lifecycle (initialize/shutdown)
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_plugin_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.plugin import PluginInterface; print(PluginInterface.__abstractmethods__)"`
    - _Requirements: 5.1, 5.4_
  
  - [x] 7.9 Create EventHandlerInterface
    - Define abstract base class
    - Add on_model_invoke_start() method signature
    - Add on_model_invoke_end() method signature
    - Add on_model_invoke_error() method signature
    - Add on_capability_invoke_start() method signature
    - Add on_capability_invoke_end() method signature
    - Add on_capability_invoke_error() method signature
    - Add on_execution_step() method signature
    - Add on_execution_complete() method signature
    - Reference LangChain's callback handler patterns
    - Write unit test in tests/unit/test_interfaces.py
    - Create mock event handler implementation
    - Test all event handler hooks
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_event_handler_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.event_handler import EventHandlerInterface; print(EventHandlerInterface.__abstractmethods__)"`
    - _Requirements: 9.2, 9.5_
  
  - [x] 7.10 Create VectorEncoderInterface
    - Define abstract base class
    - Add encode() method signature
    - Add encode_batch() method signature
    - Add aencode() async method signature
    - Add aencode_batch() async method signature
    - Add get_vector_dimension() method signature
    - Write unit test in tests/unit/test_interfaces.py
    - Create mock vector encoder implementation
    - Test sync and async methods
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_vector_encoder_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.vector_encoder import VectorEncoderInterface; print(VectorEncoderInterface.__abstractmethods__)"`
    - _Requirements: 1.1_
  
  - [x] 7.11 Create ContentReaderInterface
    - Define abstract base class
    - Add read() method signature
    - Add read_stream() method signature
    - Add aread() async method signature
    - Add get_reader_metadata() method signature
    - Reference LangChain's document loader patterns (but use Nimbus naming)
    - Write unit test in tests/unit/test_interfaces.py
    - Create mock content reader implementation
    - Test sync, async, and streaming methods
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_content_reader_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.content_reader import ContentReaderInterface; print(ContentReaderInterface.__abstractmethods__)"`
    - _Requirements: 1.1_
  
  - [x] 7.12 Create ModelRouterInterface
    - Define abstract base class
    - Create RoutingStrategy enum
    - Add register_model() method signature
    - Add select_model() method signature
    - Add route_request() method signature
    - Add aroute_request() async method signature
    - Add mark_model_failed() method signature
    - Add get_model_health() method signature
    - Add set_routing_strategy() method signature
    - Reference LiteLLM's router patterns for load balancing
    - Write unit test in tests/unit/test_interfaces.py
    - Test RoutingStrategy enum values
    - Create mock router implementation
    - Test routing and fallback logic
    - Run with `uv run pytest tests/unit/test_interfaces.py::test_model_router_interface -v`
    - Verify with `uv run python -c "from nimbus.interfaces.router import ModelRouterInterface; print(ModelRouterInterface.__abstractmethods__)"`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 8. Implement validation utilities
  - [x] 8.1 Create interface validation utilities
    - Implement function to validate interface compliance at runtime
    - Check that all abstract methods are implemented
    - Raise ValidationError for non-compliant implementations
    - Write unit test in tests/unit/test_validation.py
    - Test with compliant and non-compliant implementations
    - Test that ValidationError includes helpful context
    - Run with `uv run pytest tests/unit/test_validation.py::test_interface_compliance -v`
    - _Requirements: 5.4, 10.4_
  
  - [x] 8.2 Create schema generation utilities
    - Implement function to convert Pydantic models to JSON Schema
    - Support for structured output schema generation
    - Use Pydantic's model_json_schema() method
    - Write unit test in tests/unit/test_validation.py
    - Test schema generation for various message types
    - Test nested model schema generation
    - Run with `uv run pytest tests/unit/test_validation.py::test_schema_generation -v`
    - Verify with `uv run python -c "from nimbus.utils.validation import generate_schema; from nimbus.messages import UserMessage; print(generate_schema(UserMessage))"`
    - _Requirements: 10.2_

- [x] 9. Create package exports and documentation
  - [x] 9.1 Configure __init__.py exports
    - Export all interfaces from nimbus.interfaces
    - Export all models from nimbus.messages, nimbus.completion, nimbus.config
    - Export all exceptions from nimbus.exceptions
    - Export ConfigLoader from nimbus.config
    - Write unit test in tests/unit/test_exports.py
    - Test that all expected symbols are importable from nimbus
    - Test that __all__ is properly defined
    - Run with `uv run pytest tests/unit/test_exports.py -v`
    - Verify with `uv run python -c "from nimbus import ModelInterface, UserMessage, NimbusError, ConfigLoader; print('All imports successful')"`
    - _Requirements: 10.1_
  
  - [x] 9.2 Write README.md
    - Add project overview
    - Add installation instructions with uv: `uv pip install nimbus`, `uv pip install nimbus[bedrock]`
    - Add basic usage examples
    - Add link to full documentation
    - Reference MCP server structure for documentation patterns
    - No unit test required (documentation)
    - _Requirements: All_
  
  - [x] 9.3 Add type hints verification
    - Run mypy on all source files with `uv run mypy src/nimbus --strict`
    - Fix any type hint issues
    - Add mypy to Makefile check target: `uv run mypy src/nimbus`
    - Write test script in tests/test_type_hints.sh
    - Script should run mypy and fail if errors found
    - Run with `uv run mypy src/nimbus --strict`
    - _Requirements: 10.1_

- [ ]* 10. Write comprehensive tests
  - [ ]* 10.1 Write exception tests
    - Test NimbusError creation and string representation
    - Test specific exception types with context
    - Test exception logging
    - Run with `uv run pytest tests/unit/test_exceptions.py -v`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 10.2 Write message model tests
    - Test NimbusMessage creation and validation
    - Test to_dict() and from_dict() methods
    - Test format_for_provider() for different providers
    - Test all message type subclasses
    - Run with `uv run pytest tests/unit/test_messages.py -v`
    - _Requirements: 1.1, 4.1, 4.5_
  
  - [ ]* 10.3 Write completion model tests
    - Test CompletionRequest validation
    - Test CompletionResponse with structured outputs
    - Test StreamChunk model
    - Test TokenUsage model
    - Run with `uv run pytest tests/unit/test_completion.py -v`
    - _Requirements: 2.3, 2.4, 4.1, 4.2, 4.3, 4.4, 7.1, 7.3_
  
  - [ ]* 10.4 Write configuration tests
    - Test ConfigLoader with different sources
    - Test configuration precedence
    - Test environment variable loading
    - Test YAML/JSON file loading
    - Test configuration validation
    - Run with `uv run pytest tests/unit/test_config.py -v`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 10.5 Write interface compliance tests
    - Test interface validation utility
    - Create mock implementations of each interface
    - Test that compliant implementations pass validation
    - Test that non-compliant implementations fail validation
    - Run with `uv run pytest tests/unit/test_interfaces.py -v`
    - _Requirements: 5.4, 10.4_
  
  - [ ]* 10.6 Write integration tests
    - Test plugin registration and lifecycle
    - Test configuration loading with multiple sources
    - Test structured output schema generation
    - Run with `uv run pytest tests/integration/ -v`
    - _Requirements: 5.1, 5.4, 5.5, 8.1, 8.2, 8.3, 8.4_

## Implementation Notes

### UV Usage

All Python commands should be run using UV:
- **Testing**: `uv run pytest tests/ -v`
- **Type checking**: `uv run mypy src/nimbus --strict`
- **Linting**: `uv run ruff check src/ tests/`
- **Formatting**: `uv run black src/ tests/`
- **Quick validation**: `uv run python -c "import nimbus; print('OK')"`
- **Running scripts**: `uv run python script.py`

### MCP Reference Implementation

When designing interfaces and implementations, reference MCP server patterns:
- **Interface Design**: Check MCP server structure in ~/.kiro/settings/mcp.json
- **Command Patterns**: MCP servers use `command` + `args` pattern (e.g., `uv --directory <path> run --with <deps> mcp run server.py`)
- **Configuration**: MCP uses JSON config with env vars, autoApprove lists, and disabled flags
- **Promptify Reference**: For PromptBuilderInterface, reference Promptify's Pipeline and Prompter patterns
- **LangChain Reference**: For general LLM patterns (but use Nimbus naming conventions)
- **LiteLLM Reference**: For provider abstraction patterns

### Structured Output Implementation

When implementing structured output support:
1. Use Pydantic's `model_json_schema()` to generate JSON schemas
2. Store the schema in CompletionRequest.response_format
3. Parse and validate responses using the Pydantic model
4. Handle provider-specific differences in ModelInterface implementations

### Router Implementation

The ModelRouterInterface is defined in core but will be implemented in a separate component (likely nimbus-agents or a dedicated nimbus-router). The core only provides the contract.

### Testing Strategy

- Focus on unit tests for models and utilities
- Use mock implementations for interface testing
- Integration tests should verify multi-source configuration loading
- Optional test tasks are marked with * and focus on comprehensive coverage
- All tests run with `uv run pytest` for consistency

### Dependencies

- All tasks in section 1 must complete before other tasks
- Section 2 (exceptions) should complete before section 7 (interfaces)
- Section 3 (messages) and 4 (completion models) should complete before section 7
- Section 5 (config models) should complete before section 6 (config loading)
- Section 7 (interfaces) can be done in parallel once dependencies are met
- Section 8 (utilities) depends on sections 3, 4, 5, 7
- Section 9 (exports/docs) should be done last
- Section 10 (tests) can be done incrementally alongside implementation

### Code Quality

- All code must have complete type hints
- All public APIs must have docstrings
- Follow PEP 8 style guidelines (enforced by black and ruff)
- Maintain test coverage above 80% for non-optional tests
- Run `uv run mypy src/nimbus --strict` before committing
- Use `uv run black src/ tests/` to format code
- Use `uv run ruff check src/ tests/` to lint code

### Quick Validation Commands

After implementing each task, use these UV commands to validate:

```bash
# Import validation
uv run python -c "from nimbus import ModelInterface, UserMessage; print('OK')"

# Type checking
uv run mypy src/nimbus --strict

# Run tests
uv run pytest tests/unit/ -v

# Code formatting
uv run black src/ tests/ --check

# Linting
uv run ruff check src/ tests/

# Full validation (add to Makefile)
uv run pytest && uv run mypy src/nimbus --strict && uv run ruff check src/ tests/
```

### MCP Integration References

The following MCP servers are available for reference patterns:
- **Promptify**: Template and prompt management patterns
- **LangChain**: General LLM patterns, callbacks, document loaders
- **LiteLLM**: Provider abstraction and routing patterns
- **SDK-Python**: Python SDK structure and interface design

Access MCP documentation via:
- Promptify: Check MCP for prompt template patterns
- LangChain: Check MCP for callback and tool patterns
- LiteLLM: Check MCP for router and provider patterns

### Testing Requirements Summary

**IMPORTANT**: For each implementation task, you MUST:

1. **Write the unit test FIRST** in the appropriate test file (tests/unit/)
2. **Implement the code** to make the test pass
3. **Run the test** using the specified `uv run pytest` command
4. **Verify** the implementation works as expected

**Test File Organization**:
- `tests/unit/test_exceptions.py` - Exception hierarchy tests
- `tests/unit/test_messages.py` - Message model tests
- `tests/unit/test_completion.py` - Completion request/response tests
- `tests/unit/test_config_models.py` - Configuration model tests
- `tests/unit/test_config_loader.py` - ConfigLoader tests
- `tests/unit/test_interfaces.py` - All interface tests (one file for all interfaces)
- `tests/unit/test_validation.py` - Validation utility tests
- `tests/unit/test_exports.py` - Package export tests
- `tests/fixtures/` - Test fixtures (sample configs, mock data)

**Test Execution Pattern**:
```bash
# Run specific test
uv run pytest tests/unit/test_file.py::test_function_name -v

# Run all tests in a file
uv run pytest tests/unit/test_file.py -v

# Run all unit tests
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest tests/unit/ --cov=src/nimbus --cov-report=term-missing
```

**Test Quality Standards**:
- Each test should be focused on a single behavior
- Use descriptive test names (test_user_message_creation, test_invalid_temperature_raises_error)
- Use pytest.mark.parametrize for testing multiple cases
- Use pytest.mark.asyncio for async tests
- Mock external dependencies
- Test both success and failure cases
- Aim for 80%+ code coverage on core functionality
