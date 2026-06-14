#!/bin/bash
set -e

echo "=== Building Tetris.app ==="

# Clean previous builds
rm -rf build dist

# Build with py2app in alias mode
echo "Running py2app (alias mode)..."
python3 setup.py py2app -A

# Copy to Desktop
echo "Copying to Desktop..."
cp -r dist/Tetris.app ~/Desktop/

echo ""
echo "=== Build complete! ==="
echo "Tetris.app has been copied to ~/Desktop/"
echo "Double-click to play, or run: open ~/Desktop/Tetris.app"
