---
title: "Development"
status: current
last_updated: 2026-11-02
---

# Development

## Setup

```bash
# Clone repository
git clone https://github.com/your-org/skye.git
cd skye

# Install with dev dependencies
uv pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/skye --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_completion.py -v
```

## Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type check
uv run mypy src/skye --strict

# Run all checks
make check
```
