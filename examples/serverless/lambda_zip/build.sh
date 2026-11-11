#!/usr/bin/env sh
# Build function.zip: Skye (from PyPI, or the wheel given as $1) plus handler.py, nothing else.
# Usage: sh build.sh [path/to/skyeai-*.whl]
set -eu
cd "$(dirname "$0")"
rm -rf build function.zip
"${PYTHON:-python3}" -m pip install --quiet --disable-pip-version-check --target build "${1:-skyeai}"
rm -rf build/*.dist-info
find build -name __pycache__ -prune -exec rm -rf {} +
cp handler.py build/
(cd build && zip -qr9 ../function.zip .)
"${PYTHON:-python3}" -c "import os; print(f'function.zip: {os.path.getsize(\"function.zip\") / 1e6:.2f} MB')"
