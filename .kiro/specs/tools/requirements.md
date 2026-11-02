---
component: tools
codename: updraft
previous_name: capability-support
---

# Requirements Document

## Introduction

The `tools` component holds Skye's capabilities — local functions, remote APIs and the MCP client — behind the interfaces in `base`. A capability is defined once and used across every provider; the MCP client consumes an MCP server's tools, prompts and resources, with a built-in standard-library client by default and `fastmcp` only when chosen explicitly. This spec states the user stories the component serves and points at the requirements and decisions in steering; it copies no rule. It supersedes the former `capability-support` spec, whose pydantic schemas and `fastmcp`-first MCP design (a required `MCPServerClient`, stdio transport) are replaced by the current decisions and recorded as history.

## Requirements

### Requirement 1: Capability interface and schema

**User Story:** As a developer, I want to define capabilities with a clear schema, so that models know what tools exist and how to call them.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 16.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 16.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL honor decision D24 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 2: Capability as the extension point

**User Story:** As a developer, I want to register local functions and remote APIs through one registry, so that adding a capability never edits the core.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 6.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 6.2 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 3: Provider-agnostic capability definitions

**User Story:** As a developer, I want to define a capability once and use it with any provider, so that I do not rewrite tool definitions per provider.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 22.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 4: Capability terminology

**User Story:** As a maintainer, I want "Capability" used everywhere instead of "Tool", so that the vocabulary is consistent.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 22.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 22.2 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: Capability call handling

**User Story:** As a developer, I want tool calls parsed, validated and executed, so that agentic loops work across providers.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 16.2 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 6: Execution errors

**User Story:** As a developer, I want capability failures wrapped with context, so that a failing tool does not break the flow opaquely.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 18.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 7: Observability of capability calls

**User Story:** As a platform engineer, I want tool calls, results and errors emitted as structured events, so that I can monitor agent behaviour.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 18.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 8: MCP client, tri-faceted

**User Story:** As a user, I want MCP tools, prompts and resources consumed as Skye types, so that MCP works uniformly with the rest of the library.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 10.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 10.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 9: Built-in client by default, fastmcp by explicit choice

**User Story:** As a user, I want the built-in client by default and `fastmcp` only when I ask for it, so that MCP needs no extra dependency or hidden configuration.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 10.2 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 10.3 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 10.4 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL honor decision D15 of #[[file:.kiro/steering/12-decisions.md]].
5. THE spec SHALL honor decision D16 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 10: MCP resources through a base Port

**User Story:** As a maintainer, I want MCP resources behind a Port in `base`, so that prompts and memory can consume them without importing `tools`.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 10.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL honor decision D26 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 11: tools carries no third-party library

**User Story:** As a user deploying to a serverless runtime, I want `tools` to add nothing to the core import, so that the package stays small.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 10.7 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 7.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 12: Documentation and examples

**User Story:** As a developer, I want examples of capabilities and MCP usage, so that I can adopt them quickly.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 24.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 24.2 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 13: Superseded fastmcp-first design (history)

**User Story:** As a maintainer, I want the former pydantic + fastmcp-required design recorded as history, so that the migration is traceable and no rule is silently dropped.

#### Acceptance Criteria

1. THE spec SHALL keep this story as history only, no requirement of it being left in steering.
