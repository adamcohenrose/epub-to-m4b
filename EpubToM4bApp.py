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
import re


class EpubToM4bApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB to M4B Converter")
        self.root.geometry("600x250")  # Slightly wider for macOS padding

        self.epub_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.voice = tk.StringVar(value="en-GB-LibbyNeural")

        self.setup_ui()

    def setup_ui(self):
        # --- EPUB Selection ---
        tk.Label(self.root, text="EPUB File:").grid(
            row=0, column=0, padx=10, pady=15, sticky="e"
        )

        # Read-only entry so it displays the path but can't be typed in
        self.epub_entry = ttk.Entry(
            self.root, textvariable=self.epub_path, width=38, state="readonly"
        )
        self.epub_entry.grid(row=0, column=1, padx=5)
        # Bind left-click on the text box to open the dialog
        self.epub_entry.bind("<Button-1>", lambda e: self.browse_epub())

        tk.Button(self.root, text="Choose...", command=self.browse_epub).grid(
            row=0, column=2, padx=10
        )

        # --- Output Selection ---
        tk.Label(self.root, text="Save M4B As:").grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )

        self.out_entry = ttk.Entry(
            self.root, textvariable=self.output_path, width=38, state="readonly"
        )
        self.out_entry.grid(row=1, column=1, padx=5)
        self.out_entry.bind("<Button-1>", lambda e: self.browse_output())

        tk.Button(self.root, text="Choose...", command=self.browse_output).grid(
            row=1, column=2, padx=10
        )

        # --- Voice Selection ---
        tk.Label(self.root, text="TTS Voice:").grid(
            row=2, column=0, padx=10, pady=15, sticky="e"
        )
        voices = [
            "en-GB-LibbyNeural",
            "en-GB-MaisieNeural",
            "en-GB-RyanNeural",
            "en-GB-SoniaNeural",
            "en-GB-ThomasNeural",
        ]
        ttk.Combobox(
            self.root,
            textvariable=self.voice,
            values=voices,
            width=36,
            state="readonly",
        ).grid(row=2, column=1, padx=5, sticky="w")

        # --- Convert Button & Progress ---
        self.convert_btn = tk.Button(
            self.root,
            text="Convert to M4B",
            command=self.start_conversion,
            bg="#007AFF",
            fg="white",
        )
        self.convert_btn.grid(row=3, column=1, pady=15)

        self.status_label = tk.Label(self.root, text="Ready", fg="gray")
        self.status_label.grid(row=4, column=0, columnspan=3)

    def browse_epub(self):
        filename = filedialog.askopenfilename(
            title="Select EPUB Book", filetypes=[("EPUB Files", "*.epub")]
        )
        if filename:
            self.epub_path.set(filename)
            # Auto-fill output path so the user doesn't have to click twice unless they want to change it
            out_name = os.path.splitext(filename)[0] + ".m4b"
            self.output_path.set(out_name)

    def browse_output(self):
        # If an epub is already selected, suggest saving in the same directory
        initial_dir = (
            os.path.dirname(self.epub_path.get()) if self.epub_path.get() else "/"
        )
        initial_file = (
            os.path.basename(self.output_path.get())
            if self.output_path.get()
            else "audiobook.m4b"
        )

        filename = filedialog.asksaveasfilename(
            title="Save Audiobook As",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".m4b",
            filetypes=[("Audiobook", "*.m4b")],
        )
        if filename:
            self.output_path.set(filename)

    def start_conversion(self):
        if not self.epub_path.get() or not self.output_path.get():
            messagebox.showerror(
                "Missing Information",
                "Please select an EPUB file and choose a save location.",
            )
            return

        self.convert_btn.config(state="disabled")
        self.status_label.config(text="Parsing EPUB...", fg="black")

        threading.Thread(target=self.process_book, daemon=True).start()

    def parse_chapter_content(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")

        for element in soup(
            ["script", "style", "math", "figure", "nav", "aside", "head", "table"]
        ):
            element.extract()

        text_blocks = []
        for element in soup.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "div"]
        ):
            text = element.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            if text and len(text) > 1 and text not in text_blocks:
                text_blocks.append(text)

        if not text_blocks:
            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            if text:
                text_blocks.append(text)

        return ".\n\n".join(text_blocks)

    def process_book(self):
        temp_dir = tempfile.mkdtemp()
        try:
            book = epub.read_epub(self.epub_path.get(), {"ignore_ncx": True})

            title_meta = book.get_metadata("DC", "title")
            author_meta = book.get_metadata("DC", "creator")

            title = title_meta[0][0] if title_meta else "Unknown Title"
            author = author_meta[0][0] if author_meta else "Unknown Author"

            chapters = []
            spine_ids = [item[0] for item in book.spine]

            for item_id in spine_ids:
                item = book.get_item_with_id(item_id)
                if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                    parsed_text = self.parse_chapter_content(item.get_body_content())
                    if len(parsed_text) > 100:
                        chap_title = (
                            item.get_name()
                            .split("/")[-1]
                            .split(".")[0]
                            .replace("_", " ")
                            .title()
                        )
                        chapters.append({"title": chap_title, "text": parsed_text})

            if not chapters:
                raise ValueError("Could not extract any readable text from this EPUB.")

            asyncio.run(self.generate_audio(chapters, temp_dir))

            self.status_label.config(text="Packaging M4B (This may take a minute)...")
            self.create_m4b(chapters, temp_dir, title, author)

            self.status_label.config(text="Success! Audiobook created.", fg="green")
            messagebox.showinfo(
                "Done", f"Audiobook successfully saved to:\n{self.output_path.get()}"
            )

        except Exception as e:
            self.status_label.config(text="Error occurred during conversion.", fg="red")
            messagebox.showerror("Conversion Error", str(e))
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

            audio = MP3(audio_path)
            chapter["duration_ms"] = int(audio.info.length * 1000)

    def create_m4b(self, chapters, temp_dir, title, author):
        concat_file = os.path.join(temp_dir, "concat.txt")
        meta_file = os.path.join(temp_dir, "metadata.txt")

        with open(concat_file, "w") as f:
            for chap in chapters:
                safe_path = chap["audio_path"].replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

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
                f.write(f"title={chap['title']}\n\n")

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
            "96k",
            "-vn",
            output_file,
        ]

        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = EpubToM4bApp(root)
    root.mainloop()
