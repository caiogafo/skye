---
title: "Core interfaces"
status: current
last_updated: 2026-11-02
---

# Core Interfaces

## ModelInterface

Unified interface for all LLM providers:

```python
from abc import ABC, abstractmethod
from typing import Iterator
from skye import CompleteResponse, StreamChunk
from skye.messages import SkyeMessage

class ModelInterface(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[SkyeMessage],
        model: str,
        **kwargs
    ) -> CompleteResponse:
        """Execute a synchronous completion request."""
        pass
    
    @abstractmethod
    async def acomplete(
        self,
        messages: list[SkyeMessage],
        model: str,
        **kwargs
    ) -> CompleteResponse:
        """Execute an asynchronous completion request."""
        pass
    
    @abstractmethod
    def stream(
        self,
        messages: list[SkyeMessage],
        model: str,
        **kwargs
    ) -> Iterator[StreamChunk]:
        """Execute a streaming completion request."""
        pass
```

## CapabilityInterface

Define tools/functions that agents can use:

```python
from skye.interfaces import CapabilityInterface, CapabilitySchema

class WebSearchCapability(CapabilityInterface):
    def get_schema(self) -> CapabilitySchema:
        return CapabilitySchema(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
    
    def execute(self, query: str) -> str:
        # Implementation
        return search_results
```

## MemoryInterface

Store and retrieve agent memories:

```python
from skye.interfaces import MemoryInterface
from skye.memory import MemoryEntry

class MyMemory(MemoryInterface):
    def store(self, entry: MemoryEntry) -> str:
        # Store memory and return ID
        pass
    
    def retrieve(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        # Retrieve relevant memories
        pass
```
