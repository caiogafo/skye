#!/bin/bash
# Type hints verification script
# This script runs mypy with strict mode and fails if any errors are found

set -e

echo "Running mypy type checking with strict mode..."
echo "=============================================="

# Run mypy with strict mode
uv run mypy src/nimbus --strict

# If we get here, no errors were found
echo ""
echo "✓ Type checking passed - all type hints are valid"
exit 0
