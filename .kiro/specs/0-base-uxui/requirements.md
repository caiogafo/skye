---
component: none (cross-cutting: the public surface a user touches)
previous_name: uxui
---

# Requirements Document

## Introduction

This spec covers the public surface of Skye as a user meets it: the import paths, the names, the Ports an extension author implements, the
examples, and the first docstring a user reads. It comes from a three-part audit (the examples, the names and imports, the contracts of the
Ports; 35 findings, in `design.md`), from the 27 rules derived from it, and from three follow-up reports (familiarity, simplicity, tools) whose
conflicts are resolved in one place. Those rules are now criteria in `.kiro/steering/10-requirements.md`
(Requirements 7.14, 7.15, 15.9, 15.10, 16.6 to 16.9, 22.3 to 22.6 and 24.4 to 24.8) and the questions the audit left to the owner are decisions
D36 to D45 (first the open decisions O24 to O33) in `.kiro/steering/12-decisions.md`. Here each requirement is one user story and each acceptance criterion is a pointer
of the form `THE spec SHALL realize Requirement N.k of #[[file:.kiro/steering/10-requirements.md]]`, never a copy of the criterion. The number
after `Requirement` in a heading below is local to this file; the number in a criterion is the steering one. Fetch a steering requirement with
`grep -n -A25 "^### Requirement 24:" .kiro/steering/10-requirements.md`. The raw audit and the follow-up reports are kept under `.agents/tasks/`
(`uxui-audit-report.md`, `uxui-audit-rules.md`, `uxui-familiarity-report.md`, `uxui-simplicity-report.md`, `uxui-tools-report.md`,
`uxui-reconciliation.md`); the folder of this spec was called `uxui` before decision D35. The `.skye` language (Requirement 54, decisions D49 to D61)
adds the last story, Requirement 19: loading a router, a flow or a prompt from a file; its design and the working files it came from
(`uxui-dsl-decisions.md`, `uxui-dsl-examples.md`, `uxui-kiro-handoff-dsl.md`) are described in `design.md`.

## Requirements

### Requirement 1: Short public import paths

**User Story:** As a developer, I want to import the commonest names from `skye` and a Port from `skye.interfaces`, so that the second line of my program is not an internal layer path.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 7.14 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 7.15 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 7.8 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL honor decision D34 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 2: One name, one home

**User Story:** As a developer, I want a public name to mean one class, so that an `isinstance` or an `except` written against one import path catches what another path returns.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 22.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 3: Names that say what they do

**User Story:** As a developer, I want method, file and module names that follow one rule, so that I can guess `list_x` or `ax` and be right.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 22.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 22.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 4: One vocabulary

**User Story:** As a developer, I want capability, tool and function call explained once, and Port and Interface explained once, so that I do not search the documentation for three words.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 22.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 22.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: A Port describes the call users make

**User Story:** As an extension author, I want the Port to have the signature of the real call, so that a class written from the Port works the way the documentation teaches and the type checker agrees.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 16.6 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 16.7 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 16.2 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 6: A Port states what it raises and what it promises

**User Story:** As an extension author, I want each Port to say what it raises, what it returns when something is missing and whether it is safe to call concurrently, so that my implementation behaves as the library expects.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 16.8 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 7: Only Ports that are used

**User Story:** As an extension author, I want the exported Ports to be the ones something implements and tests, and the large ones split by role, so that the list tells me what I can really extend.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 16.9 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 16.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 8: Examples that run with no key

**User Story:** As a newcomer, I want every example to run with no key and no network and print a result, so that my first ten minutes show me what the library does instead of "skipping".

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 24.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 24.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 9: Small, plain examples

**User Story:** As a newcomer, I want one idea per example, short and plainly printed, so that I can find the line I need.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 24.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 24.7 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 24.2 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 10: True install lines

**User Story:** As a newcomer, I want every install command to name an extra that exists, so that I do not install nothing and conclude something is missing.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 24.6 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 7.13 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 11: Example folders that read like a path

**User Story:** As a newcomer, I want a short README in each example folder and a numbered reading order, so that I know what to read second.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 24.8 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 24.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 12: The first docstring runs

**User Story:** As a developer, I want the example in `help(skye)` and in each Port docstring to work when I copy it, so that the first text I read is true.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 15.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 13: One page for extending the library

**User Story:** As an extension author, I want one page that says which Port to implement, where to register it and which example to copy, so that I do not read twenty-three interface files to find out.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 15.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 6.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 14: Where this work lives

**User Story:** As a maintainer, I want the public-surface work in one cross-cutting spec at its canonical name, so that the structure spec does not grow a fifth former spec and each rule has one owner.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 15.2 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL honor decision D35 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 15: One way to execute a capability call

**User Story:** As a developer writing a tool loop or an agent, I want one primitive that runs a call and tells me how it ended, so that every path behaves the same and a failure is a field, not a text prefix.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 16.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 16.12 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 16: A toolset reaches a runtime component through one Port

**User Story:** As an agent author, I want the local registry and the gateway to offer tools through the same Port, so that the agent takes its toolset one way and passes a scope token with every call.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 16.11 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 16.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 17: A shorthand for the router

**User Story:** As a developer, I want a one-line way to write a router with a fallback, so that the common case does not cost six classes while the full form stays available.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 22.8 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 54.6 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL honor decision D59 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 18: Names a newcomer tries

**User Story:** As a developer coming from the OpenAI SDK, LiteLLM or Pydantic, I want the names I try first to exist as thin aliases, so that I do not have to learn a new word for a thing I already know.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 22.7 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 22.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 19: Load a router, a flow or a prompt from a `.skye` file

**User Story:** As a developer, I want to write a router, a flow or a prompt in one readable file and load it with one call that tells me exactly where a mistake is, so that I can read what the system will do and let a model write it for me.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 54.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 54.3 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 54.6 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 54.8 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 54.9 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL honor decision D50 of #[[file:.kiro/steering/12-decisions.md]].
7. THE spec SHALL honor decision D61 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 20: No YAML

**User Story:** As a user deploying to a serverless runtime, I want the library to read no YAML, so that the install carries no YAML library and there is one configuration language for the router, the flow and the prompt.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 54.12 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 7.12 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL honor decision D62 of #[[file:.kiro/steering/12-decisions.md]].
