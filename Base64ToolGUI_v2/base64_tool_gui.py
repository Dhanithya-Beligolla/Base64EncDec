import base64
import binascii
import mimetypes
import os
import queue
import re
import threading
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "Base64 Encode / Decode Tool"
APP_VERSION = "2.0.0"
PREVIEW_LIMIT = 5 * 1024 * 1024


def strip_data_url(text):
    text = text.strip()
    mime = None
    m = re.match(r"^data:([^;,]+)?(?:;charset=[^;,]+)?;base64,(.*)$", text, re.I | re.S)
    if m:
        mime = m.group(1)
        text = m.group(2)
    return text, mime


def normalize_b64(text, urlsafe=False, restore_padding=True):
    text, mime = strip_data_url(text)
    text = re.sub(r"\s+", "", text)
    if urlsafe:
        text = text.replace("-", "+").replace("_", "/")
    if restore_padding and len(text) % 4:
        text += "=" * (4 - len(text) % 4)
    return text, mime


def encode_block(data, urlsafe=False):
    return base64.urlsafe_b64encode(data) if urlsafe else base64.b64encode(data)


def decode_block(data, validate=True):
    return base64.b64decode(data, validate=validate)


def guess_extension(data, mime=None):
    signatures = [
        (b"%PDF-", ".pdf"), (b"\x89PNG\r\n\x1a\n", ".png"),
        (b"\xff\xd8\xff", ".jpg"), (b"GIF87a", ".gif"),
        (b"GIF89a", ".gif"), (b"PK\x03\x04", ".zip"),
        (b"Rar!\x1a\x07", ".rar"), (b"\x1f\x8b", ".gz"),
        (b"ID3", ".mp3"), (b"OggS", ".ogg"),
        (b"7z\xbc\xaf\x27\x1c", ".7z"), (b"MZ", ".exe"),
    ]
    for sig, ext in signatures:
        if data.startswith(sig):
            return ext
    if data.startswith(b"RIFF") and len(data) >= 12:
        return {b"WAVE": ".wav", b"WEBP": ".webp", b"AVI ": ".avi"}.get(data[8:12], ".bin")
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return ".mp4"
    if mime:
        return mimetypes.guess_extension(mime) or ".bin"
    return ".bin"


def decode_to_text(data, preferred="utf-8"):
    encodings = []
    for enc in [preferred, "utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1"]:
        if enc not in encodings:
            encodings.append(enc)
    for enc in encodings:
        try:
            text = data.decode(enc)
            if "\x00" not in text[:1000] or "utf-16" in enc:
                return text, enc
        except (UnicodeDecodeError, LookupError):
            pass
    return data.decode("utf-8", errors="replace"), "utf-8 with replacement"


def parallel_map(items, fn, workers):
    if workers <= 1:
        for item in items:
            yield fn(item)
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="B64Worker") as pool:
            for result in pool.map(fn, items):
                yield result


def encode_file_parallel(src_path, dst_path, workers=4, chunk_size=4*1024*1024,
                         urlsafe=False, wrap=0, progress=None):
    # Base64 chunks must be aligned to 3 input bytes.
    chunk_size = max(3, chunk_size - (chunk_size % 3))
    total = os.path.getsize(src_path)
    processed = 0

    def chunks():
        nonlocal processed
        with open(src_path, "rb") as src:
            while True:
                block = src.read(chunk_size)
                if not block:
                    break
                processed += len(block)
                if progress:
                    progress(processed, total)
                yield block

    fn = lambda b: encode_block(b, urlsafe)
    col = 0
    with open(dst_path, "wb") as dst:
        for encoded in parallel_map(chunks(), fn, workers):
            if wrap > 0:
                pos = 0
                while pos < len(encoded):
                    take = min(wrap - col, len(encoded) - pos)
                    dst.write(encoded[pos:pos+take])
                    pos += take
                    col += take
                    if col == wrap:
                        dst.write(b"\n")
                        col = 0
            else:
                dst.write(encoded)
    if progress:
        progress(total, total)


def normalized_file_chunks(src_path, char_chunk=4*1024*1024, urlsafe=False,
                           restore_padding=True):
    carry = ""
    first = True
    with open(src_path, "r", encoding="utf-8-sig", errors="strict") as src:
        while True:
            part = src.read(char_chunk)
            if not part:
                break
            if first:
                first = False
                # For data URLs, remove prefix once the comma is available.
                if part.lstrip().lower().startswith("data:"):
                    prefix_buffer = part
                    while "," not in prefix_buffer:
                        more = src.read(char_chunk)
                        if not more:
                            break
                        prefix_buffer += more
                    prefix_buffer, _ = strip_data_url(prefix_buffer)
                    part = prefix_buffer
            part = re.sub(r"\s+", "", part)
            if urlsafe:
                part = part.replace("-", "+").replace("_", "/")
            carry += part
            # Emit only complete quartets, but keep one quartet for safe EOF/padding handling.
            usable = (len(carry) // 4) * 4
            if usable >= 8:
                emit_len = usable - 4
                yield carry[:emit_len].encode("ascii")
                carry = carry[emit_len:]
    if carry:
        if restore_padding and len(carry) % 4:
            carry += "=" * (4 - len(carry) % 4)
        yield carry.encode("ascii")


def decode_file_parallel(src_path, dst_path, workers=4, chunk_size=4*1024*1024,
                         urlsafe=False, validate=True, restore_padding=True, progress=None):
    total = os.path.getsize(src_path)
    progress_bytes = 0

    raw = normalized_file_chunks(src_path, max(4096, chunk_size), urlsafe, restore_padding)

    def tracked():
        nonlocal progress_bytes
        for block in raw:
            progress_bytes = min(total, progress_bytes + len(block))
            if progress:
                progress(progress_bytes, total)
            yield block

    fn = lambda b: decode_block(b, validate)
    with open(dst_path, "wb") as dst:
        for decoded in parallel_map(tracked(), fn, workers):
            dst.write(decoded)
    if progress:
        progress(total, total)


class Base64App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry("1120x820")
        self.minsize(900, 650)

        cpus = os.cpu_count() or 4
        self.workers = tk.IntVar(value=min(4, cpus))
        self.chunk_mb = tk.IntVar(value=4)
        self.urlsafe = tk.BooleanVar(value=False)
        self.validate = tk.BooleanVar(value=True)
        self.restore_padding = tk.BooleanVar(value=True)
        self.wrap = tk.IntVar(value=0)
        self.encoding = tk.StringVar(value="utf-8")

        self.encode_file_path = tk.StringVar()
        self.decode_file_path = tk.StringVar()
        self.events = queue.Queue()
        self.busy = False

        self.build_ui()
        self.after(100, self.poll_events)

    def build_ui(self):
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")

        main = ttk.Frame(self, padding=14)
        main.pack(fill="both", expand=True)
        ttk.Label(main, text="Base64 Encode / Decode Tool",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(main, text="Text + file encoding/decoding with configurable parallel processing.").pack(anchor="w", pady=(0, 10))

        nb = ttk.Notebook(main)
        nb.pack(fill="both", expand=True)

        enc = ttk.Frame(nb, padding=10)
        dec = ttk.Frame(nb, padding=10)
        adv = ttk.Frame(nb, padding=10)
        nb.add(enc, text="Encode")
        nb.add(dec, text="Decode")
        nb.add(adv, text="Advanced Process Config")

        self.build_encode(enc)
        self.build_decode(dec)
        self.build_advanced(adv)

        footer = ttk.Frame(main)
        footer.pack(fill="x", pady=(10, 0))
        self.progress = ttk.Progressbar(footer, maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(footer, textvariable=self.status, width=45).pack(side="left", padx=(10, 0))

    def text_box(self, parent, height=8):
        frame = ttk.Frame(parent)
        txt = tk.Text(frame, height=height, wrap="word", undo=True)
        sb = ttk.Scrollbar(frame, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return frame, txt

    def build_encode(self, tab):
        group = ttk.LabelFrame(tab, text="Encode Text", padding=8)
        group.pack(fill="both", expand=True)
        ttk.Label(group, text="Plain text:").pack(anchor="w")
        frame, self.enc_input = self.text_box(group, 8)
        frame.pack(fill="both", expand=True, pady=4)

        row = ttk.Frame(group); row.pack(fill="x")
        ttk.Button(row, text="Encode Text", command=self.encode_text).pack(side="left")
        ttk.Button(row, text="Paste", command=lambda: self.paste(self.enc_input)).pack(side="left", padx=6)
        ttk.Button(row, text="Clear", command=lambda: self.clear(self.enc_input, self.enc_output)).pack(side="left")

        ttk.Label(group, text="Base64 result:").pack(anchor="w", pady=(8, 0))
        frame, self.enc_output = self.text_box(group, 8)
        frame.pack(fill="both", expand=True, pady=4)

        row = ttk.Frame(group); row.pack(fill="x")
        ttk.Button(row, text="Copy Base64", command=lambda: self.copy(self.enc_output)).pack(side="left")
        ttk.Button(row, text="Save Base64...", command=self.save_encoded_text).pack(side="left", padx=6)

        fg = ttk.LabelFrame(tab, text="Encode Any File", padding=8)
        fg.pack(fill="x", pady=(10, 0))
        ttk.Entry(fg, textvariable=self.encode_file_path).pack(side="left", fill="x", expand=True)
        ttk.Button(fg, text="Browse...", command=self.browse_encode).pack(side="left", padx=6)
        ttk.Button(fg, text="Encode File...", command=self.encode_file).pack(side="left")

    def build_decode(self, tab):
        group = ttk.LabelFrame(tab, text="Decode Base64", padding=8)
        group.pack(fill="both", expand=True)
        ttk.Label(group, text="Base64 input:").pack(anchor="w")
        frame, self.dec_input = self.text_box(group, 9)
        frame.pack(fill="both", expand=True, pady=4)

        row = ttk.Frame(group); row.pack(fill="x")
        ttk.Button(row, text="Preview as Text", command=self.decode_text).pack(side="left")
        ttk.Button(row, text="Decode & Save File", command=self.decode_pasted_to_file).pack(side="left", padx=6)
        ttk.Button(row, text="Paste", command=lambda: self.paste(self.dec_input)).pack(side="left", padx=6)
        ttk.Button(row, text="Clear", command=lambda: self.clear(self.dec_input, self.dec_output)).pack(side="left")

        ttk.Label(group, text="Decoded text preview:").pack(anchor="w", pady=(8, 0))
        frame, self.dec_output = self.text_box(group, 8)
        frame.pack(fill="both", expand=True, pady=4)

        fg = ttk.LabelFrame(tab, text="Decode Base64 Text File", padding=8)
        fg.pack(fill="x", pady=(10, 0))
        ttk.Entry(fg, textvariable=self.decode_file_path).pack(side="left", fill="x", expand=True)
        ttk.Button(fg, text="Browse...", command=self.browse_decode).pack(side="left", padx=6)
        ttk.Button(fg, text="Decode File...", command=self.decode_file).pack(side="left")

    def build_advanced(self, tab):
        cpus = os.cpu_count() or 1

        g = ttk.LabelFrame(tab, text="Parallel Processing", padding=12)
        g.pack(fill="x")
        ttk.Label(g, text="Worker threads:", width=22).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Spinbox(g, from_=1, to=max(32, cpus * 2), textvariable=self.workers, width=10).grid(row=0, column=1, sticky="w")
        ttk.Label(g, text=f"Logical CPUs detected: {cpus}. Start with 2–4 workers.").grid(row=0, column=2, sticky="w", padx=10)

        ttk.Label(g, text="Chunk size (MB):", width=22).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Spinbox(g, from_=1, to=256, textvariable=self.chunk_mb, width=10).grid(row=1, column=1, sticky="w")
        ttk.Label(g, text="Larger chunks use more RAM.").grid(row=1, column=2, sticky="w", padx=10)

        b = ttk.LabelFrame(tab, text="Base64 Options", padding=12)
        b.pack(fill="x", pady=10)
        ttk.Checkbutton(b, text="URL-safe Base64 (- and _)", variable=self.urlsafe).pack(anchor="w", pady=3)
        ttk.Checkbutton(b, text="Strict validation while decoding", variable=self.validate).pack(anchor="w", pady=3)
        ttk.Checkbutton(b, text="Restore missing = padding automatically", variable=self.restore_padding).pack(anchor="w", pady=3)

        o = ttk.LabelFrame(tab, text="Text / Output", padding=12)
        o.pack(fill="x")
        r = ttk.Frame(o); r.pack(fill="x", pady=3)
        ttk.Label(r, text="Character encoding:", width=22).pack(side="left")
        ttk.Combobox(r, textvariable=self.encoding, state="readonly", width=18,
                     values=["utf-8","utf-8-sig","utf-16","utf-16-le","utf-16-be","ascii","latin-1"]).pack(side="left")

        r = ttk.Frame(o); r.pack(fill="x", pady=3)
        ttk.Label(r, text="Base64 line wrap:", width=22).pack(side="left")
        ttk.Combobox(r, textvariable=self.wrap, state="readonly", width=18,
                     values=[0,64,76,80,120]).pack(side="left")
        ttk.Label(r, text="0 = no wrapping").pack(side="left", padx=8)

        i = ttk.LabelFrame(tab, text="Advanced Processing Notes", padding=12)
        i.pack(fill="both", expand=True, pady=10)
        ttk.Label(i, justify="left", wraplength=930, text=
            "Large file operations use ThreadPoolExecutor workers. Encoding chunks are aligned "
            "to multiples of 3 bytes and decoding chunks to multiples of 4 Base64 characters, "
            "so parallel chunk boundaries do not corrupt data. Results are written in the same "
            "order they were read. The file operation itself also runs outside Tkinter's UI "
            "thread, keeping the window responsive.\n\n"
            "More threads do not always mean more speed. Base64 conversion is already implemented "
            "efficiently in Python's native libraries, so 2–4 workers is a good starting point."
        ).pack(anchor="w")

        ttk.Button(tab, text="Restore Defaults", command=self.defaults).pack(anchor="w")

    def workers_value(self):
        try: return max(1, int(self.workers.get()))
        except Exception: return 1

    def chunk_value(self):
        try: return max(1, int(self.chunk_mb.get())) * 1024 * 1024
        except Exception: return 4 * 1024 * 1024

    def update_progress(self, current, total):
        pct = 100 if total <= 0 else min(100, current * 100 / total)
        self.events.put(("progress", pct))

    def background(self, label, fn, done):
        if self.busy:
            messagebox.showwarning("Busy", "Another operation is already running.")
            return
        self.busy = True
        self.progress["value"] = 0
        self.status.set(label)
        def run():
            try:
                fn()
                self.events.put(("done", done))
            except Exception as e:
                self.events.put(("error", str(e)))
        threading.Thread(target=run, daemon=True, name="B64Controller").start()

    def poll_events(self):
        try:
            while True:
                e = self.events.get_nowait()
                if e[0] == "progress":
                    self.progress["value"] = e[1]
                elif e[0] == "done":
                    self.busy = False
                    self.progress["value"] = 100
                    self.status.set("Completed")
                    messagebox.showinfo("Completed", e[1])
                elif e[0] == "error":
                    self.busy = False
                    self.status.set("Operation failed")
                    messagebox.showerror("Error", e[1])
        except queue.Empty:
            pass
        self.after(100, self.poll_events)

    def paste(self, widget):
        try:
            widget.delete("1.0", "end")
            widget.insert("1.0", self.clipboard_get())
            self.status.set("Pasted from clipboard")
        except tk.TclError:
            messagebox.showwarning("Clipboard", "Clipboard does not contain text.")

    def copy(self, widget):
        text = widget.get("1.0", "end-1c")
        if not text:
            return messagebox.showwarning("Copy", "There is nothing to copy.")
        self.clipboard_clear(); self.clipboard_append(text)
        self.status.set("Copied to clipboard")

    def clear(self, *widgets):
        for w in widgets: w.delete("1.0", "end")
        self.progress["value"] = 0
        self.status.set("Ready")

    def defaults(self):
        self.workers.set(min(4, os.cpu_count() or 4))
        self.chunk_mb.set(4); self.urlsafe.set(False); self.validate.set(True)
        self.restore_padding.set(True); self.wrap.set(0); self.encoding.set("utf-8")
        self.status.set("Defaults restored")

    def encode_text(self):
        text = self.enc_input.get("1.0", "end-1c")
        if not text:
            return messagebox.showwarning("Encode", "Enter text first.")
        try:
            raw = text.encode(self.encoding.get())
            out = encode_block(raw, self.urlsafe.get()).decode("ascii")
            wrap = int(self.wrap.get())
            if wrap > 0:
                out = "\n".join(out[i:i+wrap] for i in range(0, len(out), wrap))
            self.enc_output.delete("1.0", "end"); self.enc_output.insert("1.0", out)
            self.progress["value"] = 100
            self.status.set(f"Encoded {len(raw):,} bytes")
        except Exception as e:
            messagebox.showerror("Encode Error", str(e))

    def save_encoded_text(self):
        text = self.enc_output.get("1.0", "end-1c")
        if not text:
            return messagebox.showwarning("Save", "Encode something first.")
        p = filedialog.asksaveasfilename(defaultextension=".b64", initialfile="encoded.b64",
                                         filetypes=[("Base64", "*.b64"),("Text","*.txt"),("All","*.*")])
        if p:
            with open(p, "w", encoding="ascii") as f: f.write(text)
            self.status.set("Base64 saved")

    def browse_encode(self):
        p = filedialog.askopenfilename(title="Select any file to encode")
        if p: self.encode_file_path.set(p)

    def encode_file(self):
        src = self.encode_file_path.get().strip()
        if not os.path.isfile(src):
            return messagebox.showwarning("Encode File", "Select a valid input file.")
        dst = filedialog.asksaveasfilename(initialfile=os.path.basename(src)+".b64",
                                          defaultextension=".b64",
                                          filetypes=[("Base64","*.b64"),("Text","*.txt"),("All","*.*")])
        if not dst: return
        workers = self.workers_value()
        def task():
            encode_file_parallel(src, dst, workers, self.chunk_value(), self.urlsafe.get(),
                                 int(self.wrap.get()), self.update_progress)
        self.background(f"Encoding with {workers} workers...", task, f"Encoded file saved:\n{dst}")

    def decode_current(self):
        text = self.dec_input.get("1.0", "end-1c")
        if not text.strip():
            raise ValueError("Paste Base64 data first.")
        normalized, mime = normalize_b64(text, self.urlsafe.get(), self.restore_padding.get())
        try:
            data = base64.b64decode(normalized.encode("ascii"), validate=self.validate.get())
        except (binascii.Error, UnicodeEncodeError, ValueError) as e:
            raise ValueError("Invalid Base64 for the current Advanced settings.") from e
        return data, mime

    def decode_text(self):
        try:
            data, mime = self.decode_current()
            if len(data) > PREVIEW_LIMIT:
                text = f"[Decoded size: {len(data):,} bytes. Preview skipped; use Decode & Save File.]"
                used = "not previewed"
            else:
                text, used = decode_to_text(data, self.encoding.get())
            self.dec_output.delete("1.0", "end"); self.dec_output.insert("1.0", text)
            self.progress["value"] = 100
            self.status.set(f"Decoded {len(data):,} bytes ({used})")
        except Exception as e:
            messagebox.showerror("Decode Error", str(e))

    def decode_pasted_to_file(self):
        try:
            data, mime = self.decode_current()
            ext = guess_extension(data[:64], mime)
        except Exception as e:
            return messagebox.showerror("Decode Error", str(e))
        dst = filedialog.asksaveasfilename(initialfile="decoded_file"+ext, defaultextension=ext,
                                          filetypes=[("Detected/default","*"+ext),("All","*.*")])
        if dst:
            with open(dst, "wb") as f: f.write(data)
            self.progress["value"] = 100
            self.status.set(f"Saved {len(data):,} decoded bytes")
            messagebox.showinfo("Saved", f"Decoded file saved:\n{dst}")

    def browse_decode(self):
        p = filedialog.askopenfilename(title="Select Base64 text file",
                                       filetypes=[("Base64/Text","*.b64 *.base64 *.txt"),("All","*.*")])
        if p: self.decode_file_path.set(p)

    def decode_file(self):
        src = self.decode_file_path.get().strip()
        if not os.path.isfile(src):
            return messagebox.showwarning("Decode File", "Select a valid Base64 text file.")
        dst = filedialog.asksaveasfilename(initialfile="decoded_file.bin",
                                          filetypes=[("All files","*.*")])
        if not dst: return
        workers = self.workers_value()
        def task():
            decode_file_parallel(src, dst, workers, self.chunk_value(), self.urlsafe.get(),
                                 self.validate.get(), self.restore_padding.get(), self.update_progress)
        self.background(f"Decoding with {workers} workers...", task, f"Decoded file saved:\n{dst}")


if __name__ == "__main__":
    Base64App().mainloop()
