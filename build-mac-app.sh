#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

APP_NAME="ePubToM4b"
SCRIPT_NAME="EpubToM4bApp.py"
ICON_NAME="app_icon.icns"

echo "🧱 Building $APP_NAME..."
export ARCHFLAGS="-arch x86_64 -arch arm64"
pip install --upgrade pip
pip install --no-binary yarl,multidict,frozenlist,propcache,aiohttp ".[build]"

echo "🧹 Cleaning up previous builds..."
rm -rf build/ dist/ "$APP_NAME.spec"

echo "📦 Packaging $APP_NAME with PyInstaller..."
pyinstaller --windowed --noconfirm --target-architecture universal2 --icon="$ICON_NAME" --name "$APP_NAME" "$SCRIPT_NAME"

echo "✅ Build complete!"

# Automatically open the folder containing the finished .app
open dist/