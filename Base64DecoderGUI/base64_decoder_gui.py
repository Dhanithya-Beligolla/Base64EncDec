import base64
import binascii
import mimetypes
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "Base64 Decoder"
APP_VERSION = "1.0.0"

def clean_base64(value: str) -> tuple[str, str | None]:
    value = value.strip()
    mime_type = None

    data_url = re.match(r"^data:([^;,]+)?(?:;charset=[^;,]+)?;base64,(.*)$", value, re.I | re.S)
    if data_url:
        mime_type = data_url.group(1)
        value = data_url.group(2)

    value = re.sub(r"\s+", "", value)

    # Allow URL-safe Base64 too.
    value = value.replace("-", "+").replace("_", "/")

    # Restore missing padding where possible.
    missing = len(value) % 4
    if missing:
        value += "=" * (4 - missing)

    return value, mime_type

def decode_base64(value: str) -> tuple[bytes, str | None]:
    value, mime_type = clean_base64(value)
    if not value:
        raise ValueError("Please paste Base64 data first.")

    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(
            "The pasted value is not valid Base64.\n\n"
            "Tip: You can paste plain Base64 or a data URL such as "
            "'data:application/pdf;base64,...'."
        ) from exc

    return decoded, mime_type

def guess_extension(data: bytes, mime_type: str | None) -> str:
    signatures = [
        (b"%PDF-", ".pdf"),
        (b"\x89PNG\r\n\x1a\n", ".png"),
        (b"\xff\xd8\xff", ".jpg"),
        (b"GIF87a", ".gif"),
        (b"GIF89a", ".gif"),
        (b"PK\x03\x04", ".zip"),
        (b"Rar!\x1a\x07", ".rar"),
        (b"\x1f\x8b", ".gz"),
        (b"ID3", ".mp3"),
        (b"OggS", ".ogg"),
    ]
    for sig, ext in signatures:
        if data.startswith(sig):
            return ext

    if data.startswith(b"RIFF") and len(data) >= 12:
        if data[8:12] == b"WAVE":
            return ".wav"
        if data[8:12] == b"WEBP":
            return ".webp"
        if data[8:12] == b"AVI ":
            return ".avi"

    if len(data) >= 12 and data[4:8] == b"ftyp":
        return ".mp4"

    if mime_type:
        ext = mimetypes.guess_extension(mime_type)
        if ext:
            return ext

    return ".bin"

def bytes_to_text(data: bytes) -> tuple[str, str]:
    encodings = ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1"]
    for encoding in encodings:
        try:
            text = data.decode(encoding)
            if "\x00" not in text[:1000] or "utf-16" in encoding:
                return text, encoding
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace"), "utf-8 (replacement characters used)"

class Base64DecoderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry("980x720")
        self.minsize(780, 560)

        self.decoded_bytes: bytes | None = None
        self.mime_type: str | None = None

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")

        main = ttk.Frame(self, padding=14)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="Base64 Decoder", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w")
        ttk.Label(
            main,
            text="Paste Base64 data, preview decoded text, or save the decoded bytes as a file.",
        ).pack(anchor="w", pady=(0, 12))

        input_frame = ttk.LabelFrame(main, text="Base64 Input", padding=8)
        input_frame.pack(fill="both", expand=True)

        self.input_text = tk.Text(input_frame, wrap="word", height=14, undo=True)
        input_scroll = ttk.Scrollbar(input_frame, command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scroll.set)
        self.input_text.pack(side="left", fill="both", expand=True)
        input_scroll.pack(side="right", fill="y")

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=10)

        ttk.Button(buttons, text="Decode / Preview Text", command=self.preview_text).pack(side="left")
        ttk.Button(buttons, text="Decode & Save File", command=self.save_file).pack(side="left", padx=6)
        ttk.Button(buttons, text="Paste Clipboard", command=self.paste_clipboard).pack(side="left", padx=6)
        ttk.Button(buttons, text="Clear", command=self.clear_all).pack(side="left", padx=6)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(buttons, textvariable=self.status_var).pack(side="right")

        output_frame = ttk.LabelFrame(main, text="Decoded Text Preview", padding=8)
        output_frame.pack(fill="both", expand=True)

        self.output_text = tk.Text(output_frame, wrap="word", height=14, state="disabled")
        output_scroll = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scroll.set)
        self.output_text.pack(side="left", fill="both", expand=True)
        output_scroll.pack(side="right", fill="y")

        footer = ttk.Label(
            main,
            text="Supports plain Base64, URL-safe Base64, missing padding, and data:...;base64,... values.",
        )
        footer.pack(anchor="w", pady=(8, 0))

    def get_decoded(self) -> tuple[bytes, str | None]:
        value = self.input_text.get("1.0", "end-1c")
        data, mime_type = decode_base64(value)
        self.decoded_bytes = data
        self.mime_type = mime_type
        return data, mime_type

    def preview_text(self):
        try:
            data, mime_type = self.get_decoded()
            text, encoding = bytes_to_text(data)

            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", text)
            self.output_text.configure(state="disabled")

            extra = f", MIME: {mime_type}" if mime_type else ""
            self.status_var.set(f"Decoded {len(data):,} bytes as {encoding}{extra}")
        except Exception as exc:
            messagebox.showerror("Decode Error", str(exc))
            self.status_var.set("Decode failed")

    def save_file(self):
        try:
            data, mime_type = self.get_decoded()
            ext = guess_extension(data, mime_type)
            initial_name = "decoded_file" + ext

            path = filedialog.asksaveasfilename(
                title="Save decoded file",
                initialfile=initial_name,
                defaultextension=ext,
                filetypes=[
                    ("Detected/Default file", "*" + ext),
                    ("All files", "*.*"),
                ],
            )
            if not path:
                return

            with open(path, "wb") as f:
                f.write(data)

            self.status_var.set(f"Saved {len(data):,} bytes to {os.path.basename(path)}")
            messagebox.showinfo("Saved", f"Decoded file saved successfully:\n\n{path}")
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc))
            self.status_var.set("Save failed")

    def paste_clipboard(self):
        try:
            text = self.clipboard_get()
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", text)
            self.status_var.set("Pasted from clipboard")
        except tk.TclError:
            messagebox.showwarning("Clipboard", "Clipboard does not contain text.")

    def clear_all(self):
        self.input_text.delete("1.0", "end")
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.decoded_bytes = None
        self.mime_type = None
        self.status_var.set("Ready")

if __name__ == "__main__":
    app = Base64DecoderApp()
    app.mainloop()
