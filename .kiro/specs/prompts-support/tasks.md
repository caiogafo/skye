# Implementation Plan: Prompts Support

## Overview

This implementation plan converts the comprehensive prompts support design into discrete coding tasks. The implementation will create a production-ready Jinja2-based prompt builder that integrates seamlessly with Skye architecture, providing template management, few-shot learning, multimodal content support, and structured output generation.

The plan starts with interfaces, mocks, and samples to validate the user experience before implementing the full functionality.

## Tasks

- [ ] 1. Create interfaces, mocks, and samples for user experience validation
  - [x] 1.1 Set up prompts module structure and imports
    - Create src/skye/prompts/ directory structure
    - Set up __init__.py with proper exports
    - Add imports for PromptBuilderInterface from core
    - _Requirements: 11.1_
  
  - [x] 1.2 Create mock implementation of PromptBuilderInterface
    - Implement MockPromptBuilder class with all interface methods
    - Add simple in-memory template storage for testing
    - Implement basic variable substitution without Jinja2
    - _Requirements: 1.1, 2.1_
  
  - [x] 1.3 Create comprehensive usage samples and examples
    - Write sample scripts showing basic template registration and rendering
    - Add examples for few-shot learning with mock data
    - Create multimodal content examples (images, structured output)
    - Demonstrate message role management and template composition
    - _Requirements: 1.1, 2.1, 4.1, 5.1, 6.1, 7.3_
  
  - [x] 1.4 Create sample templates and test data
    - Add sample Jinja2 templates for common use cases (NER, summarization, chat)
    - Create test datasets for few-shot examples
    - Add sample multimodal content (image URLs, structured schemas)
    - _Requirements: 4.1, 5.1, 8.1_

- [ ] 2. Checkpoint - Validate user experience and API design
  - Review samples with user to ensure API feels intuitive
  - Validate that the interface covers all intended use cases
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Rewrite the stale `examples/prompts/` set off Jinja2 (D20, Requirement 30.9)
  - Note: this whole spec (introduction, glossary, design, tasks above) is legacy pre-D20 and still describes a Jinja2 + pydantic builder; it is migrated in place when `prompts` is picked up (folder to be renamed `2-services-prompts`). Separately from that migration, the twelve files under `examples/prompts/` are stale: they refer to "Jinja2" features, use a `MockPromptBuilder` alias, and manipulate `sys.path`. Rewrite them against the standard-library engine (`{{ }}`, `if`/`elif`/`else`, `for`, filters; no macros, inheritance, include, or variable assignment per D20 / Requirement 30.9), drop the Jinja2 wording and the `MockPromptBuilder` alias, and import normally without `sys.path` hacks. Keep each runnable under `tests/examples`. Found 2026-11-03 in the example-coverage review (`.agents/tasks/example-coverage-gaps.md`).
  - _Requirements: 24.2, 24.3, 30.9; D20_

- [ ] 3. Implement template registry and caching system
  - [ ] 3.1 Create TemplateRegistry class with versioning support
    - Implement template storage with name:version keys
    - Add LRU cache for compiled Jinja2 templates
    - Support template metadata storage and retrieval
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ]* 3.2 Write property test for template registry
    - **Property 1: Template round-trip consistency**
    - **Validates: Requirements 1.1, 1.2**
  
  - [ ] 3.3 Implement template compilation and caching
    - Create TemplateCache class with LRU eviction
    - Add thread-safe template compilation
    - Implement cache hit/miss tracking for performance
    - _Requirements: 12.1, 12.2, 12.5_

- [ ] 4. Implement variable validation and management
  - [ ] 4.1 Create VariableValidator class
    - Implement variable extraction from Jinja2 templates using meta.find_undeclared_variables
    - Add default values and callable defaults support
    - Implement allowed missing variables functionality
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 4.2 Write property test for variable validation
    - **Property 2: Variable merging precedence**
    - **Validates: Requirements 2.4, 3.1**
  
  - [ ] 4.3 Implement partial variable binding
    - Create partial builder functionality with bound variables
    - Support callable defaults for dynamic values (timestamps, etc.)
    - Ensure immutability of original builder when creating partials
    - _Requirements: 3.5_

- [ ] 5. Implement core Jinja2PromptBuilder class
  - [ ] 5.1 Create main Jinja2PromptBuilder implementation
    - Implement all PromptBuilderInterface methods
    - Set up Jinja2 environment with custom configuration
    - Add template registration from strings and files
    - _Requirements: 1.1, 1.2, 1.5, 1.6_
  
  - [ ]* 5.2 Write property test for template rendering
    - **Property 3: Template rendering consistency**
    - **Validates: Requirements 2.1, 2.3**
  
  - [ ] 5.3 Implement template variable extraction and validation
    - Add get_template_variables method using Jinja2 meta
    - Implement template validation with syntax checking
    - Add comprehensive error handling with context
    - _Requirements: 3.4, 10.1, 10.2_

- [ ] 6. Checkpoint - Ensure core functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement few-shot learning support
  - [ ] 7.1 Create ExampleSelector base class and implementations
    - Implement FixedExampleSelector for static examples
    - Create RandomExampleSelector with seeded randomization
    - Add basic SemanticExampleSelector with TF-IDF similarity
    - _Requirements: 4.1, 4.2, 4.4, 4.5, 4.6_
  
  - [ ]* 7.2 Write property test for example selection
    - **Property 4: Example selection consistency**
    - **Validates: Requirements 4.4, 4.5, 4.6**
  
  - [ ] 7.3 Implement example formatting and injection
    - Add example template formatting functionality
    - Implement example injection into main templates
    - Support configurable example limits and formatting
    - _Requirements: 4.2, 4.3_

- [ ] 8. Implement message formatting and role management
  - [ ] 8.1 Create MessageFormatter class
    - Implement role section parsing from rendered templates
    - Add SkyeMessage creation for different roles (System, User, Assistant, Capability)
    - Support role mapping configuration and validation
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ]* 8.2 Write property test for message formatting
    - **Property 5: Message role consistency**
    - **Validates: Requirements 6.1, 6.3, 6.4**
  
  - [ ] 8.3 Implement message placeholders and dynamic insertion
    - Add message placeholder functionality for conversation history
    - Support dynamic message insertion with proper role handling
    - Implement placeholder validation and error handling
    - _Requirements: 6.2, 6.5_

- [ ] 9. Implement multimodal content support
  - [ ] 9.1 Create ContentHandler class
    - Implement image content processing (URL, base64, file path)
    - Add content type validation and format conversion
    - Support multiple content types (text, image, audio, video)
    - _Requirements: 5.1, 5.2, 5.4_
  
  - [ ]* 9.2 Write property test for content handling
    - **Property 6: Content format validation**
    - **Validates: Requirements 5.1, 5.4**
  
  - [ ] 9.3 Integrate multimodal content with message creation
    - Add multimodal content to SkyeMessage objects
    - Implement content metadata preservation
    - Support provider-agnostic content representation
    - _Requirements: 5.3, 5.5_

- [ ] 10. Implement Jinja2 advanced features
  - [ ] 10.1 Add custom filters and macros support
    - Implement custom Jinja2 filter registration
    - Add macro registration and template composition
    - Support template inheritance and includes
    - _Requirements: 7.1, 7.2, 7.4, 7.5_
  
  - [ ]* 10.2 Write property test for template composition
    - **Property 7: Template composition consistency**
    - **Validates: Requirements 7.3**
  
  - [ ] 10.3 Implement template composition functionality
    - Add compose_templates method for multi-part templates
    - Support configurable separators and joining logic
    - Implement template dependency tracking
    - _Requirements: 7.3_

- [ ] 11. Implement output schema and structured generation
  - [ ] 11.1 Create SchemaValidator class
    - Implement Pydantic model to JSON schema conversion
    - Add direct JSON schema support and validation
    - Generate formatted output instructions for LLMs
    - _Requirements: 8.1, 8.2, 8.3, 8.5_
  
  - [ ]* 11.2 Write property test for schema validation
    - **Property 8: Schema instruction consistency**
    - **Validates: Requirements 8.1, 8.2, 8.3**
  
  - [ ] 11.3 Integrate schema validation with template rendering
    - Add output schema configuration to templates
    - Implement schema-based instruction generation
    - Support schema validation and error reporting
    - _Requirements: 8.4, 8.5_

- [ ] 12. Checkpoint - Ensure advanced features work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement template metadata and introspection
  - [ ] 13.1 Add template metadata collection and storage
    - Implement get_template_metadata method with comprehensive info
    - Add template listing and introspection capabilities
    - Support metadata queries for variables, examples, roles, content types
    - _Requirements: 9.1, 9.3, 9.4_
  
  - [ ]* 13.2 Write property test for metadata consistency
    - **Property 9: Metadata accuracy**
    - **Validates: Requirements 9.1, 9.4**
  
  - [ ] 13.3 Implement template validation and diagnostics
    - Add comprehensive template validation with detailed results
    - Implement syntax checking and variable reference validation
    - Support validation reporting without exceptions
    - _Requirements: 9.2, 9.5, 10.5_

- [ ] 14. Implement configuration and Skye integration
  - [ ] 14.1 Create configuration models and loading
    - Implement PromptBuilderConfig and Jinja2Config Pydantic models
    - Add configuration loading from environment variables and files
    - Support Skye configuration patterns with ${VAR} substitution
    - _Requirements: 11.4_
  
  - [ ]* 14.2 Write property test for configuration loading
    - **Property 10: Configuration consistency**
    - **Validates: Requirements 11.4**
  
  - [ ] 14.3 Integrate with Skye exception hierarchy and logging
    - Ensure all exceptions inherit from SkyeError
    - Add structured logging with correlation IDs
    - Implement proper error context and recovery
    - _Requirements: 11.5, 10.1, 10.2, 10.3, 10.4_

- [ ] 15. Implement performance optimizations and caching
  - [ ] 15.1 Add template compilation caching
    - Implement efficient template compilation with LRU cache
    - Add cache warming and precompilation support
    - Optimize memory usage for large template sets
    - _Requirements: 12.1, 12.2, 12.5_
  
  - [ ]* 15.2 Write property test for caching behavior
    - **Property 11: Cache consistency**
    - **Validates: Requirements 12.1, 12.2**
  
  - [ ] 15.3 Optimize variable extraction and example processing
    - Cache extracted variables to avoid repeated parsing
    - Implement efficient example formatting and caching
    - Add performance monitoring and metrics
    - _Requirements: 12.3, 12.4_

- [ ] 16. Integration and final wiring
  - [ ] 16.1 Wire all components together in main builder
    - Integrate all components into Jinja2PromptBuilder
    - Ensure proper dependency injection and initialization
    - Add comprehensive integration testing
    - _Requirements: 11.1, 11.2, 11.3_
  
  - [ ]* 16.2 Write integration tests for end-to-end functionality
    - Test complete template lifecycle from registration to rendering
    - Validate integration with SkyeMessage types and providers
    - Test multimodal content with different message types
    - _Requirements: 11.2, 11.3_
  
  - [ ] 16.3 Add module exports and package configuration
    - Update __init__.py files with proper exports
    - Configure optional dependency for skyeai[prompts]
    - Add comprehensive docstrings and type hints
    - _Requirements: 11.1_

- [ ] 17. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- Implementation follows Skye architecture guidelines with clean separation of concerns
- The first task focuses on creating interfaces, mocks, and samples to validate user experience before full implementation