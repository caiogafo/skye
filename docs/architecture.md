---
title: "Architecture"
status: current
last_updated: 2026-11-02
---

# Architecture

Skye follows Clean Architecture principles with a stable core of interfaces:

```
┌─────────────────────────────────────────┐
│         skye (base package)           │
│  ┌───────────────────────────────────┐  │
│  │   Interfaces & Contracts          │  │
│  │   - ModelInterface                │  │
│  │   - CapabilityInterface           │  │
│  │   - MemoryInterface               │  │
│  │   - SafetyFilterInterface         │  │
│  │   - ObserverInterface             │  │
│  │   - And more...                   │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Data Models (Pydantic)          │  │
│  │   - CompletionRequest/Response    │  │
│  │   - UserMessage, AssistantMessage │  │
│  │   - ModelConfig, SkyeConfig     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                  ▲
                  │ depends on
                  │
    ┌─────────────┴─────────────┐
    │   Optional Extras         │
    │   - providers/            │
    │   - agents/               │
    │   - memory/               │
    │   - tools/                │
    └───────────────────────────┘
```
