# Requirements Document: Capability Support

## Introduction

The Capability Support feature enables Skye to register, manage, and invoke tools/functions across different LLM providers. This feature allows developers to extend agent capabilities by registering local functions or remote APIs as tools that LLMs can invoke during completion requests. The implementation provides a unified interface for tool definition, registration, and execution while handling provider-specific differences transparently.

## Glossary

- **Capability**: A callable function or API that an agent can use to perform actions (synonymous with "tool" or "function")
- **CapabilitySchema**: A structured definition of a capability including name, description, parameters, and return type
- **CapabilityRegistry**: A centralized registry for managing and discovering registered capabilities
- **Tool Definition**: The JSON Schema representation of a capability for LLM function calling
- **Tool Call**: A request from an LLM to invoke a specific capability with provided arguments
- **Tool Result**: The output from executing a capability, returned to the LLM for further processing
- **Local Function**: A Python function registered as a capability
- **Remote API**: An external HTTP API registered as a capability
- **Provider-Specific Format**: The native tool/function calling format used by each LLM provider (OpenAI, Anthropic, Bedrock, etc.)
- **Tool Execution**: The process of invoking a capability with arguments and returning results
- **Capability Validation**: Runtime verification that a capability implementation matches its schema

## Requirements

### Requirement 1: Capability Interface and Schema

**User Story:** As a developer, I want to define capabilities with clear schemas, so that LLMs can understand what tools are available and how to use them.

#### Acceptance Criteria

1. THE Skye library SHALL provide a CapabilitySchema model that defines name, description, parameters, and return type
2. THE Skye library SHALL provide a CapabilityInterface with abstract methods for get_schema(), execute(), and aexecute()
3. WHEN a capability is created, THE Skye library SHALL validate that the schema has a non-empty name and description
4. THE Skye library SHALL support JSON Schema format for parameter and return type definitions
5. THE Skye library SHALL allow capabilities to be synchronous or asynchronous

### Requirement 2: Local Function Registration

**User Story:** As a developer, I want to register Python functions as capabilities, so that agents can invoke them during execution.

#### Acceptance Criteria

1. THE Skye library SHALL provide a method to register a Python function as a capability
2. WHEN a function is registered, THE Skye library SHALL automatically extract parameter information from the function signature
3. THE Skye library SHALL support both synchronous and asynchronous functions
4. THE Skye library SHALL validate that registered functions have proper type hints
5. THE Skye library SHALL allow optional custom schema overrides for registered functions

### Requirement 3: Remote API Registration

**User Story:** As a developer, I want to register remote HTTP APIs as capabilities, so that agents can invoke external services.

#### Acceptance Criteria

1. THE Skye library SHALL provide a method to register a remote HTTP API as a capability
2. WHEN an API is registered, THE Skye library SHALL require a URL, HTTP method, and schema definition
3. THE Skye library SHALL support GET, POST, PUT, DELETE, and PATCH HTTP methods
4. THE Skye library SHALL handle authentication headers and query parameters
5. THE Skye library SHALL support both synchronous and asynchronous HTTP calls

### Requirement 4: Capability Registry

**User Story:** As a platform engineer, I want a centralized registry for managing capabilities, so that I can discover and manage tools across the application.

#### Acceptance Criteria

1. THE Skye library SHALL provide a CapabilityRegistry for registering and retrieving capabilities
2. THE Skye library SHALL support registering capabilities with unique names
3. THE Skye library SHALL provide methods to list all registered capabilities
4. THE Skye library SHALL provide methods to retrieve a capability by name
5. THE Skye library SHALL support capability namespacing (e.g., "weather.get_current", "database.query")

### Requirement 5: Provider-Agnostic Tool Definition

**User Story:** As a developer, I want to define tools once and use them across different LLM providers, so that I don't need to rewrite tool definitions for each provider.

#### Acceptance Criteria

1. THE Skye library SHALL convert capability schemas to provider-specific tool formats
2. WHEN a capability is used with OpenAI, THE Skye library SHALL convert it to OpenAI function calling format
3. WHEN a capability is used with Anthropic, THE Skye library SHALL convert it to Anthropic tool use format
4. WHEN a capability is used with Bedrock, THE Skye library SHALL convert it to Bedrock tool format
5. THE Skye library SHALL handle provider-specific differences transparently

### Requirement 6: Tool Call Handling

**User Story:** As a developer, I want to handle tool calls from LLMs, so that I can execute capabilities and return results to the model.

#### Acceptance Criteria

1. THE Skye library SHALL parse tool calls from provider responses
2. WHEN a tool call is received, THE Skye library SHALL validate that the requested capability exists
3. THE Skye library SHALL validate that provided arguments match the capability schema
4. THE Skye library SHALL execute the capability with provided arguments
5. THE Skye library SHALL return tool results in a format compatible with the provider

### Requirement 7: Tool Execution and Error Handling

**User Story:** As a developer, I want robust tool execution with clear error handling, so that failures don't break the agent flow.

#### Acceptance Criteria

1. THE Skye library SHALL execute capabilities with provided arguments
2. WHEN a capability execution fails, THE Skye library SHALL wrap the error in a CapabilityExecutionError
3. THE Skye library SHALL include the original error message and stack trace in the error
4. THE Skye library SHALL support both synchronous and asynchronous execution
5. THE Skye library SHALL support timeout configuration for tool execution

### Requirement 8: Completion Request Integration

**User Story:** As a developer, I want to pass capabilities to completion requests, so that LLMs can invoke tools during generation.

#### Acceptance Criteria

1. THE CompletionRequest model SHALL accept a list of capabilities
2. WHEN capabilities are provided in a request, THE Skye library SHALL convert them to provider-specific format
3. THE Skye library SHALL pass converted tools to the provider API
4. THE Skye library SHALL handle tool_choice parameter (auto, required, specific tool)
5. THE Skye library SHALL support parallel tool calls when the provider supports them

### Requirement 9: Tool Call Response Processing

**User Story:** As a developer, I want to automatically process tool calls from responses, so that I can easily implement agentic loops.

#### Acceptance Criteria

1. THE CompletionResponse model SHALL include tool calls when present in the provider response
2. WHEN tool calls are present, THE Skye library SHALL provide a method to execute them
3. THE Skye library SHALL return tool results in a format ready to send back to the model
4. THE Skye library SHALL support multiple tool calls in a single response
5. THE Skye library SHALL track which tools were called for observability

### Requirement 10: Capability Validation and Testing

**User Story:** As a developer, I want to validate capabilities before using them, so that I can catch configuration errors early.

#### Acceptance Criteria

1. THE Skye library SHALL validate that capability schemas are valid JSON Schema
2. THE Skye library SHALL validate that capability names are unique within a registry
3. THE Skye library SHALL validate that function signatures match their declared schemas
4. THE Skye library SHALL provide a method to test capability execution
5. THE Skye library SHALL provide clear error messages for validation failures

### Requirement 11: Observability and Logging

**User Story:** As a platform engineer, I want to track tool usage and execution, so that I can monitor agent behavior.

#### Acceptance Criteria

1. THE Skye library SHALL log all tool calls with capability name and arguments
2. THE Skye library SHALL log tool execution results and latency
3. THE Skye library SHALL log tool execution errors with full context
4. THE Skye library SHALL emit structured events for tool calls and results
5. THE Skye library SHALL support correlation IDs for tracing tool calls across requests

### Requirement 12: MCP (Model Context Protocol) Support

**User Story:** As a developer, I want to use MCP servers as capabilities, so that I can leverage existing MCP tools without rewriting them.

#### Acceptance Criteria

1. THE Skye library SHALL support loading tools from MCP servers via FastMCP library
2. WHEN FastMCP is installed, THE Skye library SHALL provide MCPCapability class for wrapping MCP tools
3. THE Skye library SHALL automatically convert MCP tool schemas to Skye CapabilitySchema format
4. THE Skye library SHALL support both local and remote MCP servers
5. THE Skye library SHALL make FastMCP an optional dependency (not required for base functionality)
6. WHEN FastMCP is not installed, THE Skye library SHALL provide helpful error messages directing users to install it
7. THE Skye library SHALL support OpenAPI-based MCP tools with automatic schema extraction
8. THE Skye library SHALL cache MCP tool definitions to avoid repeated server calls

### Requirement 13: Documentation and Examples

**User Story:** As a developer, I want clear documentation and examples, so that I can quickly implement tool support in my applications.

#### Acceptance Criteria

1. THE Skye library SHALL provide docstrings for all capability-related APIs
2. THE Skye library SHALL include examples of registering local functions as capabilities
3. THE Skye library SHALL include examples of registering remote APIs as capabilities
4. THE Skye library SHALL include examples of using capabilities with different providers
5. THE Skye library SHALL include examples of implementing agentic loops with tool calls
6. THE Skye library SHALL include examples of using MCP servers as capabilities
7. THE Skye library SHALL document how to set up and configure MCP servers
