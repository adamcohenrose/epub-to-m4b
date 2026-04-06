#!/bin/bash

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
