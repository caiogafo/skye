---
title: "Roadmap"
status: current
last_updated: 2026-11-02
---

# Roadmap

- [x] Core interfaces and models
- [x] Configuration system
- [x] Exception hierarchy
- [ ] Provider implementations (OpenAI, Anthropic, Bedrock)
- [ ] Prompt management
- [ ] Agent runtime
- [ ] Memory systems
- [ ] Safety filters
- [ ] Policy engine inspired by [Cedar](https://www.cedarpolicy.com/)
  - Rules are `permit` or `forbid` statements over principal, action, resource and context. Everything is denied unless a `permit` matches, and a `forbid` always wins
  - Evaluated in pure Python, with no compiled dependency. The official Cedar engine is a Rust library, so Skye implements a small subset of the model instead of wrapping it
  - Guards capability and tool calls, model and region routing, memory access and MCP servers. Every decision is sent to observability
- [ ] Gateway inspired by [Amazon Bedrock AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-core-concepts.html)
  - One MCP endpoint (stateless HTTP, runs in a single Lambda function) that exposes Lambda functions, OpenAPI specs, upstream MCP servers and local capabilities as tools
  - Inbound authorization by IAM or a JWT authorizer, outbound authorization per target (execution role, API key, OAuth client credentials)
  - Every tool listing and tool call goes through the policy engine, so a caller only sees the tools it may use. Two tool selectors: hybrid search (keywords and embeddings) and Jev, a decision model
  - Standard library only: no `mcp` package, no web framework
- [ ] Observability integration
