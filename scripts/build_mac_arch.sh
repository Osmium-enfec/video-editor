#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/build_mac_arch.sh arm64|x86_64 [--cython]

ARCH=${1:-arm64}
shift || true
DO_CYTHON=false
if [ "$1" = "--cython" ]; then
  DO_CYTHON=true
fi

if [ "$ARCH" = "x86_64" ]; then
  echo "Building for x86_64 (Intel)"
  if command -v arch >/dev/null 2>&1; then
    echo "Running under Rosetta (arch -x86_64)..."
    arch -x86_64 /usr/bin/env bash -c "./scripts/build_mac.sh ${DO_CYTHON:+--cython}"
  else
    echo "Rosetta not available — you must run this on an Intel mac or enable Rosetta Python." >&2
    exit 1
  fi
elif [ "$ARCH" = "arm64" ]; then
  echo "Building for arm64 (Apple Silicon)"
  ./scripts/build_mac.sh ${DO_CYTHON:+--cython}
else
  echo "Unknown arch: $ARCH" >&2
  exit 2
fi
