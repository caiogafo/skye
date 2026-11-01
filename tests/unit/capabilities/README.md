# Capability Unit Tests

Unit tests for the Nimbus capability system.

## Test Coverage

This directory contains tests for:
- **Capability models** - `CapabilityCall`, `CapabilityResult`, `CapabilityInterface`
- **Capability registry** - Registration, lookup, and management
- **Capability call handler** - Execution and error handling
- **Capability transformer** - Transformation delegation to providers
- **Capability decorators** - `@capability` decorator functionality

## Test Files

- `test_capability_models.py` - Tests for capability data models
- `test_capability_registry.py` - Tests for capability registration and lookup
- `test_capability_call_handler.py` - Tests for capability execution
- `test_capability_transformer.py` - Tests for capability transformation

## Running Tests

```bash
# Run all capability tests
pytest tests/unit/capabilities/

# Run specific test file
pytest tests/unit/capabilities/test_capability_models.py

# Run with coverage
pytest tests/unit/capabilities/ --cov=src/nimbus/tools
```
