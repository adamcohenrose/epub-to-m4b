#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

APP_NAME="ePubToM4b"
SCRIPT_NAME="EpubToM4bApp.py"

echo "🧱 Building $APP_NAME..."
pip install .

echo "🧹 Cleaning up previous builds..."
rm -rf build/ dist/ "$APP_NAME.spec"

echo "📦 Packaging $APP_NAME with PyInstaller..."
pyinstaller --windowed --noconfirm --add-binary "ffmpeg:." --name "$APP_NAME" "$SCRIPT_NAME"

echo "✅ Build complete!"

# Automatically open the folder containing the finished .app
open dist/