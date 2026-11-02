---
component: models
codename: zephyr
previous_name: model-providers
---

# Requirements Document

## Introduction

The `models` component holds the adapters for every model API kind — language models, embedding models and decision models — behind the Ports defined in `base`. It is a thin, standard-library foundation: one shared HTTP transport, retry policy, error mapping and token counter, reused by every adapter, with no vendor SDK on the runtime path. This spec states the user stories the component serves and points at the requirements and decisions in steering; it copies no rule. It supersedes the former `model-providers` spec, whose SDK-based design (a selecting `ProviderRegistry`, pydantic schemas, `tenacity`, the "Vertex AI" name) is replaced by the current decisions and recorded as history.

## Requirements

### Requirement 1: Model adapters behind Ports

**User Story:** As an application developer, I want every model provider behind one interface, so that I can switch providers without changing my code.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 9.9 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 16.1 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 16.4 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 16.5 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 2: One standard-library implementation per provider

**User Story:** As a user deploying to a serverless runtime, I want one lightweight REST adapter per provider and no SDK to install, so that the package stays small and behaviour is predictable.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.3 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 9.4 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL honor decision D13 of #[[file:.kiro/steering/12-decisions.md]].
4. THE spec SHALL honor decision D14 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 3: Provider named google

**User Story:** As a maintainer, I want the former Vertex AI provider named `google`, so that the name matches the current product.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.3 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL honor decision D19 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 4: Shared transport, retry and error mapping

**User Story:** As a maintainer, I want one shared transport, retry policy and error mapping reused by every adapter, so that behaviour is consistent and no adapter duplicates it.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 9.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 18.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 5: Provider-agnostic transformation at the boundary

**User Story:** As a maintainer, I want all provider-specific transformation inside the adapter, so that the router and tools stay provider-agnostic and adding a provider touches only its adapter.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.5 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 9.10 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 6.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 6: Function calling and the OpenAI data shape

**User Story:** As a developer building agents, I want models to call capabilities and to accept the OpenAI data shape, so that tool use works without vendor lock-in.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.10 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 9.6 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 22.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 7: Embeddings

**User Story:** As a developer building retrieval, I want embedding adapters behind one Port, so that I can switch embedding models without changing my code.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 25.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 25.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 25.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 25.4 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 8: Multimodal inputs

**User Story:** As a developer building vision applications, I want to send images and other media to multimodal models, so that I can build richer experiences through the same interface.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 26.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 26.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 26.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 9: Structured output

**User Story:** As a developer, I want models to return data validated against a declared shape, so that I can parse outputs reliably.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 27.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 27.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL honor decision D24 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 10: Token counting and cost

**User Story:** As a product manager, I want token counts and cost estimates without shipping a tokenizer in the core, so that spending is visible and the footprint stays light.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 28.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 28.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 28.3 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL realize Requirement 19.1 of #[[file:.kiro/steering/10-requirements.md]].
5. THE spec SHALL realize Requirement 19.2 of #[[file:.kiro/steering/10-requirements.md]].
6. THE spec SHALL honor decision D25 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 11: Decision model (Jev)

**User Story:** As the gateway, router and guard, I want a decision model that returns a calibrated choice from a fixed set, so that selection does not need a text model.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.8 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 12: Lazy loading and packaging

**User Story:** As a user, I want provider adapters to add nothing to the core import, so that `import skye` stays small and fast.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 7.3 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 7.1 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 13: Differential tests against vendor SDKs

**User Story:** As a maintainer, I want the vendor SDKs used only as development oracles, so that I can prove the REST adapters are equivalent without shipping an SDK.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.4 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL honor decision D14 of #[[file:.kiro/steering/12-decisions.md]].

### Requirement 14: Provider health and observability

**User Story:** As an SRE, I want provider success, latency and error metrics exposed, so that I can detect and respond to issues.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 17.2 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 18.3 of #[[file:.kiro/steering/10-requirements.md]].

### Requirement 15: Superseded SDK-based design (history)

**User Story:** As a maintainer, I want the former SDK-based design recorded as history, so that the migration is traceable and no rule is silently dropped.

#### Acceptance Criteria

1. THE spec SHALL keep this story as history only, no requirement of it being left in steering.

### Requirement 16: Create a client with one call

**User Story:** As a developer, I want to create the client of any provider with one call in the style of `boto3.client`, so that I write the same line for every provider and the library stays light to import.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 9.11 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 9.12 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 7.8 of #[[file:.kiro/steering/10-requirements.md]].
4. THE spec SHALL honor decision D28 of #[[file:.kiro/steering/12-decisions.md]].
