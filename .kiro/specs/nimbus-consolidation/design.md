# Design Document

## Overview

This design outlines a comprehensive consolidation effort for the Nimbus library to ensure consistent naming conventions, enhance configuration management with YAML support and environment variable substitution, improve test organization and coverage, and update documentation to reflect the current state of the codebase.

The consolidation addresses several key areas:
1. **Terminology Consistency**: Standardize on "Capability" terminology throughout
2. **Configuration Enhancement**: Add YAML configuration support with environment variable substitution
3. **Test Organization**: Restructure tests into clear categories with improved coverage
4. **Documentation Updates**: Ensure steering documents accurately reflect current architecture
5. **Example Reorganization**: Improve example structure and documentation

## Architecture

### Current State Analysis

The codebase currently has:
- Mixed terminology in some areas (tool_models.py, tool_call_handler.py, tool_transformer.py)
- Router configuration only via Python code
- Tests scattered across unit/ and integration/ directories
- Examples in a flat structure under examples/
- Steering documents that may not reflect recent changes

### Target State

The refactored codebase will have:
- Consistent "Capability" terminology throughout
- YAML configuration support for routers with environment variable substitution
- Well-organized test structure: unit/, integration/, stress/
- Categorized examples with clear README files
- Updated steering documents reflecting current architecture

## Components and Interfaces

### 1. Configuration Loader for YAML

**Purpose**: Load router configurations from YAML files with environment variable substitution.

**Location**: `src/nimbus/config.py` (enhance existing)

**Key Methods**:
```python
def load_router_config(yaml_path: str) -> dict[str, Any]:
    """Load router configuration from YAML file with env var substitution."""
    
def substitute_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    """Recursively substitute ${VAR_NAME} with environment variables."""
```

**YAML Format**:
```yaml
routes:
  - alias: "gpt-3.5-turbo"
    strategy: "rate_limit_aware"
    targets:
      - model: "azure/chatgpt-v-2"
        provider: "azure"
        api_key: "${AZURE_API_KEY}"
        api_base: "${AZURE_API_BASE}"
        tpm: 100000
        rpm: 1000
      - model: "gpt-3.5-turbo"
        provider: "openai"
        api_key: "${OPENAI_API_KEY}"
        tpm: 200000
        rpm: 2000

fallbacks:
  - primary: "gpt-4"
    fallbacks: ["gpt-3.5-turbo"]

retry_policies:
  - error_type: "RateLimitError"
    max_retries: 3

allowed_fails_policies:
  - error_type: "RateLimitError"
    allowed_fails_per_minute: 100
```

### 2. ModelRouter Enhancement

**Purpose**: Support loading configuration from YAML files and environment variable substitution in Python config.

**Location**: `src/nimbus/routes/model_router.py`

**New Methods**:
```python
@classmethod
def from_yaml(cls, yaml_path: str, **kwargs) -> "ModelRouter":
    """Create router from YAML configuration file."""

@classmethod
def from_config_dict(cls, config: dict[str, Any], **kwargs) -> "ModelRouter":
    """Create router from configuration dictionary."""
```

**Enhanced ModelTarget**:
```python
class ModelTarget(BaseModel):
    # ... existing fields ...
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to substitute environment variables."""
        self._substitute_env_vars()
    
    def _substitute_env_vars(self) -> None:
        """Substitute ${VAR_NAME} patterns with environment variables."""
```

### 3. File Renaming Strategy

**Files to Rename**:
- `tool_models.py` → `capability_models.py`
- `tool_call_handler.py` → `capability_call_handler.py`
- `tool_transformer.py` → `capability_transformer.py`

**Classes to Rename**:
- `ToolCall` → `CapabilityCall`
- `ToolResult` → `CapabilityResult`
- `ToolCallHandler` → `CapabilityCallHandler`
- `ToolTransformer` → `CapabilityTransformer`

**Breaking Change**:
This is a clean break with no backward compatibility. All old names will be removed.

### 4. Test Organization

**New Structure**:
```
tests/
├── unit/                      # Fast, isolated tests
│   ├── capabilities/          # Capability system tests
│   ├── providers/             # Provider tests
│   ├── routes/                # Router tests
│   └── utils/                 # Utility tests
├── integration/               # Multi-component tests
│   ├── capabilities/          # End-to-end capability tests
│   ├── providers/             # Provider integration tests
│   └── routes/                # Router integration tests
├── stress/                    # Performance and load tests
│   ├── test_concurrent_routing.py
│   ├── test_rate_limiting.py
│   └── test_capability_load.py
└── fixtures/                  # Shared test fixtures
    ├── __init__.py
    ├── mock_responses.py
    ├── sample_configs.py
    └── images/
```

### 5. Example Reorganization

**New Structure**:
```
examples/
├── README.md                  # Overview of all examples
├── basic/                     # Basic usage examples
│   ├── README.md
│   ├── simple_completion.py
│   └── streaming_example.py
├── capabilities/              # Capability examples
│   ├── README.md
│   ├── local_function.py
│   ├── remote_api.py
│   └── mcp_server.py
├── providers/                 # Provider-specific examples
│   ├── README.md
│   ├── openai_example.py
│   ├── anthropic_example.py
│   ├── bedrock_example.py
│   ├── azure_example.py
│   └── vertex_example.py
├── routing/                   # Router examples
│   ├── README.md
│   ├── basic_routing.py
│   ├── yaml_config.py
│   ├── fallback_chains.py
│   └── rate_limiting.py
└── advanced/                  # Advanced patterns
    ├── README.md
    ├── multimodal.py
    ├── structured_output.py
    └── function_calling.py
```

## Data Models

### RouterConfig (New)

```python
class RouterConfig(BaseModel):
    """Complete router configuration from YAML."""
    
    routes: list[RouteConfig] = Field(default_factory=list)
    fallbacks: list[FallbackConfig] = Field(default_factory=list)
    retry_policies: list[RetryPolicyConfig] = Field(default_factory=list)
    allowed_fails_policies: list[AllowedFailsPolicyConfig] = Field(default_factory=list)
    strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN
    cooldown_seconds: float = 60.0
    enable_pre_call_checks: bool = True
```

### CapabilityCall (Renamed from ToolCall)

```python
class CapabilityCall(BaseModel):
    """Represents a capability invocation request from an LLM."""
    
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Capability name")
    arguments: dict[str, Any] = Field(default_factory=dict)
```

### CapabilityResult (Renamed from ToolResult)

```python
class CapabilityResult(BaseModel):
    """Represents the result of executing a capability."""
    
    capability_call_id: str = Field(..., description="ID of the capability call")
    name: str = Field(..., description="Capability name")
    result: Any = Field(default=None)
    error: str | None = Field(default=None)
```

### 6. Provider-Specific Transformation Consolidation

**Purpose**: Consolidate all provider-specific transformation logic into provider client classes, making the core library completely provider-agnostic.

**Current Problem**:
- Provider-specific transformations are scattered across multiple modules
- `MessageTransformer` has provider-specific methods (`to_openai_format`, `to_bedrock_format`)
- `CapabilityTransformer` has provider-specific methods
- Core library code needs to know about provider formats
- Adding a new provider requires changes to multiple files

**Target Architecture**:
- Each provider client class handles ALL transformations for that provider
- Core library uses only Nimbus-native models
- Transformers become thin delegation layers
- Adding a new provider only requires creating a new provider client class

**New Provider Client Interface**:
```python
class BaseModelProvider(ABC):
    """Base class for all model providers with transformation methods."""
    
    @abstractmethod
    def _transform_request(self, request: CompletionRequest) -> dict[str, Any]:
        """Transform Nimbus request to provider-specific format.
        
        This method handles ALL provider-specific transformations:
        - Message format conversion
        - Capability/tool format conversion
        - Parameter mapping
        - Provider-specific options
        """
        pass
    
    @abstractmethod
    def _transform_response(self, response: Any) -> CompletionResponse:
        """Transform provider response to Nimbus format.
        
        This method handles ALL provider-specific transformations:
        - Message extraction
        - Tool call extraction and conversion
        - Usage information extraction
        - Metadata extraction
        """
        pass
    
    def _transform_messages(self, messages: list[NimbusMessage]) -> list[dict[str, Any]]:
        """Transform Nimbus messages to provider-specific format.
        
        Override this method to implement provider-specific message transformation.
        """
        raise NotImplementedError
    
    def _transform_capabilities(self, capabilities: list[CapabilityInterface]) -> list[dict[str, Any]]:
        """Transform Nimbus capabilities to provider-specific format.
        
        Override this method to implement provider-specific capability transformation.
        """
        raise NotImplementedError
    
    def _extract_tool_calls(self, response: Any) -> list[CapabilityCall] | None:
        """Extract tool calls from provider response.
        
        Override this method to implement provider-specific tool call extraction.
        """
        return None
```

**Refactored MessageTransformer**:
```python
class MessageTransformer:
    """Thin delegation layer for message transformations.
    
    This class no longer contains provider-specific logic.
    It delegates to provider client methods.
    """
    
    @staticmethod
    def transform_for_provider(
        messages: list[NimbusMessage],
        provider: BaseModelProvider
    ) -> list[dict[str, Any]]:
        """Delegate message transformation to provider."""
        return provider._transform_messages(messages)
```

**Refactored CapabilityTransformer**:
```python
class CapabilityTransformer:
    """Thin delegation layer for capability transformations.
    
    This class no longer contains provider-specific logic.
    It delegates to provider client methods.
    """
    
    @staticmethod
    def transform_for_provider(
        capabilities: list[CapabilityInterface],
        provider: BaseModelProvider
    ) -> list[dict[str, Any]]:
        """Delegate capability transformation to provider."""
        return provider._transform_capabilities(capabilities)
```

**Migration Path**:
1. Add transformation methods to BaseModelProvider
2. Move provider-specific logic from transformers to provider clients
3. Update provider clients to implement all transformation methods
4. Update transformers to delegate to provider clients
5. Remove provider-specific methods from transformers
6. Update all call sites to use new delegation pattern

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Environment Variable Substitution Consistency

*For any* configuration string containing ${VAR_NAME} pattern, when the environment variable exists, substitution should replace the pattern with the variable value, and when it doesn't exist, it should raise a ConfigurationError.

**Validates: Requirements 2.2, 6.1**

### Property 2: YAML Configuration Round-Trip

*For any* valid RouterConfig, serializing to YAML and then loading back should produce an equivalent configuration (excluding environment variable substitution).

**Validates: Requirements 2.1**

### Property 3: Terminology Consistency

*For any* public API in the capabilities module, references to tool functionality should use "Capability" terminology, not "Tool" terminology.

**Validates: Requirements 1.1, 1.2**

### Property 4: Complete Terminology Migration

*For any* public API or internal code, there should be zero references to "Tool" terminology in capability-related code.

**Validates: Requirements 1.5**

### Property 5: Test Organization

*For any* test file, it should be located in the appropriate directory (unit/, integration/, or stress/) based on its testing scope.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 6: Example Completeness

*For any* major feature category (capabilities, routing, providers), there should exist at least one working example demonstrating its usage.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 7: Configuration Validation

*For any* invalid YAML configuration (missing required fields, invalid types), loading should raise a clear ConfigurationError with specific details about what is invalid.

**Validates: Requirements 2.4**

### Property 8: Concurrent Request Handling

*For any* router under concurrent load, it should correctly track active requests and rate limits without race conditions.

**Validates: Requirements 7.1**

### Property 9: Provider Transformation Encapsulation

*For any* provider client class, all provider-specific transformation logic should be contained within that class and not leak into core library code.

**Validates: Requirements 9.1, 9.5**

### Property 10: Core Library Provider Agnosticism

*For any* core library module (router, capabilities, completion models), it should only reference Nimbus-native models and never provider-specific formats.

**Validates: Requirements 9.4, 9.6, 9.7, 9.8**

### Property 11: Transformer Delegation

*For any* transformation operation, the transformer should delegate to the appropriate provider client method rather than implementing provider-specific logic.

**Validates: Requirements 9.2, 9.3**

## Error Handling

### Configuration Errors

```python
class ConfigurationError(NimbusError):
    """Raised when configuration is invalid."""
    
    def __init__(
        self,
        message: str,
        config_path: str | None = None,
        field_name: str | None = None,
        **kwargs
    ):
        super().__init__(message, {
            "config_path": config_path,
            "field_name": field_name,
            **kwargs
        })
```

**Error Scenarios**:
1. Missing environment variable: "Environment variable '${VAR}' not found"
2. Invalid YAML syntax: "Failed to parse YAML: {error}"
3. Invalid configuration: "Invalid router configuration: {details}"
4. Missing required field: "Required field '{field}' missing in configuration"

### Deprecation Warnings

```python
import warnings

def _deprecated_alias(old_name: str, new_name: str):
    """Issue deprecation warning for renamed classes."""
    warnings.warn(
        f"{old_name} is deprecated, use {new_name} instead",
        DeprecationWarning,
        stacklevel=2
    )
```

## Testing Strategy

### Unit Tests

**Coverage Goals**:
- Configuration loading: 90%+
- Environment variable substitution: 95%+
- Router selection logic: 90%+
- Capability models: 85%+

**Key Test Files**:
- `tests/unit/test_config_loader.py`: YAML loading and env var substitution
- `tests/unit/routes/test_router_config.py`: Router configuration validation
- `tests/unit/capabilities/test_capability_models.py`: Renamed model tests
- `tests/unit/capabilities/test_capability_call_handler.py`: Handler tests

### Integration Tests

**Scenarios**:
1. End-to-end router configuration from YAML
2. Multi-provider routing with fallbacks
3. Capability execution across different providers
4. Rate limiting with concurrent requests

**Key Test Files**:
- `tests/integration/routes/test_yaml_routing.py`
- `tests/integration/capabilities/test_end_to_end.py`
- `tests/integration/providers/test_multi_provider.py`

### Stress Tests

**Scenarios**:
1. Concurrent routing (100+ simultaneous requests)
2. Rate limit enforcement under load
3. Failover behavior under high error rates
4. Capability execution with high concurrency

**Key Test Files**:
- `tests/stress/test_concurrent_routing.py`
- `tests/stress/test_rate_limiting.py`
- `tests/stress/test_capability_load.py`

**Metrics to Track**:
- Requests per second
- Average latency
- P95/P99 latency
- Error rate
- Memory usage

### Property-Based Tests

Use `hypothesis` for property-based testing:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1))
def test_env_var_substitution_idempotent(var_name: str):
    """Substituting twice should equal substituting once."""
    # Property test for env var substitution
```

## Migration Guide

### For Users

**Breaking Changes**: All "Tool" terminology has been removed. You must update your code.

**Step 1**: Update all imports:
```python
# Old (will not work)
from nimbus.capabilities import ToolCall, ToolResult, ToolCallHandler

# New (required)
from nimbus.capabilities import CapabilityCall, CapabilityResult, CapabilityCallHandler
```

**Step 2**: Update all variable names and references:
```python
# Old
tool_call = ToolCall(id="1", name="get_weather", arguments={})
tool_result = ToolResult(tool_call_id="1", name="get_weather", result={})

# New
capability_call = CapabilityCall(id="1", name="get_weather", arguments={})
capability_result = CapabilityResult(capability_call_id="1", name="get_weather", result={})
```

**Step 3**: Use YAML configuration (optional but recommended):
```python
# Programmatic (still works)
router = ModelRouter(routes=[...])

# YAML (recommended for complex configs)
router = ModelRouter.from_yaml("router_config.yaml")
```

**Step 4**: Use environment variables in config:
```python
# In YAML
api_key: "${OPENAI_API_KEY}"

# Or in Python
target = ModelTarget(
    model="gpt-4",
    provider="openai",
    api_key="${OPENAI_API_KEY}"  # Will be substituted
)
```

### For Contributors

**Step 1**: Follow new test organization:
- Unit tests → `tests/unit/`
- Integration tests → `tests/integration/`
- Stress tests → `tests/stress/`

**Step 2**: Use "Capability" terminology exclusively:
- Never use "Tool" in new code
- Update any remaining "Tool" references to "Capability"

**Step 3**: Run full test suite:
```bash
pytest tests/
```

## Implementation Notes

### Phase 1: Terminology Consolidation
1. Rename files (tool_* → capability_*)
2. Rename classes (Tool* → Capability*)
3. Add backward compatibility aliases
4. Update all internal references
5. Update documentation

### Phase 2: Configuration Enhancement
1. Implement environment variable substitution
2. Add YAML loading support
3. Create RouterConfig model
4. Add validation and error handling
5. Write comprehensive tests

### Phase 3: Test Reorganization
1. Create new test directory structure
2. Move existing tests to appropriate locations
3. Add stress tests
4. Improve test fixtures
5. Update test documentation

### Phase 4: Example Reorganization
1. Create new example directory structure
2. Move and categorize existing examples
3. Add missing examples (YAML config, etc.)
4. Write README files for each category
5. Ensure all examples work

### Phase 5: Documentation Updates
1. Update steering documents
2. Update architecture diagrams
3. Update API documentation
4. Add migration guide
5. Update README

## Performance Considerations

### Environment Variable Substitution

- Cache substituted values to avoid repeated os.getenv() calls
- Perform substitution once during initialization, not per-request
- Use compiled regex for pattern matching

### YAML Loading

- Load and parse YAML once at startup
- Cache parsed configuration
- Validate configuration eagerly to fail fast

### Test Performance

- Use pytest-xdist for parallel test execution
- Mock external dependencies in unit tests
- Use fixtures to avoid repeated setup
- Profile slow tests and optimize

## Security Considerations

### Environment Variables

- Never log actual API key values
- Mask sensitive values in error messages
- Support .env files for local development
- Document secure practices for production

### YAML Configuration

- Validate all inputs from YAML files
- Sanitize file paths to prevent directory traversal
- Limit file size to prevent DoS
- Use safe YAML loading (yaml.safe_load)

## Breaking Changes

### Removed Names

All "Tool" terminology has been removed and replaced with "Capability":
- `ToolCall` → `CapabilityCall` (no alias)
- `ToolResult` → `CapabilityResult` (no alias)
- `ToolCallHandler` → `CapabilityCallHandler` (no alias)
- `ToolTransformer` → `CapabilityTransformer` (no alias)

### Migration Required

Users must update their code to use the new names:
```python
# Old (will not work)
from nimbus.capabilities import ToolCall  # ImportError

# New (required)
from nimbus.capabilities import CapabilityCall
```

This is a breaking change requiring a major version bump.

## Documentation Updates

### Steering Documents

Update `.kiro/steering/nimbus-architecture.md`:
- Reflect current package structure
- Add YAML configuration examples
- Update naming conventions section
- Add environment variable guidelines

### API Documentation

- Update all docstrings to use "Capability" terminology
- Add examples of YAML configuration
- Document environment variable substitution
- Add migration guide

### README

- Update quick start examples
- Add YAML configuration example
- Update feature list
- Add link to migration guide
