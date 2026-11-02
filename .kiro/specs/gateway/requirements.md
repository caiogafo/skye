# Requirements Document: Gateway

## Introduction

The Gateway feature lets a Skye agent use tools without carrying a fixed list of them. The agent talks to one endpoint that speaks the Model Context Protocol (MCP). For each operation in progress, the Gateway registers and exposes only the tools that operation needs, and checks every listing and every call against the policy engine. It is inspired by Amazon Bedrock AgentCore Gateway (targets, inbound and outbound authorization, tool search, policy on every call) and is designed to run in a single AWS Lambda function.

Status: requirements draft, to be reviewed before design. Items marked OPEN are decisions for the owner.

## Glossary

- **Gateway**: The Skye component that exposes tools through one MCP endpoint
- **Target**: A source of tools behind the Gateway: a Lambda function, an OpenAPI document, an upstream MCP server, or a local capability
- **Tool**: A callable operation with a name, a description and a JSON Schema for its arguments (a Capability, in Skye terms)
- **Registry**: The catalogue of all tools the Gateway knows, with their target, tags and version
- **Operation**: The unit of work an agent is carrying out, described by a short text, optional tags, and the principal on whose behalf it runs
- **Toolset**: The tools exposed to one operation
- **Selector**: A strategy that ranks the tools of the Registry for an operation. Skye ships two: hybrid search and Jev
- **Scope token**: A signed, expiring token that names the toolset of an operation, so the Gateway needs no server-side session
- **Principal**: The caller, identified from IAM or from a JWT
- **Policy engine**: The component specified in `.kiro/specs/policy-engine`
- **Warm container**: A Lambda execution environment reused by later invocations
- **Decision model**: A model that does not generate text. It takes a state and typed questions (yes or no, a category, a score) and returns a choice from a fixed set, with calibrated probabilities. Jev, from TypeSafe AI, is one ("System One" model). The `models` component exposes decision models through one interface
- **Hierarchical selection**: Choosing in two steps (a domain first, then a tool inside it) when there are more candidates than a decision model accepts as labels

## Requirements

### Requirement 1: MCP endpoint

**User Story:** As an agent developer, I want one standard endpoint for tools, so that any MCP client can use the Gateway.

#### Acceptance Criteria

1. THE Gateway SHALL serve MCP over stateless HTTP, handling initialize, ping, tools/list and tools/call
2. THE Gateway SHALL NOT require a session held in the memory of one process between requests
3. THE Gateway SHALL return protocol errors in the JSON-RPC format defined by MCP
4. THE Gateway SHALL be implemented with the Python standard library, without the `mcp` package and without a web framework
5. THE Gateway SHALL state the MCP specification version it implements (OPEN: version to be fixed in design after reading the specification)

### Requirement 2: Targets

**User Story:** As a platform engineer, I want to attach existing functions and APIs as tools, so that I do not rewrite them.

#### Acceptance Criteria

1. THE Gateway SHALL support four target types: Lambda function, OpenAPI document, upstream MCP server, local capability
2. WHEN a target is registered, THE Gateway SHALL convert its operations into tools with a stable identifier of the form target and tool name
3. THE Gateway SHALL read OpenAPI documents in JSON, and in YAML only when the optional YAML parser is installed
4. WHEN one target fails, THE Gateway SHALL keep serving the tools of the other targets
5. THE Gateway SHALL reuse the existing CapabilityRegistry for local capabilities

### Requirement 3: Registry

**User Story:** As a platform engineer, I want the tool catalogue stored outside the function, so that every invocation sees the same tools.

#### Acceptance Criteria

1. THE Gateway SHALL keep the Registry in an external store: DynamoDB through boto3 when running in Lambda, files or memory for local use and tests
2. THE Gateway SHALL load the Registry lazily and cache it in the warm container with a time to live
3. WHEN the time to live expires, THE Gateway SHALL refresh the Registry inside the request that notices it, not in a background thread
4. THE Gateway SHALL store for each tool its name, description, argument schema, tags, target and version

### Requirement 4: Toolset per operation

**User Story:** As an agent developer, I want the agent to see only the tools its current operation needs, so that the prompt stays small and the agent cannot reach tools it should not use.

#### Acceptance Criteria

1. WHEN a client lists tools for an operation, THE Gateway SHALL return only the toolset selected for that operation
2. THE Gateway SHALL accept the operation description, tags and principal from the caller in each request
3. THE Gateway SHALL limit the size of a toolset to a configurable maximum (OPEN: default value)
4. THE Gateway SHALL reject a tool call for a tool outside the toolset named by the scope token
5. WHEN no operation is given, THE Gateway SHALL return only the discovery tool

### Requirement 5: Discovery tool

**User Story:** As an agent, I want to ask for more tools while I work, so that an operation that changes can get what it now needs.

#### Acceptance Criteria

1. THE Gateway SHALL always expose a discovery tool named skye_find_tools that takes a query and returns matching tools
2. WHEN the discovery tool returns tools, THE Gateway SHALL return an extended scope token that includes them
3. THE Gateway SHALL apply the policy engine to the results, so that a caller never learns about tools it may not use

### Requirement 6: Scope token

**User Story:** As a platform engineer, I want a stateless way to bind a toolset to an operation, because Lambda keeps no state between invocations.

#### Acceptance Criteria

1. THE Gateway SHALL issue a scope token that carries the operation identifier, the tool identifiers, the principal and an expiry time
2. THE Gateway SHALL sign the scope token with HMAC-SHA256 from the standard library
3. WHEN a tools/call arrives, THE Gateway SHALL verify signature and expiry before executing
4. THE Gateway SHALL read the signing key from the environment or from a secrets store (OPEN: key rotation)

### Requirement 7: Selection strategies

**User Story:** As an agent developer, I want to choose tools with hybrid search or with a decision model, so that the agent gets the right few tools fast.

#### Acceptance Criteria

1. THE Gateway SHALL define a Selector interface that takes an operation and the Registry and returns ranked tools with a reason for each, so that other selectors can be added later
2. THE Gateway SHALL ship two selectors: hybrid search and Jev
3. THE hybrid search selector SHALL combine a lexical ranking (BM25-style, standard library) with a semantic ranking (embeddings from a model of the `models` component) and fuse the two rankings
   - THE Gateway SHALL support more than one fusion method (reciprocal rank fusion and weighted scores), chosen by a setting
   - THE Gateway SHALL compute the embedding of a tool when the tool is registered, and store it through a vector storage interface, with an implementation that keeps vectors with the tool in the Registry, and room for others
   - THE Gateway SHALL NOT require a vector database
   - THE Gateway SHALL support ranking all tools and ranking only the best N lexical candidates, chosen by a setting
   - WHEN the embedding service is unavailable, THE hybrid selector SHALL use the lexical ranking alone and record that it did
4. THE Jev selector SHALL ask a decision model (Jev, or any model that implements the decision interface of the `models` component) to choose the tools for an operation from a shortlist, and SHALL record the probabilities it returns
   - THE Gateway SHALL reach a decision model through an endpoint and credentials given in settings, and SHALL work with any endpoint that speaks the Jev wire format, local-jev included
   - WHEN there are more candidates than the maximum number of labels set for the decision model, THE selector SHALL choose in two steps, domain first and then tool
   - WHEN the probability of the best choice is below the configured threshold, THE selector SHALL return the hybrid shortlist instead
   - WHEN the decision model is unavailable, THE Gateway SHALL fall back to the hybrid selector and record the fallback
5. THE Gateway SHALL support three modes, chosen per operation type by a setting: hybrid alone, Jev alone, and hybrid then Jev (hybrid builds the shortlist, Jev chooses from it)
6. THE Gateway SHALL record which selector, and which mode, exposed each tool, for audit
7. THE Gateway SHALL NOT choose the mode, the decision model, the embedding model, the vector storage or any threshold on its own: each is a setting that the owner provides, and the Gateway SHALL fail with a clear error naming the missing setting when the chosen mode needs one that is not set

### Requirement 8: Lambda constraints

**User Story:** As a platform engineer, I want the Gateway to behave correctly in Lambda, where parallel processes and background work are not available.

#### Acceptance Criteria

1. THE Gateway SHALL NOT use multiprocessing (pools, queues or process-based workers)
2. THE Gateway SHALL NOT depend on work that continues after the response is returned, because the environment is frozen between invocations
3. THE Gateway SHALL run concurrent I/O, such as calls to several targets, with asyncio or threads inside one invocation only
4. THE Gateway SHALL finish every request within a configurable time limit and return a partial result with an error note when a target is late
5. THE Gateway SHALL keep all state that must survive between invocations in the external store

### Requirement 9: Inbound authorization

**User Story:** As a platform engineer, I want to know who is calling, so that policy can decide what they may use.

#### Acceptance Criteria

1. THE Gateway SHALL support AWS IAM (SigV4) authentication and a JWT authorizer in front of it, taking the principal from the verified identity
2. THE Gateway SHALL NOT verify JWT signatures itself unless this is approved in design (OPEN: needs RSA verification without a compiled library)
3. WHEN no identity is available, THE Gateway SHALL deny the request unless an explicit local-development setting allows it

### Requirement 10: Outbound authorization

**User Story:** As a platform engineer, I want each target to be called with its own credentials, so that callers never hold them.

#### Acceptance Criteria

1. THE Gateway SHALL support these outbound modes per target: the function execution role, API key, OAuth client credentials, SigV4 signing
2. THE Gateway SHALL cache an OAuth access token in the warm container until shortly before it expires
3. THE Gateway SHALL NOT include credentials in tool results, logs or error messages

### Requirement 11: Policy on every call

**User Story:** As a security owner, I want every listing and call authorized, so that access is enforced in one place.

#### Acceptance Criteria

1. THE Gateway SHALL ask the policy engine for a decision on every tools/list, every discovery query and every tools/call
2. WHEN the decision is deny, THE Gateway SHALL omit the tool from listings and reject the call
3. THE Gateway SHALL support an enforcement mode and a log-only mode

### Requirement 12: Observability

**User Story:** As a security owner, I want a record of what each agent could see and do.

#### Acceptance Criteria

1. THE Gateway SHALL write one structured JSON log line per decision, with principal, operation identifier, selector, tools exposed or called, policy decision and latency
2. THE Gateway SHALL NOT log tool arguments or results unless explicitly enabled
3. THE Gateway SHALL publish its counters through the observability module

### Requirement 13: Size and load budgets

**User Story:** As a maintainer, I want the Gateway to stay small, because it is deployed in a Lambda package.

#### Acceptance Criteria

1. THE Gateway SHALL depend only on the standard library and libraries preinstalled in AWS Lambda
2. THE Gateway SHALL have its own entry in budgets.toml for size over the core and import time (OPEN: values)
3. THE Gateway SHALL be covered by the existing budget tests in the pull request workflow

### Requirement 14: Local mode

**User Story:** As a developer, I want to run the Gateway on my machine, so that I can test without AWS.

#### Acceptance Criteria

1. THE Gateway SHALL run as a local HTTP server built on the standard library
2. THE Gateway SHALL use the same request handler in the local server and in Lambda

## Open questions for the owner

1. (Settings, not decisions: see the next section.)
2. Which MCP specification version to target, and whether to support responses that stream.
3. Who describes the operation: the agent, the calling application, or the Gateway from the conversation?
4. Default and maximum toolset size.
5. (Settings, not decisions: see the next section.)
6. Registry store: DynamoDB only, or also S3 or Parameter Store.
7. Scope token key management and rotation.
8. Whether the Gateway also fronts model calls (the ModelRouter) or only tools.

## Settings the owner provides (the Gateway does not decide them)
Requirement 7.7 means these have no built-in choice. The design must define one configuration object for them, with a clear error when one is missing.
- Selection mode per operation type: hybrid, Jev, or hybrid then Jev.
- Decision model: endpoint and credentials (Jev early access, with a waitlist since 15 September 2026, or a local-jev server), maximum labels, probability threshold.
- Embedding model for the semantic ranking, and the vector storage.
- Hybrid: fusion method, number of lexical candidates to rank semantically (all, or the best N), weights.
- Toolset size per operation.
