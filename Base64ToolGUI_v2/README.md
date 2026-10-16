# Base64 Encode / Decode Tool v2.0

## Included capabilities

- Encode pasted text to Base64.
- Encode any file to Base64.
- Decode pasted Base64 to readable text.
- Decode pasted Base64 to any file.
- Decode large `.b64`, `.base64`, or `.txt` files.
- Standard and URL-safe Base64.
- Automatic missing `=` padding restoration.
- Strict Base64 validation switch.
- Text encoding selection.
- Configurable Base64 line wrapping.
- Configurable worker threads.
- Configurable file chunk size.
- Background processing + progress bar.

## Advanced Process Config

Open the **Advanced Process Config** tab.

Recommended starting values:

- Worker threads: 2–4
- Chunk size: 4 MB
- URL-safe: Off unless your source uses URL-safe Base64
- Strict validation: On
- Restore padding: On
- Encoding: UTF-8
- Line wrap: 0

For very large files, try 4–8 workers and 8–32 MB chunks.

More threads do not always improve performance. Base64 conversion is already
implemented in optimized native code. The configurable worker pool is mainly
useful for large-file chunk processing and I/O overlap.

## Why chunk alignment matters

Base64 works in 3-byte input groups and produces 4 Base64 characters.

The application therefore:

- aligns encoding chunks to multiples of 3 bytes;
- aligns decoding chunks to multiples of 4 Base64 characters;
- preserves result order when multiple workers are active.

This prevents multithreaded chunk boundaries from changing the decoded data.

## Run from Python

Python 3.10+ recommended.

    py base64_tool_gui.py

or double-click:

    run.bat

## Build standalone EXE

Double-click:

    build_exe.bat

Output:

    dist\Base64Tool.exe

## Build Windows installer

Install Inno Setup 6 first:

    winget install --id JRSoftware.InnoSetup -e -s winget -i

Then:

    build_exe.bat
    build_installer.bat

Output:

    installer_output\Base64Tool_Setup_v2.exe

## Security note

Base64 is encoding, not encryption. Only open decoded files from sources you trust.
