# Design Document: nimbus

## Overview

The nimbus library serves as the foundational layer for the Nimbus GenAI platform. It provides a Clean Architecture-based design where all components are built on a stable core of interfaces and models. The design emphasizes:

- **Provider-agnostic abstractions** for LLM interactions
- **Optional extras architecture** - install only what you need
- **Type safety** using Pydantic models and Python type hints
- **Minimal base dependencies** to remain lightweight and stable
- **Zero coupling** between optional components

### Installation Philosophy

The base installation (`pip install nimbus`) provides only:
- **Interfaces**: Contracts that define how components interact
- **Models**: Data structures (messages, requests, responses, configs)
- **Exceptions**: Error hierarchy
- **Configuration**: Config loading system

All implementations are optional extras:
```bash
pip install nimbus                    # Base only
pip install nimbus[bedrock]           # + Bedrock provider
pip install nimbus[agents,memory]     # + Multiple extras
pip install nimbus[all]               # Everything
```

### Usage Example

```python
# Install: pip install nimbus[bedrock]

from nimbus.completion import CompletionRequest
from nimbus.messages import UserMessage
from nimbus.providers.bedrock import BedrockModel

model = BedrockModel(model_id="anthropic.claude-3-sonnet")
response = model.complete(
    CompletionRequest(
        messages=[UserMessage(content="Hello")],
        model="claude-3-sonnet"
    )
)
```

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    nimbus (base)                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Core Interfaces & Contracts             │  │
│  │  - ModelInterface                                 │  │
│  │  - PromptBuilderInterface                         │  │
│  │  - CapabilityInterface                            │  │
│  │  - MemoryInterface                                │  │
│  │  - SafetyFilterInterface                          │  │
│  │  - ObserverInterface                              │  │
│  │  - StorageAdapterInterface                        │  │
│  │  - PluginInterface                                │  │
│  │  - EventHandlerInterface                          │  │
│  │  - VectorEncoderInterface                         │  │
│  │  - ContentReaderInterface                         │  │
│  │  - ModelRouterInterface                           │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Data Models (Pydantic)                  │  │
│  │  - NimbusMessage, UserMessage, AssistantMessage   │  │
│  │  - SystemMessage, CapabilityMessage               │  │
│  │  - ContentChunk                                   │  │
│  │  - CompletionRequest                              │  │
│  │  - CompletionResponse                             │  │
│  │  - StreamChunk                                    │  │
│  │  - TokenUsage                                     │  │
│  │  - ModelConfig, RateLimitConfig, RetryConfig    │  │
│  │  - CooldownConfig, RoutingStrategy              │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Exception Hierarchy                     │  │
│  │  - NimbusError (base)                             │  │
│  │  - ProviderError                                  │  │
│  │  - ConfigurationError                             │  │
│  │  - ValidationError                                │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Configuration System                    │  │
│  │  - ConfigLoader                                   │  │
│  │  - EnvironmentConfig                              │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ (depends on)
                          ▼
        ┌─────────────────────────────────────┐
        │   Optional Extras (same package)    │
        │  - nimbus[bedrock]                  │
        │  - nimbus[openai]                   │
        │  - nimbus[agents]                   │
        │  - nimbus[prompts]                  │
        │  - nimbus[tools]                    │
        │  - nimbus[memory]                   │
        │  - nimbus[guard]                    │
        │  - nimbus[observe]                  │
        └─────────────────────────────────────┘
```

### Dependency Flow

All optional extras depend on the base nimbus package. The base package has no dependencies on any extras, creating a stable foundation.

```
nimbus (base: interfaces + models)
    ↑
    │ optional extras
    │
    ├── nimbus[bedrock] (AWS Bedrock provider)
    ├── nimbus[openai] (OpenAI provider)
    ├── nimbus[anthropic] (Anthropic provider)
    ├── nimbus[agents] (Agent runtime)
    ├── nimbus[prompts] (Prompt management)
    ├── nimbus[tools] (Capabilities/tools)
    ├── nimbus[memory] (Persistent memory)
    ├── nimbus[guard] (Safety filters)
    └── nimbus[observe] (Observability)
```

## Components and Interfaces

### 1. Message Types

Different message types for structured conversation handling.

**Purpose**: Provide type-safe message representations for different roles and contexts.

**Message Type Definitions**:
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime

class NimbusMessage(BaseModel):
    """Base class for all message types."""
    content: str
    role: Literal["user", "assistant", "system", "capability"]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def message_type(self) -> str:
        """Return the message type."""
        return self.role
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "id": self.id,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NimbusMessage":
        """Create message from dictionary format."""
        role = data.get("role")
        if role == "user":
            return UserMessage(**data)
        elif role == "assistant":
            return AssistantMessage(**data)
        elif role == "system":
            return SystemMessage(**data)
        elif role == "capability":
            return CapabilityMessage(**data)
        else:
            return cls(**data)
    
    def format_for_provider(self, provider: str) -> Dict[str, Any]:
        """Format message for specific provider (OpenAI, Anthropic, etc.)."""
        # Base implementation - can be overridden by subclasses
        return {"role": self.role, "content": self.content}

class UserMessage(NimbusMessage):
    """Message from a user."""
    role: Literal["user"] = "user"

class AssistantMessage(NimbusMessage):
    """Message from an AI assistant."""
    role: Literal["assistant"] = "assistant"
    capability_calls: List[Dict[str, Any]] = Field(default_factory=list)
    
    def format_for_provider(self, provider: str) -> Dict[str, Any]:
        """Format assistant message with capability calls for provider."""
        base = super().format_for_provider(provider)
        if self.capability_calls:
            if provider == "openai":
                base["tool_calls"] = self.capability_calls
            elif provider == "anthropic":
                base["tool_use"] = self.capability_calls
        return base

class SystemMessage(NimbusMessage):
    """System-level instruction message."""
    role: Literal["system"] = "system"

class CapabilityMessage(NimbusMessage):
    """Message containing capability execution results."""
    role: Literal["capability"] = "capability"
    capability_id: str
    capability_name: str
    
    def format_for_provider(self, provider: str) -> Dict[str, Any]:
        """Format capability message for provider."""
        base = {"role": "tool" if provider == "openai" else "user", "content": self.content}
        if provider == "openai":
            base["tool_call_id"] = self.capability_id
            base["name"] = self.capability_name
        return base
```

### 2. ModelInterface

The core abstraction for LLM provider interactions.

**Purpose**: Define a contract for invoking language models regardless of the underlying provider.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import Iterator, Optional
from nimbus.models import CompletionRequest, CompletionResponse, StreamChunk

class ModelInterface(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a synchronous completion request."""
        pass
    
    @abstractmethod
    def stream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Execute a streaming completion request."""
        pass
    
    @abstractmethod
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute an asynchronous completion request."""
        pass
    
    @abstractmethod
    async def astream(self, request: CompletionRequest) -> Iterator[StreamChunk]:
        """Execute an asynchronous streaming completion request."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> dict:
        """Return metadata about the model (name, provider, capabilities)."""
        pass
```

**Key Design Decisions**:
- Supports both sync and async operations
- Streaming is a first-class citizen
- Request/response use Pydantic models for validation
- Provider-specific details are abstracted away

### 2. PromptBuilderInterface

Abstraction for prompt template management and rendering.

**Purpose**: Enable reusable, parameterized prompts with version control.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from nimbus.models import Message

class PromptBuilderInterface(ABC):
    """Abstract interface for prompt template management."""
    
    @abstractmethod
    def render(self, template_name: str, variables: Dict[str, Any]) -> List[Message]:
        """Render a template with provided variables into messages."""
        pass
    
    @abstractmethod
    def register_template(self, name: str, template: str, version: str = "1.0") -> None:
        """Register a new prompt template."""
        pass
    
    @abstractmethod
    def get_template(self, name: str, version: Optional[str] = None) -> str:
        """Retrieve a template by name and optional version."""
        pass
```

### 3. CapabilityInterface

Abstraction for tools/functions that agents can invoke.

**Purpose**: Define executable capabilities that extend agent functionality.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel

class CapabilitySchema(BaseModel):
    """Schema defining a capability's signature."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema format
    returns: Dict[str, Any]

class CapabilityInterface(ABC):
    """Abstract interface for agent capabilities (tools)."""
    
    @abstractmethod
    def get_schema(self) -> CapabilitySchema:
        """Return the capability's schema for LLM function calling."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the capability with provided arguments."""
        pass
    
    @abstractmethod
    async def aexecute(self, **kwargs) -> Any:
        """Execute the capability asynchronously."""
        pass
```

### 4. MemoryInterface

Abstraction for persistent memory storage and retrieval.

**Purpose**: Enable agents to store and recall information across sessions.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from nimbus.models import MemoryEntry

class MemoryInterface(ABC):
    """Abstract interface for memory storage."""
    
    @abstractmethod
    def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry and return its ID."""
        pass
    
    @abstractmethod
    def retrieve(self, query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[MemoryEntry]:
        """Retrieve relevant memories based on query."""
        pass
    
    @abstractmethod
    def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory by ID."""
        pass
    
    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        pass
```

### 5. SafetyFilterInterface

Abstraction for input/output validation and moderation.

**Purpose**: Provide guardrails for safe AI interactions.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import List
from nimbus.models import Message, SafetyResult

class SafetyFilterInterface(ABC):
    """Abstract interface for safety filters and guardrails."""
    
    @abstractmethod
    def validate_input(self, messages: List[Message]) -> SafetyResult:
        """Validate input messages before sending to model."""
        pass
    
    @abstractmethod
    def validate_output(self, response: str) -> SafetyResult:
        """Validate model output before returning to user."""
        pass
    
    @abstractmethod
    def get_policies(self) -> List[str]:
        """Return list of active safety policies."""
        pass
```

### 6. ObserverInterface

Abstraction for telemetry, logging, and monitoring.

**Purpose**: Enable observability without coupling to specific monitoring tools.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum

class EventType(Enum):
    MODEL_CALL = "model_call"
    CAPABILITY_EXECUTION = "capability_execution"
    MEMORY_ACCESS = "memory_access"
    ERROR = "error"

class ObserverInterface(ABC):
    """Abstract interface for observability."""
    
    @abstractmethod
    def log_event(self, event_type: EventType, data: Dict[str, Any], correlation_id: str) -> None:
        """Log an event with structured data."""
        pass
    
    @abstractmethod
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str]) -> None:
        """Record a metric value."""
        pass
    
    @abstractmethod
    def start_trace(self, operation_name: str) -> str:
        """Start a distributed trace and return trace ID."""
        pass
    
    @abstractmethod
    def end_trace(self, trace_id: str, status: str) -> None:
        """End a distributed trace."""
        pass
```

### 7. StorageAdapterInterface

Abstraction for data persistence backends.

**Purpose**: Decouple storage implementation from business logic.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class StorageAdapterInterface(ABC):
    """Abstract interface for storage backends."""
    
    @abstractmethod
    def save(self, collection: str, data: Dict[str, Any]) -> str:
        """Save data to a collection and return ID."""
        pass
    
    @abstractmethod
    def query(self, collection: str, filters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Query data from a collection."""
        pass
    
    @abstractmethod
    def vector_search(self, collection: str, embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        pass
    
    @abstractmethod
    def delete(self, collection: str, item_id: str) -> bool:
        """Delete an item from a collection."""
        pass
```

### 8. PluginInterface

Abstraction for plugin lifecycle management.

**Purpose**: Enable dynamic plugin registration and initialization.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class PluginInterface(ABC):
    """Abstract interface for Nimbus plugins."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Clean up resources before shutdown."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata (name, version, dependencies)."""
        pass
```

### 9. EventHandlerInterface

Abstraction for event handling during execution.

**Purpose**: Enable hooking into various lifecycle events for logging, monitoring, or custom logic.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from nimbus.models import NimbusMessage, CompletionResponse

class EventHandlerInterface(ABC):
    """Abstract interface for execution event handlers."""
    
    @abstractmethod
    def on_model_invoke_start(self, messages: List[NimbusMessage], **kwargs) -> None:
        """Called when model invocation starts."""
        pass
    
    @abstractmethod
    def on_model_invoke_end(self, response: CompletionResponse, **kwargs) -> None:
        """Called when model invocation completes."""
        pass
    
    @abstractmethod
    def on_model_invoke_error(self, error: Exception, **kwargs) -> None:
        """Called when model invocation fails."""
        pass
    
    @abstractmethod
    def on_capability_invoke_start(self, capability_name: str, inputs: Dict[str, Any], **kwargs) -> None:
        """Called when a capability invocation starts."""
        pass
    
    @abstractmethod
    def on_capability_invoke_end(self, capability_name: str, output: Any, **kwargs) -> None:
        """Called when a capability invocation completes."""
        pass
    
    @abstractmethod
    def on_capability_invoke_error(self, capability_name: str, error: Exception, **kwargs) -> None:
        """Called when a capability invocation fails."""
        pass
    
    @abstractmethod
    def on_execution_step(self, step_name: str, step_data: Dict[str, Any], **kwargs) -> None:
        """Called on each execution step."""
        pass
    
    @abstractmethod
    def on_execution_complete(self, result: Any, **kwargs) -> None:
        """Called when execution completes."""
        pass
```

### 10. VectorEncoderInterface

Abstraction for text-to-vector encoding models.

**Purpose**: Provide a unified interface for generating vector representations from text.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import List

class VectorEncoderInterface(ABC):
    """Abstract interface for vector encoding models."""
    
    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """Encode a single text into a vector."""
        pass
    
    @abstractmethod
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into vectors."""
        pass
    
    @abstractmethod
    async def aencode(self, text: str) -> List[float]:
        """Encode a single text into a vector asynchronously."""
        pass
    
    @abstractmethod
    async def aencode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into vectors asynchronously."""
        pass
    
    @abstractmethod
    def get_vector_dimension(self) -> int:
        """Return the dimension of the output vectors."""
        pass
```

### 11. ContentReaderInterface

Abstraction for reading content from various sources.

**Purpose**: Standardize content ingestion from different file formats and sources.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import List, Iterator, Optional, Dict, Any
from nimbus.models import ContentChunk

class ContentReaderInterface(ABC):
    """Abstract interface for content readers."""
    
    @abstractmethod
    def read(self) -> List[ContentChunk]:
        """Read all content from the source."""
        pass
    
    @abstractmethod
    def read_stream(self) -> Iterator[ContentChunk]:
        """Stream content chunks one at a time."""
        pass
    
    @abstractmethod
    async def aread(self) -> List[ContentChunk]:
        """Read all content asynchronously."""
        pass
    
    @abstractmethod
    def get_reader_metadata(self) -> Dict[str, Any]:
        """Return metadata about the reader (supported formats, source type)."""
        pass
```

### 12. ModelRouterInterface

Abstraction for intelligent model routing and load balancing.

**Purpose**: Enable advanced routing strategies including load balancing, fallbacks, rate limiting, and cost optimization.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum
from nimbus.models import CompletionRequest, CompletionResponse, ModelConfig

class RoutingStrategy(Enum):
    """Available routing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    LOWEST_LATENCY = "lowest_latency"
    LOWEST_COST = "lowest_cost"
    RATE_LIMIT_AWARE = "rate_limit_aware"
    WEIGHTED = "weighted"

class ModelRouterInterface(ABC):
    """Abstract interface for model routing and load balancing."""
    
    @abstractmethod
    def register_model(self, config: ModelConfig) -> None:
        """Register a model configuration for routing."""
        pass
    
    @abstractmethod
    def select_model(self, request: CompletionRequest) -> ModelConfig:
        """Select the best model configuration based on routing strategy."""
        pass
    
    @abstractmethod
    def route_request(self, request: CompletionRequest) -> CompletionResponse:
        """Route request to selected model with fallback support."""
        pass
    
    @abstractmethod
    async def aroute_request(self, request: CompletionRequest) -> CompletionResponse:
        """Route request asynchronously with fallback support."""
        pass
    
    @abstractmethod
    def mark_model_failed(self, model_id: str, error: Exception) -> None:
        """Mark a model as failed for cooldown tracking."""
        pass
    
    @abstractmethod
    def get_model_health(self, model_id: str) -> Dict[str, Any]:
        """Get health metrics for a model (success rate, latency, etc.)."""
        pass
    
    @abstractmethod
    def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """Set the routing strategy."""
        pass
```



## Data Models

### Core Pydantic Models

All data structures use Pydantic for validation and serialization.

**ContentChunk Model**:
```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ContentChunk(BaseModel):
    """Represents a chunk of content with metadata."""
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_id: Optional[str] = None
    source: Optional[str] = None
    
    def __str__(self) -> str:
        return self.text
```

**Message Models** (see Message Types section above for NimbusMessage, UserMessage, AssistantMessage, SystemMessage, CapabilityMessage)

**CompletionRequest Model**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Type

class CompletionRequest(BaseModel):
    """Request for model completion."""
    messages: List[NimbusMessage]
    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stop: Optional[List[str]] = None
    stream: bool = False
    capabilities: Optional[List[Dict[str, Any]]] = None
    capability_choice: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None  # For structured outputs
    response_schema: Optional[Type[BaseModel]] = None  # Pydantic model for structured outputs
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**TokenUsage Model**:
```python
from pydantic import BaseModel

class TokenUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

**CompletionResponse Model**:
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
from datetime import datetime

class CompletionResponse(BaseModel):
    """Response from model completion."""
    id: str
    model: str
    provider: str
    content: str
    structured_output: Optional[BaseModel] = None  # Parsed structured output if requested
    role: str = "assistant"
    finish_reason: str
    usage: TokenUsage
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_output(self) -> Union[str, BaseModel]:
        """Get the output - structured if available, otherwise text content."""
        return self.structured_output if self.structured_output else self.content
```

**StreamChunk Model**:
```python
from pydantic import BaseModel
from typing import Optional

class StreamChunk(BaseModel):
    """A chunk from a streaming response."""
    id: str
    delta: str
    finish_reason: Optional[str] = None
    index: int = 0
```

**MemoryEntry Model**:
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class MemoryEntry(BaseModel):
    """A single memory entry."""
    id: Optional[str] = None
    content: str
    memory_type: str  # episodic, semantic, persona
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**SafetyResult Model**:
```python
from pydantic import BaseModel
from typing import List, Optional

class SafetyResult(BaseModel):
    """Result of safety validation."""
    is_safe: bool
    violations: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    filtered_content: Optional[str] = None
```

## Structured Output Support

### Overview

Nimbus-core provides built-in support for structured outputs, allowing models to return typed, validated data structures instead of raw text.

### Usage Pattern

```python
from pydantic import BaseModel
from nimbus.models import CompletionRequest, UserMessage

class PersonInfo(BaseModel):
    name: str
    age: int
    occupation: str

request = CompletionRequest(
    messages=[UserMessage(content="Extract person info: John is 30 and works as an engineer")],
    model="gpt-4",
    response_schema=PersonInfo
)

response = model.complete(request)
person = response.structured_output  # Returns PersonInfo instance
```

### Implementation Strategy

1. **Schema Generation**: Convert Pydantic models to JSON Schema
2. **Provider Adaptation**: Transform schema to provider-specific format (OpenAI's `response_format`, Anthropic's tool use pattern)
3. **Response Parsing**: Parse model output and validate against schema
4. **Error Handling**: Provide clear errors if output doesn't match schema

### Provider-Specific Handling

Different providers handle structured outputs differently:

- **OpenAI**: Native `response_format` with JSON schema
- **Anthropic**: Use tool calling pattern with single tool
- **Others**: Prompt engineering + post-processing validation

The ModelInterface implementations handle these differences transparently.

## Error Handling

### Exception Hierarchy

```python
class NimbusError(Exception):
    """Base exception for all Nimbus errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ProviderError(NimbusError):
    """Error from an LLM provider."""
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, {"provider": provider, "status_code": status_code, **kwargs})

class ConfigurationError(NimbusError):
    """Error in configuration."""
    pass

class ValidationError(NimbusError):
    """Error in data validation."""
    def __init__(self, message: str, field: str, value: Any):
        super().__init__(message, {"field": field, "value": value})

class CapabilityExecutionError(NimbusError):
    """Error during capability execution."""
    def __init__(self, message: str, capability_name: str, **kwargs):
        super().__init__(message, {"capability": capability_name, **kwargs})
```

### Error Handling Strategy

1. **Wrap provider-specific errors** in ProviderError with context
2. **Log all errors** with appropriate severity
3. **Include correlation IDs** for tracing
4. **Preserve stack traces** for debugging
5. **Return structured error responses** to callers

## Configuration Management

### Configuration Sources (Priority Order)

1. **Code** - Explicit parameters passed to constructors
2. **Environment Variables** - NIMBUS_* prefixed variables
3. **Configuration Files** - YAML/JSON files

### Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class RateLimitConfig(BaseModel):
    """Rate limit configuration for a model."""
    requests_per_minute: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_day: Optional[int] = None

class RetryConfig(BaseModel):
    """Retry configuration for a model."""
    max_retries: int = 3
    retry_after_seconds: int = 5
    exponential_backoff: bool = True
    retry_on_errors: List[str] = Field(default_factory=lambda: ["rate_limit", "timeout", "server_error"])

class CooldownConfig(BaseModel):
    """Cooldown configuration for failed models."""
    enabled: bool = True
    allowed_fails_per_minute: int = 3
    cooldown_duration_seconds: int = 60

class ModelConfig(BaseModel):
    """Configuration for a model."""
    model_id: str
    provider: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60
    
    # Advanced routing features
    rate_limits: Optional[RateLimitConfig] = None
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    cooldown_config: CooldownConfig = Field(default_factory=CooldownConfig)
    fallback_models: List[str] = Field(default_factory=list)
    
    # Load balancing
    weight: float = 1.0  # For weighted routing
    priority: int = 0  # Higher priority models are preferred
    tags: List[str] = Field(default_factory=list)  # For tag-based routing
    
    # Cost tracking
    cost_per_1k_prompt_tokens: Optional[float] = None
    cost_per_1k_completion_tokens: Optional[float] = None

class NimbusConfig(BaseModel):
    """Global Nimbus configuration."""
    log_level: str = "INFO"
    enable_telemetry: bool = True
    correlation_id_header: str = "X-Correlation-ID"
    models: Dict[str, ModelConfig] = Field(default_factory=dict)
    plugins: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Router configuration
    default_routing_strategy: str = "round_robin"
    enable_fallbacks: bool = True
    enable_rate_limiting: bool = True
```

### ConfigLoader Implementation

```python
import os
import yaml
import json
from pathlib import Path
from typing import Optional

class ConfigLoader:
    """Loads configuration from multiple sources."""
    
    @staticmethod
    def load(config_path: Optional[Path] = None, overrides: Optional[Dict] = None) -> NimbusConfig:
        """Load configuration with precedence: overrides > env > file."""
        config_data = {}
        
        # 1. Load from file
        if config_path and config_path.exists():
            with open(config_path) as f:
                if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
                    config_data = yaml.safe_load(f)
                elif config_path.suffix == '.json':
                    config_data = json.load(f)
        
        # 2. Override with environment variables
        for key, value in os.environ.items():
            if key.startswith('NIMBUS_'):
                config_key = key[7:].lower()  # Remove NIMBUS_ prefix
                config_data[config_key] = value
        
        # 3. Apply code overrides
        if overrides:
            config_data.update(overrides)
        
        return NimbusConfig(**config_data)
```

## Testing Strategy

### Unit Testing

- **Interface Compliance Tests**: Verify that implementations satisfy interface contracts
- **Pydantic Model Tests**: Validate data model validation rules
- **Configuration Tests**: Test configuration loading from different sources
- **Exception Tests**: Verify exception hierarchy and error handling

### Integration Testing

- **Mock Provider Tests**: Test ModelInterface with mock providers
- **Plugin Registration Tests**: Test dynamic plugin loading
- **Configuration Integration**: Test multi-source configuration merging

### Test Structure

```
tests/
├── unit/
│   ├── test_interfaces.py
│   ├── test_models.py
│   ├── test_exceptions.py
│   └── test_config.py
├── integration/
│   ├── test_plugin_system.py
│   └── test_config_loading.py
└── fixtures/
    ├── sample_config.yaml
    └── mock_providers.py
```

## Package Structure

```
nimbus/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── nimbus/
│       ├── __init__.py              # Core exports
│       ├── completion.py            # CompletionRequest, CompletionResponse, etc.
│       ├── messages.py              # UserMessage, AssistantMessage, etc.
│       ├── memory.py                # MemoryEntry, etc.
│       ├── exceptions.py            # NimbusError hierarchy
│       ├── config.py                # ModelConfig, NimbusConfig, ConfigLoader
│       ├── interfaces/              # All interface definitions (always included)
│       │   ├── __init__.py
│       │   ├── model.py
│       │   ├── prompt.py
│       │   ├── capability.py
│       │   ├── memory.py
│       │   ├── safety.py
│       │   ├── observer.py
│       │   ├── storage.py
│       │   ├── plugin.py
│       │   ├── event_handler.py
│       │   ├── vector_encoder.py
│       │   ├── content_reader.py
│       │   └── router.py
│       ├── providers/               # Optional: [bedrock], [openai], [anthropic]
│       │   ├── __init__.py
│       │   ├── bedrock.py
│       │   ├── openai.py
│       │   └── anthropic.py
│       ├── agents/                  # Optional: [agents]
│       │   ├── __init__.py
│       │   └── runtime.py
│       ├── prompts/                 # Optional: [prompts]
│       │   ├── __init__.py
│       │   └── builder.py
│       ├── tools/                   # Optional: [tools]
│       │   ├── __init__.py
│       │   └── registry.py
│       ├── memory/                  # Optional: [memory] (implementations)
│       │   ├── __init__.py
│       │   ├── episodic.py
│       │   └── semantic.py
│       ├── guard/                   # Optional: [guard]
│       │   ├── __init__.py
│       │   └── filters.py
│       ├── observe/                 # Optional: [observe]
│       │   ├── __init__.py
│       │   └── telemetry.py
│       └── utils/
│           ├── __init__.py
│           └── validation.py
└── tests/
    ├── unit/
    └── integration/
```

## Dependencies

### Base Dependencies (Always Installed)

```toml
[project]
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
]
```

### Optional Dependencies (Extras)

```toml
[project.optional-dependencies]
# Individual providers
bedrock = ["boto3>=1.28"]
openai = ["openai>=1.0"]
anthropic = ["anthropic>=0.25"]
azure = ["azure-ai-inference>=1.0.0b1"]

# Individual components
agents = []
prompts = []
tools = []
memory = ["redis>=5.0", "psycopg2-binary>=2.9"]
guard = []
observe = ["opentelemetry-api>=1.20", "prometheus-client>=0.19"]

# Convenience bundles
providers = ["boto3>=1.28", "openai>=1.0", "anthropic>=0.25", "azure-ai-inference>=1.0.0b1"]
all = ["boto3>=1.28", "openai>=1.0", "anthropic>=0.25", "azure-ai-inference>=1.0.0b1", "redis>=5.0", "psycopg2-binary>=2.9", "opentelemetry-api>=1.20", "prometheus-client>=0.19"]
```

### Development Dependencies

```toml
[dependency-groups]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
```

## Design Principles

1. **Dependency Inversion**: All components depend on abstractions, not concretions
2. **Interface Segregation**: Interfaces are focused and minimal
3. **Single Responsibility**: Each interface has one clear purpose
4. **Open/Closed**: Open for extension (plugins), closed for modification (core interfaces)
5. **Liskov Substitution**: Any implementation of an interface can be substituted
6. **Type Safety**: Strong typing with Pydantic and type hints
7. **Fail Fast**: Validate early with clear error messages
8. **Zero Coupling**: No dependencies between optional components

## Future Considerations

- **Versioning Strategy**: Semantic versioning with interface stability guarantees
- **Backward Compatibility**: Deprecation policy for interface changes
- **Performance**: Benchmarking framework for interface implementations
- **Documentation**: Auto-generated API docs from type hints and docstrings
- **Plugin Discovery**: Automatic plugin discovery via entry points
