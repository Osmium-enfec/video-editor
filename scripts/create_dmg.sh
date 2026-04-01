#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/create_dmg.sh /path/to/YourApp.app "Volume Name" output.dmg "Developer ID Application: Your Name (TEAMID)"

APP_PATH="$1"
VOL_NAME="${2:-VideoEditor}"
OUT_DMG="${3:-VideoEditor.dmg}"
IDENTITY="${4:-}"

if [ ! -d "$APP_PATH" ]; then
  echo "App bundle not found: $APP_PATH"
  exit 1
fi

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Copying app to temporary folder..."
cp -R "$APP_PATH" "$TMP_DIR/"

APP_NAME=$(basename "$APP_PATH")
TMP_APP="$TMP_DIR/$APP_NAME"

if [ -n "$IDENTITY" ]; then
  echo "Codesigning $TMP_APP with identity: $IDENTITY"
  codesign --deep --force --options runtime --sign "$IDENTITY" "$TMP_APP"
fi

echo "Creating DMG $OUT_DMG (volume name: $VOL_NAME)..."
hdiutil create -srcfolder "$TMP_DIR" -volname "$VOL_NAME" -format UDZO -ov "$OUT_DMG"

echo "DMG created: $OUT_DMG"
