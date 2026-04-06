import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import asyncio
import subprocess
import os
import tempfile
import shutil
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import edge_tts
from mutagen.mp3 import MP3


class EpubToM4bApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB to M4B Converter")
        self.root.geometry("500x250")

        self.epub_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.voice = tk.StringVar(value="en-US-AriaNeural")  # Default voice

        self.setup_ui()

    def setup_ui(self):
        # EPUB Selection
        tk.Label(self.root, text="Select EPUB:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        tk.Entry(self.root, textvariable=self.epub_path, width=40).grid(
            row=0, column=1, padx=10
        )
        tk.Button(self.root, text="Browse", command=self.browse_epub).grid(
            row=0, column=2, padx=10
        )

        # Output Selection
        tk.Label(self.root, text="Save M4B As:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        tk.Entry(self.root, textvariable=self.output_path, width=40).grid(
            row=1, column=1, padx=10
        )
        tk.Button(self.root, text="Browse", command=self.browse_output).grid(
            row=1, column=2, padx=10
        )

        # Voice Selection
        tk.Label(self.root, text="TTS Voice:").grid(
            row=2, column=0, padx=10, pady=10, sticky="w"
        )
        voices = [
            "en-GB-LibbyNeural",
            "en-GB-MaisieNeural",
            "en-GB-RyanNeural",
            "en-GB-SoniaNeural",
            "en-GB-ThomasNeural",
        ]
        ttk.Combobox(self.root, textvariable=self.voice, values=voices, width=37).grid(
            row=2, column=1, padx=10, sticky="w"
        )

        # Convert Button & Progress
        self.convert_btn = tk.Button(
            self.root,
            text="Convert to M4B",
            command=self.start_conversion,
            bg="#007AFF",
            fg="white",
        )
        self.convert_btn.grid(row=3, column=1, pady=20)

        self.status_label = tk.Label(self.root, text="Ready", fg="gray")
        self.status_label.grid(row=4, column=0, columnspan=3)

    def browse_epub(self):
        filename = filedialog.askopenfilename(filetypes=[("EPUB Files", "*.epub")])
        if filename:
            self.epub_path.set(filename)
            # Auto-fill output path
            out_name = os.path.splitext(filename)[0] + ".m4b"
            self.output_path.set(out_name)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".m4b", filetypes=[("Audiobook", "*.m4b")]
        )
        if filename:
            self.output_path.set(filename)

    def start_conversion(self):
        if not self.epub_path.get() or not self.output_path.get():
            messagebox.showerror("Error", "Please select input and output files.")
            return

        self.convert_btn.config(state="disabled")
        self.status_label.config(text="Parsing EPUB...", fg="black")

        # Run in background thread to keep UI responsive
        threading.Thread(target=self.process_book, daemon=True).start()

    def process_book(self):
        temp_dir = tempfile.mkdtemp()
        try:
            book = epub.read_epub(self.epub_path.get())
            title = (
                book.get_metadata("DC", "title")[0][0]
                if book.get_metadata("DC", "title")
                else "Unknown Title"
            )
            author = (
                book.get_metadata("DC", "creator")[0][0]
                if book.get_metadata("DC", "creator")
                else "Unknown Author"
            )

            chapters = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_body_content(), "html.parser")
                    text = soup.get_text(separator=" ", strip=True)
                    if len(text) > 150:  # Skip empty/meaningless pages
                        chapters.append({"title": item.get_name(), "text": text})

            # Generate Audio
            asyncio.run(self.generate_audio(chapters, temp_dir))

            # Merge to M4B
            self.status_label.config(text="Packaging M4B (This may take a minute)...")
            self.create_m4b(chapters, temp_dir, title, author)

            self.status_label.config(text="Success! Audiobook created.", fg="green")
            messagebox.showinfo(
                "Done", f"Audiobook saved to:\n{self.output_path.get()}"
            )

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            messagebox.showerror("Error", str(e))
        finally:
            shutil.rmtree(temp_dir)
            self.convert_btn.config(state="normal")

    async def generate_audio(self, chapters, temp_dir):
        for i, chapter in enumerate(chapters):
            self.status_label.config(
                text=f"Generating Audio: Chapter {i + 1} of {len(chapters)}"
            )
            audio_path = os.path.join(temp_dir, f"chap_{i:04d}.mp3")
            communicate = edge_tts.Communicate(chapter["text"], self.voice.get())
            await communicate.save(audio_path)
            chapter["audio_path"] = audio_path

            # Calculate duration for metadata
            audio = MP3(audio_path)
            chapter["duration_ms"] = int(audio.info.length * 1000)

    def create_m4b(self, chapters, temp_dir, title, author):
        concat_file = os.path.join(temp_dir, "concat.txt")
        meta_file = os.path.join(temp_dir, "metadata.txt")

        # 1. Build Concat file for FFmpeg
        with open(concat_file, "w") as f:
            for chap in chapters:
                f.write(f"file '{chap['audio_path']}'\n")

        # 2. Build FFmpeg Metadata file (for Apple Books Chapters)
        with open(meta_file, "w", encoding="utf-8") as f:
            f.write(";FFMETADATA1\n")
            f.write(f"title={title}\n")
            f.write(f"artist={author}\n")
            f.write(f"album={title}\n\n")

            current_time = 0
            for i, chap in enumerate(chapters):
                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={current_time}\n")
                current_time += chap["duration_ms"]
                f.write(f"END={current_time}\n")
                f.write(f"title=Chapter {i + 1}\n\n")

        # 3. Run FFmpeg command to compile M4B
        output_file = self.output_path.get()
        if os.path.exists(output_file):
            os.remove(output_file)

        ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
        cmd = [
            ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-i",
            meta_file,
            "-map_metadata",
            "1",
            "-c:a",
            "aac",
            "-b:a",
            "96k",  # AAC is required for M4B
            "-vn",
            output_file,
        ]

        # Hide terminal window on macOS during subprocess
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = EpubToM4bApp(root)
    root.mainloop()
