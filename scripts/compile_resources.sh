#!/usr/bin/env bash
# Compile Qt resources for QGIS 3 (Qt5) and QGIS 4 (Qt6).
# Tries pyrcc5 first (QGIS 3), then pyrcc6 (QGIS 4), then PyQt5 module as fallback.
# After compilation, rewrites the PyQt5/Qt6 import to use the
# version-independent qgis.PyQt wrapper.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PLUGIN_DIR"

if command -v pyrcc5 &>/dev/null; then
    echo "Using pyrcc5..."
    pyrcc5 src/resources.qrc -o src/resources.py
elif command -v pyrcc6 &>/dev/null; then
    echo "Using pyrcc6..."
    pyrcc6 src/resources.qrc -o src/resources.py
else
    echo "Using PyQt5.pyrcc_main..."
    python3 -m PyQt5.pyrcc_main src/resources.qrc -o src/resources.py
fi

# Replace PyQt5/PyQt6 imports with version-independent qgis.PyQt wrapper
# so the file works on both QGIS 3 (Qt5) and QGIS 4 (Qt6).
# Also strip the unnecessary UTF-8 coding comment added by pyrcc.
python3 scripts/post_process_resources.py src/resources.py

echo "DONE"
