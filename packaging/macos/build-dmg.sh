#!/usr/bin/env sh
set -eu

APP_PATH="dist/Quack2Tex.app"
DMG_PATH="dist/Quack2Tex.dmg"

if [ ! -d "$APP_PATH" ]; then
  echo "Missing $APP_PATH. Run make mac-app first." >&2
  exit 1
fi

if ! command -v create-dmg >/dev/null 2>&1; then
  echo "create-dmg is required. Install it with: brew install create-dmg" >&2
  exit 1
fi

rm -f "$DMG_PATH"

create-dmg \
  --volname "Quack2Tex" \
  --window-pos 200 120 \
  --window-size 640 420 \
  --icon-size 96 \
  --icon "Quack2Tex.app" 180 170 \
  --app-drop-link 460 170 \
  "$DMG_PATH" \
  "$APP_PATH"
