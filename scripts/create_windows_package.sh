#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/create_windows_package.sh /path/to/dist/folder

DIST_DIR="${1:-dist}"

if [ ! -d "$DIST_DIR" ]; then
  echo "Dist folder not found: $DIST_DIR"
  exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TP_FFMPEG="$SCRIPT_DIR/../third_party/ffmpeg/windows"

if [ -d "$TP_FFMPEG" ]; then
  echo "Copying ffmpeg files into distribution..."
  # Copy all ffmpeg*.exe into the dist root (next to your exe)
  find "$TP_FFMPEG" -type f -name "ffmpeg*.exe" -exec cp {} "$DIST_DIR/" \; || true
fi

echo "Windows packaging helper completed. Verify ffmpeg presence in $DIST_DIR"
