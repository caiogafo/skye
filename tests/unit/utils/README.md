# Utility Unit Tests

Unit tests for Skye utility functions.

## Test Coverage

This directory contains tests for:
- **Token counting** - Token calculation for different models
- **Cost calculation** - Cost estimation based on token usage
- **Image handling** - Image encoding and processing
- **Validation utilities** - Input validation helpers
- **Lazy imports** - Lazy loading of optional dependencies

## Test Files

- `test_token_counter.py` - Tests for token counting utilities
- `test_cost_calculator.py` - Tests for cost calculation
- `test_image_handler.py` - Tests for image processing
- `test_validation.py` - Tests for validation utilities
- `test_lazy_import.py` - Tests for lazy import mechanism

## Running Tests

```bash
# Run all utility tests
pytest tests/unit/utils/

# Run specific test file
pytest tests/unit/utils/test_token_counter.py

# Run with coverage
pytest tests/unit/utils/ --cov=src/skye/utils
```

## Testing Approach

Utility tests should:
- Test edge cases thoroughly
- Verify correct calculations
- Test error handling
- Ensure utilities are stateless and pure when possible
