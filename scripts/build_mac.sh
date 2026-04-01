#!/usr/bin/env bash
set -e
# Usage: ./scripts/build_mac.sh [--cython]
# Optional: pass --cython to compile selected modules with Cython first.

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "Installing build dependencies (pyinstaller, cython)..."
python3 -m pip install -r requirements-build.txt

if [ "$1" = "--cython" ]; then
  echo "Compiling selected modules with Cython..."
  python3 setup_cython.py build_ext --inplace
fi

echo "Running PyInstaller..."
python3 -m PyInstaller --noconfirm --onefile --windowed --name "VideoEditor" \
  --add-data "ffedit/config/presets.json:ffedit/config" \
  ffedit/app.py

echo "Build complete. See the standalone binary in dist/VideoEditor"
