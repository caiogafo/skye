# Implementation Plan

- [x] 1. Update steering documentation to reflect current state
  - Update `.kiro/steering/nimbus-architecture.md` with current package structure
  - Add YAML configuration examples to steering docs
  - Update naming conventions to emphasize "Capability" over "Tool"
  - Add environment variable substitution guidelines
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2. Implement environment variable substitution utility
  - Create `substitute_env_vars()` function in `src/nimbus/config.py`
  - Support `${VAR_NAME}` syntax for environment variable references
  - Raise clear ConfigurationError when variable not found
  - Add caching to avoid repeated os.getenv() calls
  - Support recursive substitution in nested dictionaries
  - _Requirements: 2.2, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 2.1 Write unit tests for environment variable substitution
  - Test successful substitution with existing env vars
  - Test error handling for missing env vars
  - Test nested dictionary substitution
  - Test caching behavior
  - Test edge cases (empty strings, special characters)
  - _Requirements: 2.2, 6.1, 6.2, 6.3_

- [x] 3. Implement YAML configuration loading for routers
  - Create `load_router_config()` function in `src/nimbus/config.py`
  - Create `RouterConfig` Pydantic model
  - Integrate environment variable substitution
  - Add validation for required fields
  - Provide clear error messages for invalid YAML
  - _Requirements: 2.1, 2.3, 2.4_

- [x] 3.1 Write unit tests for YAML configuration loading
  - Test loading valid YAML configurations
  - Test error handling for invalid YAML syntax
  - Test error handling for missing required fields
  - Test environment variable substitution in YAML
  - Test validation of configuration values
  - _Requirements: 2.1, 2.4_

- [x] 4. Enhance ModelRouter with YAML support
  - Add `from_yaml()` class method to ModelRouter
  - Add `from_config_dict()` class method to ModelRouter
  - Update ModelTarget to support env var substitution in post_init
  - Add `_substitute_env_vars()` method to ModelTarget
  - Update documentation with YAML examples
  - _Requirements: 2.1, 2.5, 6.1, 6.4_

- [x] 4.1 Write integration tests for YAML router configuration
  - Test creating router from YAML file
  - Test router behavior with YAML-configured routes
  - Test fallback chains from YAML
  - Test retry policies from YAML
  - Test environment variable substitution in router config
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 5. Rename capability-related files
  - Rename `tool_models.py` to `capability_models.py`
  - Rename `tool_call_handler.py` to `capability_call_handler.py`
  - Rename `tool_transformer.py` to `capability_transformer.py`
  - Update all internal imports to use new names
  - _Requirements: 1.1, 1.2_

- [x] 6. Add transformation methods to BaseModelProvider
  - Add abstract `_transform_messages()` method to BaseModelProvider
  - Add abstract `_transform_capabilities()` method to BaseModelProvider
  - Add abstract `_extract_tool_calls()` method to BaseModelProvider
  - Update BaseModelProvider docstrings to document transformation responsibilities
  - _Requirements: 9.1, 9.5_

- [x] 6.1 Implement message transformation in OpenAIProvider
  - Move OpenAI message transformation logic from MessageTransformer to OpenAIProvider
  - Implement `_transform_messages()` method in OpenAIProvider
  - Handle all OpenAI-specific message format requirements
  - Remove OpenAI-specific logic from MessageTransformer
  - _Requirements: 9.1, 9.3_

- [x] 6.2 Implement message transformation in BedrockProvider
  - Move Bedrock message transformation logic from MessageTransformer to BedrockProvider
  - Implement `_transform_messages()` method in BedrockProvider
  - Handle all Bedrock-specific message format requirements
  - Remove Bedrock-specific logic from MessageTransformer
  - _Requirements: 9.1, 9.3_

- [x] 6.3 Implement capability transformation in OpenAIProvider
  - Move OpenAI capability transformation logic from CapabilityTransformer to OpenAIProvider
  - Implement `_transform_capabilities()` method in OpenAIProvider
  - Handle all OpenAI-specific tool format requirements
  - Remove OpenAI-specific logic from CapabilityTransformer
  - _Requirements: 9.1, 9.2_

- [x] 6.4 Implement capability transformation in BedrockProvider
  - Move Bedrock capability transformation logic from CapabilityTransformer to BedrockProvider
  - Implement `_transform_capabilities()` method in BedrockProvider
  - Handle all Bedrock-specific tool format requirements
  - Remove Bedrock-specific logic from CapabilityTransformer
  - _Requirements: 9.1, 9.2_

- [x] 6.5 Implement tool call extraction in OpenAIProvider
  - Implement `_extract_tool_calls()` method in OpenAIProvider
  - Move tool call extraction logic from response transformation
  - Return list of CapabilityCall objects
  - _Requirements: 9.1_

- [x] 6.6 Implement tool call extraction in BedrockProvider
  - Implement `_extract_tool_calls()` method in BedrockProvider
  - Move tool call extraction logic from response transformation
  - Return list of CapabilityCall objects
  - _Requirements: 9.1_

- [x] 6.7 Refactor MessageTransformer to delegation layer
  - Remove all provider-specific methods from MessageTransformer
  - Add `transform_for_provider()` delegation method
  - Update all call sites to use delegation pattern
  - Ensure MessageTransformer is provider-agnostic
  - _Requirements: 9.3, 9.4_

- [x] 6.8 Refactor CapabilityTransformer to delegation layer
  - Remove all provider-specific methods from CapabilityTransformer
  - Add `transform_for_provider()` delegation method
  - Update all call sites to use delegation pattern
  - Ensure CapabilityTransformer is provider-agnostic
  - _Requirements: 9.2, 9.4_

- [x] 6.9 Update provider _transform_request methods
  - Update OpenAIProvider._transform_request to use internal transformation methods
  - Update BedrockProvider._transform_request to use internal transformation methods
  - Remove direct calls to MessageTransformer and CapabilityTransformer
  - Ensure all provider-specific logic is self-contained
  - _Requirements: 9.1, 9.5_
- [x] 6.10 Remove legacy transformation code
  - Identify and delete all legacy message/capability transformation logic no longer used
  - Remove obsolete helper functions, data structures, and intermediate adapters
  - Clean up deprecated imports and dead code paths in providers and transformers
  - Ensure no call sites reference removed legacy logic
  - _Requirements: 9.1, 9.2, 9.3, 9.4*_
- [x] 6.11 Write unit tests for provider transformation encapsulation
  - Test that MessageTransformer has no provider-specific logic
  - Test that CapabilityTransformer has no provider-specific logic
  - Test that each provider handles all its own transformations
  - Test delegation pattern works correctly
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 7. Rename capability-related classes
  - Rename `ToolCall` to `CapabilityCall` in capability_models.py
  - Rename `ToolResult` to `CapabilityResult` in capability_models.py
  - Rename `ToolCallHandler` to `CapabilityCallHandler`
  - Rename `ToolTransformer` to `CapabilityTransformer`
  - Update all references throughout codebase
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 8. Update all documentation and docstrings
  - Replace "tool" with "capability" in all docstrings
  - Update examples in docstrings to use new names
  - Update module-level documentation
  - Update inline comments
  - Verify zero "Tool" references remain in capability code
  - _Requirements: 1.3, 1.5_

- [x] 9. Create new test directory structure
  - Create `tests/stress/` directory
  - Create subdirectories in `tests/unit/` for better organization
  - Create subdirectories in `tests/integration/` for better organization
  - Create `tests/fixtures/sample_configs.py` for YAML fixtures
  - Add README files explaining test organization
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 10. Validate provider transformation consolidation
  - Verify all provider-specific transformation logic is in provider client classes
  - Ensure no provider-specific code exists in core library modules (router, capabilities, completion)
  - Verify MessageTransformer and CapabilityTransformer only delegate to providers
  - Check that adding a new provider requires no changes to core library code
  - Document provider transformation architecture in code comments
  - Remove any legacy code related with Transformations elsewhere in the codebase
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [x] 11. Move and reorganize existing tests
  - Move unit tests to appropriate subdirectories
  - Move integration tests to appropriate subdirectories
  - Update test imports after file moves
  - Update tests to use new Capability* names
  - Ensure all tests still pass after reorganization
  - _Requirements: 8.1, 8.2, 8.4_

- [x] 12. Create stress tests for concurrent routing
  - Create `tests/stress/test_concurrent_routing.py`
  - Test router with 100+ concurrent requests
  - Test rate limit tracking under concurrent load
  - Measure and report performance metrics
  - Test for race conditions in request tracking
  - _Requirements: 7.1, 7.2_

- [x] 13. Create stress tests for rate limiting
  - Create `tests/stress/test_rate_limiting.py`
  - Test TPM/RPM enforcement under load
  - Test rate limit reset behavior
  - Test pre-call rate limit checks
  - Measure throughput and latency
  - _Requirements: 7.2_

- [x] 14. Create stress tests for capability execution
  - Create `tests/stress/test_capability_load.py`
  - Test concurrent capability execution
  - Test capability registry under load
  - Test MCP capability performance
  - Measure execution latency distribution
  - _Requirements: 7.4_

- [x] 15. Create stress tests for failover scenarios
  - Create `tests/stress/test_failover.py`
  - Test router behavior when models fail
  - Test cooldown mechanism under load
  - Test fallback chain execution
  - Measure failover latency
  - _Requirements: 7.3_

- [x] 16. Reorganize examples directory
  - Create `examples/basic/` directory with README
  - Create `examples/capabilities/` directory with README
  - Create `examples/providers/` directory with README
  - Create `examples/routing/` directory with README
  - Create `examples/advanced/` directory with README
  - Move existing examples to appropriate directories
  - Update all examples to use Capability* terminology
  - _Requirements: 4.1, 4.5_

- [x] 16.1 Remove ProviderRegistry and standardize provider interface
  - Remove all ProviderRegistry usage from codebase
  - Ensure all code uses `nimbus.provider()` interface exclusively
  - Update provider.complete() to accept parameters directly (not CompletionRequest objects)
  - Update all examples to use direct parameter passing
  - Update all tests to use `nimbus.provider()` interface
  - Update documentation to remove ProviderRegistry references
  - Update README.md to show only `nimbus.provider()` usage
  - Deprecate or remove ProviderRegistry class
  - _Requirements: 4.1, 4.5_

- [x] 16.2 Remove remaining transformer files and consolidate into providers
  - Remove `src/nimbus/providers/transformers.py` (all logic should be in provider clients)
  - Remove `src/nimbus/interfaces/message_transformer.py` (if still provider-specific)
  - Remove `src/nimbus/capabilities/capability_transformer.py` (if still provider-specific)
  - Verify all transformation logic is in provider client classes only
  - Ensure no standalone transformer modules exist outside provider clients
  - Update any imports that reference removed transformer files
  - Verify providers handle all transformations internally via _transform_messages(), _transform_capabilities(), etc.
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 17. Create YAML routing examples
  - Create `examples/routing/yaml_config.py`
  - Create sample YAML configuration file
  - Demonstrate environment variable usage
  - Demonstrate multiple routing strategies
  - Add comprehensive comments
  - _Requirements: 4.3_

- [ ] 18. Create capability examples
  - Create `examples/capabilities/local_function.py`
  - Create `examples/capabilities/remote_api.py`
  - Create `examples/capabilities/mcp_server.py`
  - Add README explaining each capability type
  - _Requirements: 4.2_

- [ ] 19. Update main examples README
  - Create comprehensive `examples/README.md`
  - Document all example categories
  - Add quick start guide
  - Link to individual category READMEs
  - _Requirements: 4.5_

- [ ] 20. Add comprehensive unit tests for capabilities
  - Ensure all capability types have unit tests
  - Test capability registration and lookup
  - Test capability schema generation
  - Test capability execution (sync and async)
  - Achieve 80%+ coverage on capability module
  - _Requirements: 3.2_

- [ ] 21. Add comprehensive unit tests for router
  - Test all routing strategies
  - Test health tracking
  - Test rate limiting
  - Test cooldown mechanism
  - Test fallback chains
  - Achieve 80%+ coverage on router module
  - _Requirements: 3.3_

- [ ] 22. Add comprehensive unit tests for providers
  - Test all provider implementations
  - Test provider registry
  - Test error handling
  - Test retry logic
  - Achieve 80%+ coverage on provider module
  - _Requirements: 3.4_

- [ ] 23. Checkpoint - Ensure all tests pass
  - Run full test suite
  - Verify test coverage meets 80% goal
  - Fix any failing tests
  - Ensure all examples run successfully
  - Verify zero "Tool" references in capability code
  - Ask user if questions arise

- [ ]* 24. Update main README
  - Add YAML configuration example
  - Update quick start with Capability terminology
  - Add breaking changes notice (v1.0.0)
  - Update feature list
  - Add links to examples

- [ ] 25. Final validation and cleanup
  - Run linters (ruff, black, mypy)
  - Fix any type errors
  - Ensure all docstrings are complete
  - Verify all imports work correctly
  - Verify zero "Tool" terminology in capability code
  - Run full test suite one final time

- [x] 26. Fix failing transformer tests
  - Update tests/unit/utils/test_transformers.py to use delegation pattern
  - Remove tests for provider-specific methods (to_openai_format, to_anthropic_format, etc.)
  - Add tests for transform_for_provider delegation method
  - Ensure tests verify delegation to provider._transform_messages()
  - _Requirements: 9.3, 9.4_

- [x] 27. Fix failing provider tool calling tests
  - Update tests/unit/providers/test_openai_provider.py tool calling tests
  - Update tests/unit/providers/test_vertex_provider.py tool calling tests
  - Ensure tests use provider's internal _transform_capabilities() method
  - Verify capability transformation is encapsulated in provider
  - _Requirements: 9.1, 9.2_

- [x] 28. Fix failing retry logic tests
  - Update tests/unit/providers/test_retry_logic.py
  - Ensure retry decorator tests work with new provider structure
  - Verify retry logic preserves exception chains
  - Test retry with streaming responses
  - _Requirements: 3.4_

- [x] 29. Fix failing router YAML integration tests
  - Update tests/unit/routes/test_router_yaml_integration.py
  - Fix from_config_dict tests
  - Fix from_yaml tests with environment variables
  - Ensure YAML configuration loading works correctly
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 30. Fix failing completion request tests
  - Update tests/unit/test_completion.py
  - Fix capabilities field tests
  - Fix tool_choice validation tests
  - Ensure CompletionRequest model validation works
  - _Requirements: 1.2, 1.3_

- [ ] 31. Fix failing exports test
  - Update tests/unit/test_exports.py
  - Ensure __all__ list matches actual exports
  - Verify all public APIs are properly exported
  - _Requirements: 1.5_
