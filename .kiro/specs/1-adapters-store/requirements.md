---
component: store
codename: lake
---

# Requirements Document

## Introduction

The one place for state backends, behind the storage Port. This spec is at the requirements stage: the design and the tasks come after the requirements are approved.

The requirements themselves live in `.kiro/steering/10-requirements.md`; each requirement below is one user story of this component, and each acceptance criterion is a pointer to the steering criterion it realizes (never a copy).

## Requirements

### Requirement 1: State

**User Story:** As a maintainer, I want all state backends in one component behind one Port, so that durable state is not duplicated in each service.

#### Acceptance Criteria

1. THE spec SHALL realize Requirement 12.1 of #[[file:.kiro/steering/10-requirements.md]].
2. THE spec SHALL realize Requirement 12.2 of #[[file:.kiro/steering/10-requirements.md]].
3. THE spec SHALL realize Requirement 12.3 of #[[file:.kiro/steering/10-requirements.md]].
