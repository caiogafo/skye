# Requirements Document

## Introduction

This document specifies the requirements for adding comprehensive prompts support to Skye using Jinja2 templating. The feature will provide a robust, production-ready implementation of the existing `PromptBuilderInterface`, enabling template management, few-shot learning, multimodal content support, and structured output generation. The implementation will follow Skye's clean architecture principles and be available as an optional extra (`skyeai[prompts]`).

## Glossary

- **Prompt_Builder**: The main class implementing `PromptBuilderInterface` using Jinja2 templating
- **Template**: A Jinja2 template string with variable placeholders for generating prompts
- **Template_Registry**: Internal storage system for managing templates with versioning
- **Variable_Validator**: Component that validates template variables against requirements
- **Example_Selector**: Component that selects relevant few-shot examples dynamically
- **Message_Formatter**: Component that converts rendered templates to `SkyeMessage` objects
- **Content_Handler**: Component that processes multimodal content (text, images, audio, etc.)
- **Schema_Validator**: Component that validates and formats output schemas
- **Jinja_Environment**: Configured Jinja2 environment with custom filters and macros

## Requirements

### Requirement 1: Core Template Management

**User Story:** As a developer, I want to register and manage prompt templates with versioning, so that I can organize and maintain reusable prompts across my application.

#### Acceptance Criteria

1. WHEN a developer registers a template from a string, THE Prompt_Builder SHALL store it with the specified name and version
2. WHEN a developer registers a template from a file path, THE Prompt_Builder SHALL load and store the file contents with the specified name and version
3. WHEN a developer retrieves a template by name without version, THE Prompt_Builder SHALL return the latest version
4. WHEN a developer retrieves a template by name with version, THE Prompt_Builder SHALL return the exact version requested
5. WHEN a developer attempts to register a template with invalid Jinja2 syntax, THE Prompt_Builder SHALL raise a validation error
6. WHEN a developer attempts to retrieve a non-existent template, THE Prompt_Builder SHALL raise a KeyError

### Requirement 2: Template Rendering and Variable Injection

**User Story:** As a developer, I want to render templates with variable substitution, so that I can generate dynamic prompts based on runtime data.

#### Acceptance Criteria

1. WHEN a developer renders a template with all required variables, THE Prompt_Builder SHALL return a list of `SkyeMessage` objects
2. WHEN a developer renders a template with missing required variables, THE Prompt_Builder SHALL raise a ValueError unless the variable is in the allowed missing list
3. WHEN a developer renders a template with extra variables, THE Prompt_Builder SHALL ignore the extra variables without error
4. WHEN a developer renders a template, THE Prompt_Builder SHALL merge provided variables with default values, giving priority to provided variables
5. WHEN a developer renders a template with callable default values, THE Prompt_Builder SHALL execute the callables to get current values

### Requirement 3: Variable Management and Validation

**User Story:** As a developer, I want to configure default values and allowed missing variables, so that I can create flexible templates that work in different contexts.

#### Acceptance Criteria

1. WHEN a developer sets default values, THE Prompt_Builder SHALL use these values when variables are not provided during rendering
2. WHEN a developer sets allowed missing variables, THE Prompt_Builder SHALL not raise errors for these variables when they are missing
3. WHEN a developer extracts variables from a template, THE Prompt_Builder SHALL return all Jinja2 variable names found in the template
4. WHEN a developer validates a template, THE Prompt_Builder SHALL check for syntax errors and undefined variables
5. WHEN a developer creates a partial builder with bound variables, THE Prompt_Builder SHALL return a new instance with those variables pre-filled

### Requirement 4: Few-Shot Learning Support

**User Story:** As a developer, I want to add examples to templates and configure dynamic example selection, so that I can implement few-shot learning patterns effectively.

#### Acceptance Criteria

1. WHEN a developer adds examples to a template, THE Prompt_Builder SHALL store the examples and make them available during rendering
2. WHEN a developer renders a template with examples, THE Prompt_Builder SHALL format and inject the examples using the configured example template
3. WHEN a developer configures a semantic example selector, THE Prompt_Builder SHALL select the most relevant examples based on input similarity
4. WHEN a developer configures a random example selector, THE Prompt_Builder SHALL select random examples up to the maximum limit
5. WHEN a developer configures a fixed example selector, THE Prompt_Builder SHALL always use the same set of examples
6. WHEN no example selector is configured, THE Prompt_Builder SHALL use all available examples up to a reasonable default limit

### Requirement 5: Multimodal Content Support

**User Story:** As a developer, I want to include images, audio, and other media in my templates, so that I can create rich multimodal prompts for vision and audio models.

#### Acceptance Criteria

1. WHEN a developer configures image content for a template variable, THE Prompt_Builder SHALL process image URLs, base64 data, or file paths appropriately
2. WHEN a developer configures multimodal content types, THE Prompt_Builder SHALL validate content format and create appropriate message content
3. WHEN a developer renders a template with image content, THE Prompt_Builder SHALL create messages with proper multimodal content structure
4. WHEN a developer provides invalid image format, THE Prompt_Builder SHALL raise a validation error with descriptive message
5. WHEN a developer renders multimodal content, THE Prompt_Builder SHALL preserve content type metadata in the resulting messages

### Requirement 6: Message Role Management

**User Story:** As a developer, I want to control message roles (system, user, assistant) in my templates, so that I can create proper conversation structures for different AI models.

#### Acceptance Criteria

1. WHEN a developer sets message roles for template sections, THE Prompt_Builder SHALL create separate `SkyeMessage` objects for each role
2. WHEN a developer adds message placeholders, THE Prompt_Builder SHALL allow dynamic insertion of conversation history
3. WHEN a developer renders a template with role mappings, THE Prompt_Builder SHALL create `SystemMessage`, `UserMessage`, and `AssistantMessage` objects as appropriate
4. WHEN no role mapping is specified, THE Prompt_Builder SHALL default to creating `UserMessage` objects
5. WHEN a developer specifies invalid role names, THE Prompt_Builder SHALL raise a validation error

### Requirement 7: Jinja2 Advanced Features

**User Story:** As a developer, I want to use custom Jinja2 filters, macros, and template composition, so that I can create sophisticated and reusable prompt components.

#### Acceptance Criteria

1. WHEN a developer registers a custom Jinja2 filter, THE Prompt_Builder SHALL make it available in all template rendering
2. WHEN a developer registers a Jinja2 macro, THE Prompt_Builder SHALL make it available for use in templates
3. WHEN a developer composes templates from multiple parts, THE Prompt_Builder SHALL create a new template by joining the parts with the specified separator
4. WHEN a developer uses Jinja2 template inheritance, THE Prompt_Builder SHALL support extends and include directives
5. WHEN a developer uses conditional logic in templates, THE Prompt_Builder SHALL evaluate Jinja2 if/else statements correctly

### Requirement 8: Output Schema and Structured Generation

**User Story:** As a developer, I want to define expected output schemas for my prompts, so that I can generate structured outputs and validate LLM responses.

#### Acceptance Criteria

1. WHEN a developer sets an output schema using a Pydantic model, THE Prompt_Builder SHALL generate appropriate JSON schema instructions
2. WHEN a developer sets an output schema using a JSON schema dictionary, THE Prompt_Builder SHALL format it for LLM consumption
3. WHEN a developer requests output instructions, THE Prompt_Builder SHALL return formatted instructions based on the configured schema
4. WHEN no output schema is configured, THE Prompt_Builder SHALL return empty output instructions
5. WHEN a developer provides an invalid schema, THE Prompt_Builder SHALL raise a validation error

### Requirement 9: Template Metadata and Introspection

**User Story:** As a developer, I want to inspect template metadata and validate templates, so that I can debug issues and understand template requirements.

#### Acceptance Criteria

1. WHEN a developer requests template metadata, THE Prompt_Builder SHALL return information about variables, examples, content types, and roles
2. WHEN a developer validates a template, THE Prompt_Builder SHALL check syntax, variable references, and return detailed validation results
3. WHEN a developer lists available templates, THE Prompt_Builder SHALL return all registered template names and versions
4. WHEN a developer inspects template variables, THE Prompt_Builder SHALL distinguish between required and optional variables
5. WHEN a developer checks template configuration, THE Prompt_Builder SHALL return current settings for examples, roles, and content types

### Requirement 10: Error Handling and Validation

**User Story:** As a developer, I want comprehensive error handling with clear messages, so that I can quickly identify and fix issues in my templates and usage.

#### Acceptance Criteria

1. WHEN template rendering fails due to missing variables, THE Prompt_Builder SHALL raise a `ValueError` with specific variable names
2. WHEN template registration fails due to syntax errors, THE Prompt_Builder SHALL raise a `ValueError` with Jinja2 error details
3. WHEN file loading fails, THE Prompt_Builder SHALL raise a `FileNotFoundError` with the attempted file path
4. WHEN invalid content types are provided, THE Prompt_Builder SHALL raise a `ValueError` with supported format information
5. WHEN template validation fails, THE Prompt_Builder SHALL return detailed error information without raising exceptions

### Requirement 11: Integration with Skye Architecture

**User Story:** As a developer, I want prompts support to integrate seamlessly with existing Skye components, so that I can use it alongside other Skye features without conflicts.

#### Acceptance Criteria

1. WHEN the prompts module is imported, THE system SHALL only require Jinja2 as an additional dependency
2. WHEN prompts are rendered, THE Prompt_Builder SHALL create standard `SkyeMessage` objects compatible with all providers
3. WHEN used with capabilities, THE Prompt_Builder SHALL support `CapabilityMessage` creation and formatting
4. WHEN configuration is loaded, THE Prompt_Builder SHALL support Skye configuration patterns with environment variable substitution
5. WHEN errors occur, THE Prompt_Builder SHALL use Skye exception hierarchy and logging patterns

### Requirement 12: Performance and Caching

**User Story:** As a developer, I want efficient template rendering with caching, so that my application performs well under load.

#### Acceptance Criteria

1. WHEN templates are registered, THE Prompt_Builder SHALL compile and cache Jinja2 templates for fast rendering
2. WHEN the same template is rendered multiple times, THE Prompt_Builder SHALL reuse compiled templates without recompilation
3. WHEN template variables are extracted, THE Prompt_Builder SHALL cache variable lists to avoid repeated parsing
4. WHEN examples are processed, THE Prompt_Builder SHALL cache formatted examples for reuse
5. WHEN large numbers of templates are registered, THE Prompt_Builder SHALL maintain reasonable memory usage through efficient storage