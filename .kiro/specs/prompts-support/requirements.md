---
component: prompts
---

# Requirements Document

## Introduction

This document specifies the requirements for adding comprehensive prompts support to Skye using Jinja2 templating. The feature will provide a robust, production-ready implementation of the existing `PromptBuilderInterface`, enabling template management, few-shot learning, multimodal content support, and structured output generation. The implementation will follow Skye's clean architecture principles and be available as an optional extra (`skyeai[prompts]`).

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy). Questions that were open in the former text are in `.kiro/steering/12-decisions.md`.

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

1. THE spec SHALL realize Requirement 29.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 29.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 29.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 2: Template Rendering and Variable Injection

**User Story:** As a developer, I want to render templates with variable substitution, so that I can generate dynamic prompts based on runtime data.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 30.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 30.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 30.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 30.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 3: Variable Management and Validation

**User Story:** As a developer, I want to configure default values and allowed missing variables, so that I can create flexible templates that work in different contexts.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 30.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 30.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 30.5 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 29.6 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 30.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 4: Few-Shot Learning Support

**User Story:** As a developer, I want to add examples to templates and configure dynamic example selection, so that I can implement few-shot learning patterns effectively.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 31.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 31.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 31.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 31.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: Multimodal Content Support

**User Story:** As a developer, I want to include images, audio, and other media in my templates, so that I can create rich multimodal prompts for vision and audio models.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 32.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 32.6 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 32.5 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 6: Message Role Management

**User Story:** As a developer, I want to control message roles (system, user, assistant) in my templates, so that I can create proper conversation structures for different AI models.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 32.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 32.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 32.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 7: Jinja2 Advanced Features

**User Story:** As a developer, I want to use custom Jinja2 filters, macros, and template composition, so that I can create sophisticated and reusable prompt components.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 30.8 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 30.9 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 30.7 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL honor decision D20 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 8: Output Schema and Structured Generation

**User Story:** As a developer, I want to define expected output schemas for my prompts, so that I can generate structured outputs and validate LLM responses.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 33.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 33.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 33.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 33.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL honor decision D24 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 9: Template Metadata and Introspection

**User Story:** As a developer, I want to inspect template metadata and validate templates, so that I can debug issues and understand template requirements.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 29.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 29.6 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 29.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 10: Error Handling and Validation

**User Story:** As a developer, I want comprehensive error handling with clear messages, so that I can quickly identify and fix issues in my templates and usage.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 30.2 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 29.3 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 29.1 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 32.6 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 29.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 11: Integration with Skye Architecture

**User Story:** As a developer, I want prompts support to integrate seamlessly with existing Skye components, so that I can use it alongside other Skye features without conflicts.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 34.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 34.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 34.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL honor decision D20 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 12: Performance and Caching

**User Story:** As a developer, I want efficient template rendering with caching, so that my application performs well under load.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 34.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 34.5 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 34.6 of #[[file:.kiro/steering/10-requirements.md]].
