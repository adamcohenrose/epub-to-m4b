#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

APP_NAME="ePubToM4b"
SCRIPT_NAME="EpubToM4bApp.py"

echo "Preparing environment..."
brew install tcl-tk
env \
  PATH="$(brew --prefix tcl-tk)/bin:$PATH" \
  LDFLAGS="-L$(brew --prefix tcl-tk)/lib" \
  CPPFLAGS="-I$(brew --prefix tcl-tk)/include" \
  PKG_CONFIG_PATH="$(brew --prefix tcl-tk)/lib/pkgconfig" \
  PYTHON_CONFIGURE_OPTS="--with-tcltk-includes='-I$(brew --prefix tcl-tk)/include' --with-tcltk-libs='-L$(brew --prefix tcl-tk)/lib -ltcl8.6 -ltk8.6'" \
  MACOSX_DEPLOYMENT_TARGET=15.0 \
  pyenv install 3.13.11
pyenv virtualenv 3.13.11 3.13.11-epub2audiobk
pyenv local 3.13.11-epub2audiobk

echo "🧱 Building $APP_NAME..."
pip install ".[build]"

echo "🧹 Cleaning up previous builds..."
rm -rf build/ dist/ "$APP_NAME.spec"

echo "📦 Packaging $APP_NAME with PyInstaller..."
pyinstaller --windowed --noconfirm --add-binary "ffmpeg:." --name "$APP_NAME" "$SCRIPT_NAME"

echo "✅ Build complete!"

# Automatically open the folder containing the finished .app
open dist/