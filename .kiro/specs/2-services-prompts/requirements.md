---
component: prompts
codename: cirrus
previous_name: prompts-support
---

# Requirements Document

## Introduction

The `prompts` component implements the `PromptBuilderInterface` of `base`: versioned templates, variable injection, few-shot examples, message roles, multimodal content and output schemas. It follows the liteprompt design with a standard-library template engine (`prompts/engine.py`), so it needs no third-party library and no extra (decision D20; Requirement 13). The `prompt` block of the `.skye` language is the second way to write a prompt (decision D60). This spec states the user stories the component serves and points at the requirements and decisions in steering; it copies no rule. It supersedes the former `prompts-support` spec, whose Jinja2 and pydantic design is replaced by the current decisions and recorded as history in `design.md`.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy). Questions that were open in the former text are in `.kiro/steering/12-decisions.md`.

## Glossary

- **Prompt_Builder**: The class implementing `PromptBuilderInterface` (`BasePromptBuilder`), using the standard-library engine
- **Template**: A template string with `{{ }}` placeholders, `if` and `for` blocks, for generating prompts
- **Template_Registry**: Internal storage system for managing templates with versioning
- **Variable_Validator**: Component that validates template variables against requirements
- **Example_Selector**: Component that selects relevant few-shot examples dynamically
- **Message_Formatter**: Component that converts rendered templates to `SkyeMessage` objects
- **Content_Handler**: Component that processes multimodal content (text, images, audio, etc.)
- **Schema_Validator**: Component that validates and formats output schemas
- **Engine**: The standard-library template engine `prompts/engine.py`, with the built-in filters and the custom filters the developer registers

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

### Requirement 7: Template engine features

**User Story:** As a developer, I want to use conditionals, loops, custom filters and template composition (without macros, inheritance or includes, decision D20), so that I can create reusable prompt components.

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

### Requirement 13: Described and typed prompt inputs

**User Story:** As a developer, I want a prompt to say what it takes and give precise errors for wrong data, so that a mistake in an input fails early with its path instead of producing an empty section.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 30.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 30.11 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 54.20 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL honor decision D69 of #[[file:.kiro/steering/12-decisions.md]].
5. THE spec SHALL honor decision D73 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 14: Structured output declared in the prompt

**User Story:** As a developer, I want to declare the shape of the answer once and have the format instructions generated, so that I never write a JSON, table or XML structure by hand.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 33.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 33.6 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 33.7 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 33.8 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL honor decision D70 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 15: Bundled agent prompts and their conventions

**User Story:** As a developer building agents, I want ready prompts with one input shape for tools and memories, so that I can swap one prompt for another without rewriting the data I pass.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 30.12 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 30.13 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 30.14 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 31.5 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL honor decision D74 of #[[file:.kiro/steering/12-decisions.md]].
6. THE spec SHALL honor decision D71 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 16: Prompt help and examples

**User Story:** As a developer, I want to ask a prompt what it takes and gives back, and to learn the language from examples that cannot fall behind, so that I use a prompt without reading its source.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 34.7 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 34.8 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 24.9 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 24.10 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL honor decision D73 of #[[file:.kiro/steering/12-decisions.md]].
6. THE spec SHALL honor decision D74 of #[[file:.kiro/steering/12-decisions.md]].
