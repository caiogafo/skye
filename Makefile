.PHONY: help install install-dev clean format lint type-check type-check-providers test test-unit test-integration test-cov test-providers test-capabilities check all

# Default target
help:
	@echo "Nimbus Development Commands"
	@echo "============================"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install base dependencies"
	@echo "  make install-dev      Install with dev dependencies"
	@echo "  make install-all      Install with all extras"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black"
	@echo "  make lint             Lint code with ruff"
	@echo "  make type-check       Type check with mypy"
	@echo "  make type-check-providers  Type check providers only"
	@echo "  make check            Run all checks (format, lint, type-check)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-providers   Run provider unit tests only"
	@echo "  make test-capabilities Run capability unit tests only"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Remove build artifacts and cache"
	@echo "  make all              Run format, check, and test"
	@echo ""

# Installation targets
install:
	uv sync

install-dev:
	uv sync --group dev

install-all:
	uv sync --all-extras --group dev

# Code formatting
format:
	@echo "Formatting code with black..."
	uv run black src/ tests/
	@echo "✓ Formatting complete"

# Linting
lint:
	@echo "Linting code with ruff..."
	uv run ruff check src/ tests/
	@echo "✓ Linting complete"

# Type checking
type-check:
	@echo "Type checking with mypy..."
	uv run mypy src/nimbus --strict
	@echo "✓ Type checking complete"

# Type checking for providers specifically
type-check-providers:
	@echo "Type checking providers with mypy..."
	uv run mypy src/nimbus/providers --strict
	@echo "✓ Provider type checking complete"

# Run all checks (for task completion validation)
check: format lint type-check
	@echo ""
	@echo "================================"
	@echo "✓ All checks passed successfully"
	@echo "================================"

# Testing targets
test:
	@echo "Running all tests..."
	uv run pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	uv run pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/integration/ -v

test-providers:
	@echo "Running provider unit tests..."
	uv run pytest tests/unit/providers/ -v

test-capabilities:
	@echo "Running capability unit tests..."
	uv run pytest tests/unit/capabilities/ -v

test-cov:
	@echo "Running tests with coverage..."
	uv run pytest tests/ --cov=src/nimbus --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Clean complete"

# Run everything (format, check, test)
all: format check test
	@echo ""
	@echo "========================================"
	@echo "✓ All tasks completed successfully!"
	@echo "========================================"
