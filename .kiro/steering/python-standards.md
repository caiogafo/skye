---
inclusion: always
---

# Python Standards for Nimbus

## Python Version

- **Minimum**: Python 3.10
- **Recommended**: Python 3.11 or 3.12
- **Rationale**: Modern type hints, pattern matching, better performance

## Code Style

### Formatting

Use **Black** for code formatting:
```bash
black src/ tests/
```

Configuration in pyproject.toml:
```toml
[tool.black]
line-length = 100
target-version = ['py310']
```

### Linting

Use **Ruff** for fast linting:
```bash
ruff check src/ tests/
```

Configuration in pyproject.toml:
```toml
[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "I", "N", "W", "UP"]
```

### Type Checking

Use **mypy** for static type checking:
```bash
mypy src/
```

Configuration in pyproject.toml:
```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
```

## Type Hints

### Always Use Type Hints

```python
# ✅ Good
def process_message(message: str, max_length: int = 100) -> str:
    return message[:max_length]

# ❌ Bad
def process_message(message, max_length=100):
    return message[:max_length]
```

### Use Modern Type Hint Syntax

```python
# ✅ Good (Python 3.10+)
def get_items() -> list[str]:
    return ["item1", "item2"]

def get_config() -> dict[str, Any]:
    return {"key": "value"}

# ❌ Bad (old style)
from typing import List, Dict
def get_items() -> List[str]:
    return ["item1", "item2"]
```

### Use Optional and Union Correctly

```python
from typing import Optional, Union

# ✅ Good
def find_user(user_id: str) -> Optional[User]:
    return user_db.get(user_id)

# ✅ Also good (Python 3.10+)
def find_user(user_id: str) -> User | None:
    return user_db.get(user_id)
```

### Use TypeVar for Generics

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value
    
    def get(self) -> T:
        return self.value
```

## Pydantic Best Practices

### Use Pydantic v2

```python
from pydantic import BaseModel, Field, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(frozen=True)  # Immutable
    
    name: str
    age: int = Field(gt=0, le=150)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
```

### Use Field for Validation

```python
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0)
    model_id: str = Field(min_length=1)
```

### Use Validators for Complex Logic

```python
from pydantic import BaseModel, field_validator

class CompletionRequest(BaseModel):
    messages: list[NimbusMessage]
    model: str
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v: list[NimbusMessage]) -> list[NimbusMessage]:
        if not v:
            raise ValueError('messages cannot be empty')
        return v
```

## Async/Await Patterns

### Naming Convention

Prefix async functions with `a`:

```python
# ✅ Good
async def acomplete(request: CompletionRequest) -> CompletionResponse:
    ...

async def aencode(text: str) -> list[float]:
    ...

# ❌ Bad
async def complete_async(request: CompletionRequest) -> CompletionResponse:
    ...
```

### Use asyncio Properly

```python
import asyncio

# ✅ Good
async def process_batch(items: list[str]) -> list[str]:
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)

# ❌ Bad (blocking in async function)
async def process_batch(items: list[str]) -> list[str]:
    results = []
    for item in items:
        result = process_item_sync(item)  # Blocking!
        results.append(result)
    return results
```

### Provide Both Sync and Async

```python
class ModelInterface(ABC):
    @abstractmethod
    def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Synchronous completion."""
        pass
    
    @abstractmethod
    async def acomplete(self, request: CompletionRequest) -> CompletionResponse:
        """Asynchronous completion."""
        pass
```

## Error Handling

### Use Custom Exceptions

```python
# ✅ Good
class NimbusError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ProviderError(NimbusError):
    def __init__(self, message: str, provider: str, **kwargs):
        super().__init__(message, {"provider": provider, **kwargs})
```

### Preserve Context

```python
# ✅ Good
try:
    result = external_api_call()
except ExternalAPIError as e:
    raise ProviderError(
        f"Provider call failed: {e}",
        provider="openai",
        original_error=str(e)
    ) from e

# ❌ Bad (loses context)
try:
    result = external_api_call()
except ExternalAPIError as e:
    raise ProviderError("Provider call failed")
```

### Use Context Managers

```python
# ✅ Good
class ResourceManager:
    def __enter__(self):
        self.resource = acquire_resource()
        return self.resource
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.resource.cleanup()
        return False

# Usage
with ResourceManager() as resource:
    resource.use()
```

## Testing

### Use pytest

```python
import pytest
from nimbus_core.models import NimbusMessage, UserMessage

def test_user_message_creation():
    msg = UserMessage(content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"

def test_message_validation():
    with pytest.raises(ValidationError):
        UserMessage(content="")  # Empty content should fail

@pytest.mark.asyncio
async def test_async_completion():
    response = await model.acomplete(request)
    assert response.content
```

### Use Fixtures

```python
import pytest

@pytest.fixture
def sample_config():
    return ModelConfig(
        model_id="gpt-4",
        provider="openai",
        temperature=0.7
    )

def test_with_fixture(sample_config):
    assert sample_config.model_id == "gpt-4"
```

### Use Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("temperature,expected", [
    (0.0, True),
    (0.7, True),
    (2.0, True),
    (-0.1, False),
    (2.1, False),
])
def test_temperature_validation(temperature, expected):
    try:
        config = ModelConfig(model_id="test", provider="test", temperature=temperature)
        assert expected is True
    except ValidationError:
        assert expected is False
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def complete(self, request: CompletionRequest) -> CompletionResponse:
    """Execute a completion request.
    
    Args:
        request: The completion request containing messages and parameters.
    
    Returns:
        CompletionResponse containing the model's response and metadata.
    
    Raises:
        ProviderError: If the provider API call fails.
        ValidationError: If the request is invalid.
    
    Example:
        >>> request = CompletionRequest(
        ...     messages=[UserMessage(content="Hello")],
        ...     model="gpt-4"
        ... )
        >>> response = model.complete(request)
        >>> print(response.content)
    """
    pass
```

### Module Docstrings

```python
"""Model interface definitions for Nimbus.

This module provides the core ModelInterface that all LLM provider
implementations must follow. It supports both synchronous and asynchronous
operations, streaming, and structured outputs.

Example:
    >>> from nimbus_core.interfaces import ModelInterface
    >>> from nimbus_providers.openai import OpenAIModel
    >>> 
    >>> model = OpenAIModel(api_key="...")
    >>> response = model.complete(request)
"""
```

## Dependency Management

### Use uv

```toml
[project]
name = "nimbus"
version = "0.1.0"
description = "Modular GenAI library with optional extras"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
# Optional dependencies
bedrock = ["boto3>=1.28"]
openai = ["openai>=1.0"]
all = ["boto3>=1.28", "openai>=1.0"]

[dependency-groups]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
```

### Pin Major Versions

```toml
# ✅ Good
"pydantic>=2.0"  # Allows 2.x updates
"requests>=2.31"

# ❌ Bad
"pydantic"  # Too loose (no version constraint)
"requests==2.31.0"  # Too strict (exact pin)
```

## Performance

### Use __slots__ for Performance-Critical Classes

```python
class Message:
    __slots__ = ('content', 'role', 'metadata')
    
    def __init__(self, content: str, role: str):
        self.content = content
        self.role = role
        self.metadata = {}
```

### Use Generators for Large Datasets

```python
# ✅ Good
def read_large_file(path: str) -> Iterator[str]:
    with open(path) as f:
        for line in f:
            yield line.strip()

# ❌ Bad (loads everything into memory)
def read_large_file(path: str) -> list[str]:
    with open(path) as f:
        return [line.strip() for line in f]
```

### Cache Expensive Operations

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_model_config(model_id: str) -> ModelConfig:
    # Expensive operation
    return load_config_from_db(model_id)
```

## Security

### Never Hardcode Secrets

```python
# ✅ Good
import os
api_key = os.getenv("OPENAI_API_KEY")

# ❌ Bad
api_key = "sk-1234567890abcdef"
```

### Validate All Inputs

```python
# ✅ Good
class CompletionRequest(BaseModel):
    messages: list[NimbusMessage]
    model: str = Field(min_length=1)
    temperature: float = Field(ge=0.0, le=2.0)

# ❌ Bad (no validation)
class CompletionRequest:
    def __init__(self, messages, model, temperature):
        self.messages = messages
        self.model = model
        self.temperature = temperature
```

### Use Secrets Management

```python
# ✅ Good
from pathlib import Path
import json

def load_secrets() -> dict[str, str]:
    secrets_path = Path.home() / ".nimbus" / "secrets.json"
    if secrets_path.exists():
        return json.loads(secrets_path.read_text())
    return {}
```

## Logging

### Use Structured Logging

```python
import logging
import json

logger = logging.getLogger(__name__)

# ✅ Good
logger.info(
    "Model invocation completed",
    extra={
        "model_id": "gpt-4",
        "tokens_used": 150,
        "latency_ms": 234,
        "correlation_id": "abc-123"
    }
)

# ❌ Bad
logger.info(f"Model gpt-4 used 150 tokens in 234ms")
```

### Use Appropriate Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical messages for very serious errors

```python
logger.debug("Request payload: %s", request.dict())
logger.info("Processing completion request")
logger.warning("Rate limit approaching: %d/%d", current, limit)
logger.error("Provider API call failed", exc_info=True)
logger.critical("System shutdown initiated")
```
