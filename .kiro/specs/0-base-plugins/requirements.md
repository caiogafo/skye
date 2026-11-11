---
component: none (cross-cutting: plugins, the registrar and the provider profile)
---

# Requirements Document

## Introduction

This spec covers how a third party adds an integration to Skye without changing it, and how the knowledge that belongs to one provider or to
the store is kept in one place that the other components read. It follows decision D107 (plugins are wanted) and D108 (this spec exists;
the rules are Requirements 56 to 61 of steering). How the plugins are built is the open decision O59, with the points the scan of the code
added in O60 to O63; the rules below are the proposal and are approved with this spec. The scan that found the scattered knowledge is
`docs/_notes/extension-points-scan.md`; it is a working note and is not part of the spec.

The work has two halves that share one mechanism. The first is the plugin door: one plugin object with `register(registrar)`, one registrar
method per kind of integration, discovery through the entry-point group `skye.plugins` that runs lazily, explicit registration with
`skye.use`, an allowlist in the configuration file, one conformance function per kind and the command `skye plugins`. The second is the
provider profile, registered together with the provider class, which cost, token counting, the router and `auth` read instead of keeping
their own tables, together with the matching rule for the store: the router no longer knows how a counter is stored or how expiry works.
The profile shape of the model entry (`tokenizer`, `message_overhead`, prices) is shared with the token counter work of `1-adapters-models`.

Here each requirement is one user story and each acceptance criterion is a pointer of the form
`THE spec SHALL realize Requirement N.k of #[[file:.kiro/steering/10-requirements.md]]`, never a copy of the criterion. The number after
`Requirement` in a heading below is local to this file; the number in a criterion is the steering one. Fetch a steering requirement with
`grep -n -A25 "^### Requirement 59:" .kiro/steering/10-requirements.md`. The order of work (provider profile first, then the store, then the
closed kinds) is in D108 and is kept by the tasks.

## Glossary

- **Plugin**: an object with `register(registrar)` (the Port `PluginInterface`, Requirement 56.1 of steering); it adds one or more integrations.
- **Registrar**: the object a plugin receives, with one method per kind of integration (`RegistrarInterface`, Requirement 56.2).
- **Kind**: a category of integration that has a registrar method, such as a model provider or a store backend.
- **Provider profile**: the one declaration of everything specific to a provider (`ProviderProfile`, Requirement 59.1); a model entry in it is a `ModelProfile` (Requirement 59.2).
- **Entry-point group**: the group `skye.plugins` of Python package metadata, scanned lazily with `importlib.metadata` (Requirement 57.1).
- **Conformance function**: the public `check_<kind>` of a kind that tests an implementation offline (Requirement 58.4).

## Requirements

### Requirement 1: One plugin, one registrar

**User Story:** As a third-party author, I want to add an integration to Skye with one object, so that I change nothing inside Skye.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 56.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 56.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 56.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 56.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 56.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 56.6 of #[[file:.kiro/steering/10-requirements.md]].
7. THE spec SHALL realize Requirement 56.7 of #[[file:.kiro/steering/10-requirements.md]].
8. THE spec SHALL realize Requirement 56.8 of #[[file:.kiro/steering/10-requirements.md]].
9. THE spec SHALL honor decision D107 of #[[file:.kiro/steering/12-decisions.md]].
10. THE spec SHALL honor decision D108 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 2: Plugins found when needed and loaded when allowed

**User Story:** As a user, I want installed plugins found without code, or added with one call, and I want to choose which ones load, so that I control what runs in my function.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 57.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 57.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 57.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 57.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 57.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 57.6 of #[[file:.kiro/steering/10-requirements.md]].
7. THE spec SHALL realize Requirement 57.7 of #[[file:.kiro/steering/10-requirements.md]].
8. THE spec SHALL realize Requirement 57.8 of #[[file:.kiro/steering/10-requirements.md]].
9. THE spec SHALL realize Requirement 57.9 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 3: Every kind open, every plugin testable

**User Story:** As a plugin author, I want every kind of integration open to me and a test that tells me my plugin works, so that I know it is ready before I publish it.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 58.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 58.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 58.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 58.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 58.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 58.6 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 4: A provider declared once

**User Story:** As a provider author, I want to declare everything that is specific to my provider once, together with its class, so that cost, token counting, routing and authentication need no edit of mine.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 59.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 59.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 59.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 59.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 59.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 59.6 of #[[file:.kiro/steering/10-requirements.md]].
7. THE spec SHALL realize Requirement 59.7 of #[[file:.kiro/steering/10-requirements.md]].
8. THE spec SHALL realize Requirement 59.8 of #[[file:.kiro/steering/10-requirements.md]].
9. THE spec SHALL realize Requirement 59.9 of #[[file:.kiro/steering/10-requirements.md]].
10. THE spec SHALL realize Requirement 59.10 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: Provider and storage knowledge in one place

**User Story:** As a maintainer, I want the knowledge that belongs to one provider, and the knowledge that belongs to the store, each in exactly one place, so that adding a component edits one class and the other components call that logic.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 60.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 60.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 60.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 60.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 60.5 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL realize Requirement 60.6 of #[[file:.kiro/steering/10-requirements.md]].
7. THE spec SHALL realize Requirement 60.7 of #[[file:.kiro/steering/10-requirements.md]].
8. THE spec SHALL realize Requirement 60.8 of #[[file:.kiro/steering/10-requirements.md]].
9. THE spec SHALL realize Requirement 60.9 of #[[file:.kiro/steering/10-requirements.md]].
10. THE spec SHALL realize Requirement 60.10 of #[[file:.kiro/steering/10-requirements.md]].
11. THE spec SHALL realize Requirement 60.11 of #[[file:.kiro/steering/10-requirements.md]].
12. THE spec SHALL realize Requirement 60.12 of #[[file:.kiro/steering/10-requirements.md]].
13. THE spec SHALL honor decision D97 of #[[file:.kiro/steering/12-decisions.md]].
14. THE spec SHALL honor decision D98 of #[[file:.kiro/steering/12-decisions.md]].
15. THE spec SHALL honor decision D104 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 6: Easy to learn, light to load

**User Story:** As a user who wants to extend Skye, I want one example, one page and an up-to-date skill, so that I write my first plugin in minutes.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 61.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 61.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 61.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 61.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL honor decision D27 of #[[file:.kiro/steering/12-decisions.md]].
