#!/bin/bash
# Type hints verification script for provider code
# Run with: bash tests/test_provider_type_hints.sh

set -e

echo "🔍 Checking type hints for provider code..."
echo "=============================================="

# Run mypy with strict mode
echo ""
echo "Running mypy with --strict mode..."
uv run mypy src/nimbus/models --strict

echo ""
echo "✅ Type hints verification passed!"
echo ""
echo "Summary:"
echo "  • All provider code has complete type hints"
echo "  • No implicit Any types"
echo "  • All functions have return type annotations"
echo "  • All parameters have type annotations"
