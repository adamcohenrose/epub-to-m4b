# epub2m4b

A macOS application designed to convert EPUB eBooks directly into M4B audiobooks with chapters using Microsoft Edge's Text-to-Speech (TTS) engine.

This project was constructed by **Google Gemini** based on https://github.com/p0n1/epub_to_audiobook and https://github.com/DrewThomasson/ebook2audiobook

## Features
* **EPUB Parsing**: Automatically extracts text and chapter structures from EPUB files.
* **High-Quality TTS**: Uses `edge-tts` for natural-sounding speech generation.
* **M4B with Metadata**: Packages audio into M4B files including title, author, and chapter markers.
* **Simple GUI**: A user-friendly macOS interface built with Tkinter.

## Prerequisites for Build
* **Homebrew**: Required to install system dependencies like Tcl-Tk.
* **pyenv & pyenv-virtualenv**: Used for managing the specific Python version and environment.
* **ffmpeg**: The app utilizes `ffmpeg` to handle audio packaging; ensure it is accessible in your environment.

## Setup and Installation

### 1. Prepare the Build Environment
The project includes a helper script, `build-install.sh`, to automate the environment setup on macOS. This script installs Tcl-Tk via Homebrew and configures a specific Python 3.13.11 virtual environment.

Run the following command in your terminal:
```bash
./build-install.sh
```

### 2. Build the macOS Application

Once the environment is prepared, you can use `build-mac-app.sh` to package the script into a standalone `.app` file using PyInstaller.

Run the build script:

```bash
./build-mac-app.sh
```

Upon completion, the `dist/` folder will open automatically, containing **ePubToM4b.app**.

## Usage
1.  Launch the application.
2.  **EPUB File**: Click "Choose..." to select your eBook.
3.  **Save M4B As**: Select the destination for your audiobook.
4.  **TTS Voice**: Choose a preferred voice from the dropdown (e.g., `en-GB-LibbyNeural`).
5.  **Convert**: Click "Convert to M4B" to start the process. The status bar will track progress from parsing to packaging.

## Dependencies
The project relies on several key Python libraries:
* `ebooklib`: For EPUB reading.
* `beautifulsoup4`: For HTML parsing and text cleaning.
* `edge-tts`: For Microsoft Edge TTS integration.
* `mutagen`: For handling audio metadata.
* `pyinstaller`: For application packaging.