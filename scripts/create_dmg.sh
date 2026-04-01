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

# If we have prebuilt ffmpeg binaries in third_party/ffmpeg/macos, copy them
# into the app bundle so offline installers include ffmpeg.
FFMPEG_THIRD_PARTY="$(pwd)/third_party/ffmpeg/macos"
if [ -d "$FFMPEG_THIRD_PARTY" ]; then
  echo "Including bundled ffmpeg files from $FFMPEG_THIRD_PARTY into app bundle..."
  RES_DIR="$TMP_APP/Contents/Resources/ffmpeg"
  mkdir -p "$RES_DIR"
  cp -R "$FFMPEG_THIRD_PARTY"/* "$RES_DIR/" || true
  # Make any binaries executable
  find "$RES_DIR" -type f -name "ffmpeg*" -exec chmod +x {} + || true
fi

if [ -n "$IDENTITY" ]; then
  echo "Codesigning $TMP_APP with identity: $IDENTITY"
  codesign --deep --force --options runtime --sign "$IDENTITY" "$TMP_APP"
fi

echo "Creating DMG $OUT_DMG (volume name: $VOL_NAME)..."
hdiutil create -srcfolder "$TMP_DIR" -volname "$VOL_NAME" -format UDZO -ov "$OUT_DMG"

echo "DMG created: $OUT_DMG"
