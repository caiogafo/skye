---
title: "Provider Transformation Architecture"
status: current
last_updated: 2026-11-02
---

# Provider Transformation Architecture

## Overview

This document describes the provider transformation architecture in Skye, which ensures complete provider encapsulation and makes the core library provider-agnostic.

## Core Principle

**All provider-specific transformation logic MUST be encapsulated within provider client classes.**

This principle ensures:
- Core library remains provider-agnostic
- Adding new providers requires no changes to core code
- Provider-specific logic is isolated and maintainable
- Clear separation of concerns

## Architecture Components

### 1. Provider Client Classes

Each provider client (e.g., `OpenAIProvider`, `BedrockProvider`) inherits from `BaseModelProvider` and implements all transformation methods:

```python
class OpenAIProvider(BaseModelProvider):
    """OpenAI provider with all transformations encapsulated."""
    
    def _transform_messages(self, messages: list[SkyeMessage]) -> list[dict[str, Any]]:
        """Transform Skye messages to OpenAI format."""
        # All OpenAI-specific message transformation logic here
        pass
    
    def _transform_capabilities(self, capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """Transform Skye capabilities to OpenAI tool format."""
        # All OpenAI-specific capability transformation logic here
        pass
    
    def _extract_capability_calls(self, response: Any) -> list[CapabilityCall] | None:
        """Extract capability calls from OpenAI response."""
        # All OpenAI-specific extraction logic here
        pass
    
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform CompletionRequest to OpenAI format."""
        # Uses internal transformation methods
        return {
            "model": request.model,
            "messages": self._transform_messages(request.messages),
            "tools": self._transform_capabilities(request.capabilities) if request.capabilities else None,
            # ... other OpenAI-specific mappings
        }
    
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform OpenAI response to CompletionResponse."""
        # Uses internal extraction methods
        tool_calls = self._extract_capability_calls(response)
        return CompletionResponse(...)
```

### 2. Thin Delegation Layers

Core library transformers are thin delegation layers that forward to provider methods:

#### MessageTransformer

```python
class MessageTransformer:
    """Thin delegation layer for message transformations."""
    
    @staticmethod
    def transform_for_provider(
        messages: list[SkyeMessage],
        provider: BaseModelProvider
    ) -> list[dict[str, Any]]:
        """Delegate to provider's transformation method."""
        return provider._transform_messages(messages)
```

#### CapabilityTransformer

```python
class CapabilityTransformer:
    """Thin delegation layer for capability transformations."""
    
    @staticmethod
    def transform_for_provider(
        capabilities: list[CapabilityInterface],
        provider: BaseModelProvider
    ) -> list[dict[str, Any]]:
        """Delegate to provider's transformation method."""
        return provider._transform_capabilities(capabilities)
```

### 3. Provider-Agnostic Core Library

Core library modules use only Skye-native models:

- **src/skye/router/** - Router and routing logic
- **src/skye/tools/** - Capability system
- **src/skye/base/completion.py** - Completion models
- **src/skye/base/messages.py** - Message models

These modules MUST NOT contain provider-specific code.

## Transformation Flow

### Request Flow

```
User Code
  ↓
CompletionRequest (Skye format)
  ↓
Router (provider-agnostic)
  ↓
Provider Client
  ↓
_transform_request()
  ├─ _transform_messages()
  └─ _transform_capabilities()
  ↓
Provider-Specific Request
  ↓
Provider API
```

### Response Flow

```
Provider API
  ↓
Provider-Specific Response
  ↓
Provider Client
  ↓
_transform_response()
  └─ _extract_capability_calls()
  ↓
CompletionResponse (Skye format)
  ↓
User Code
```

## Adding a New Provider

To add a new provider, you only need to:

1. Create a new provider class inheriting from `BaseModelProvider`
2. Implement all required transformation methods:
   - `_initialize_client()`
   - `_transform_messages()`
   - `_transform_capabilities()`
   - `_extract_capability_calls()`
   - `_transform_request()`
   - `_transform_response()`
   - `_transform_stream_chunk()`
   - `_call_provider()`
   - `_call_provider_stream()`
   - `get_model_info()`

3. No changes to core library code required!

### Example: Adding a New Provider

```python
class NewProvider(BaseModelProvider):
    """New provider implementation."""
    
    def _initialize_client(self) -> Any:
        """Initialize provider client."""
        import new_provider_sdk
        return new_provider_sdk.Client(api_key=self.config["api_key"])
    
    def _transform_messages(self, messages: list[SkyeMessage]) -> list[dict[str, Any]]:
        """Transform to provider-specific message format."""
        # All provider-specific logic here
        return [{"role": msg.role, "text": msg.content} for msg in messages]
    
    def _transform_capabilities(self, capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """Transform to provider-specific tool format."""
        # All provider-specific logic here
        return [{"name": cap.get_schema().name, ...} for cap in capabilities]
    
    def _extract_capability_calls(self, response: Any) -> list[CapabilityCall] | None:
        """Extract capability calls from provider response."""
        # All provider-specific logic here
        if not response.tool_calls:
            return None
        return [CapabilityCall(id=tc.id, name=tc.name, ...) for tc in response.tool_calls]
    
    # ... implement other required methods
```

## Known Architectural Debt

### CapabilityCallHandler

The `CapabilityCallHandler` class in `src/skye/tools/capability_call_handler.py` currently contains provider-specific parsing and formatting methods:

- `_parse_openai_capability_calls()`
- `_parse_anthropic_capability_calls()`
- `_parse_bedrock_capability_calls()`
- `_parse_google_capability_calls()`
- `_format_openai_results()`
- `_format_anthropic_results()`
- `_format_bedrock_results()`
- `_format_google_results()`

**Status**: This is documented architectural debt. The provider clients already implement `_extract_capability_calls()` which is used during response transformation, so the `CapabilityCallHandler` provides an alternative interface for capability execution workflows.

**Future Refactor**: In a future refactor, this logic should be moved to provider classes as:
- `provider._parse_capability_calls(response)` - Parse from provider response
- `provider._format_capability_results(results)` - Format for provider

This would make `CapabilityCallHandler` a thin delegation layer like `MessageTransformer` and `CapabilityTransformer`, completing the provider encapsulation architecture.

## Validation

To validate the architecture, run:

```bash
python scripts/validate_provider_architecture.py
```

This script checks:
1. All provider-specific transformation logic is in provider client classes
2. No provider-specific code exists in core library modules
3. MessageTransformer and CapabilityTransformer only delegate to providers
4. Adding a new provider requires no changes to core library code

## Benefits

### 1. Provider Agnosticism

Core library code never needs to know about specific providers:

```python
# Router code (provider-agnostic)
def route_request(self, request: CompletionRequest) -> CompletionResponse:
    provider = self._select_provider(request.model)
    return provider.complete(request)  # Provider handles all transformations
```

### 2. Easy Provider Addition

Adding a new provider is straightforward:

```python
# Just create a new provider class
class MyNewProvider(BaseModelProvider):
    # Implement transformation methods
    pass

# No changes to core library needed!
```

### 3. Maintainability

Provider-specific logic is isolated:

```python
# All OpenAI logic in one place
class OpenAIProvider(BaseModelProvider):
    def _transform_messages(self, messages):
        # OpenAI-specific logic
        pass
    
    def _transform_capabilities(self, capabilities):
        # OpenAI-specific logic
        pass
```

### 4. Testability

Each provider can be tested independently:

```python
def test_openai_message_transformation():
    provider = OpenAIProvider(api_key="test")
    messages = [UserMessage(content="Hello")]
    transformed = provider._transform_messages(messages)
    assert transformed == [{"role": "user", "content": "Hello"}]
```

## Anti-Patterns to Avoid

### ❌ Provider-Specific Code in Core Library

```python
# BAD: Provider-specific logic in router
class ModelRouter:
    def route_request(self, request):
        if request.provider == "openai":
            # OpenAI-specific transformation
            transformed = self._transform_for_openai(request)
        elif request.provider == "bedrock":
            # Bedrock-specific transformation
            transformed = self._transform_for_bedrock(request)
```

### ❌ Provider-Specific Methods in Transformers

```python
# BAD: Provider-specific methods in transformer
class MessageTransformer:
    def to_openai_format(self, messages):
        # OpenAI-specific logic
        pass
    
    def to_bedrock_format(self, messages):
        # Bedrock-specific logic
        pass
```

### ✅ Correct Pattern: Delegation

```python
# GOOD: Delegation to provider
class MessageTransformer:
    @staticmethod
    def transform_for_provider(messages, provider):
        return provider._transform_messages(messages)
```

## References

- [BaseModelProvider](../../src/skye/models/base.py) - Base provider class with transformation methods
- [OpenAIProvider](../../src/skye/models/llm/openai_compatible.py) - Example provider implementation
- [BedrockProvider](../../src/skye/models/llm/bedrock.py) - Example provider implementation
- `MessageTransformer` (`models/transformers.py`) - thin delegation layer; the file no longer exists, the logic lives in each adapter
- `CapabilityTransformer` (`tools/capability_transformer.py`) - thin delegation layer; the file no longer exists, the logic lives in each adapter
