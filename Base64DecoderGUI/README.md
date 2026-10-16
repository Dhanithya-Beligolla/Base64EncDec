# Base64 Decoder GUI for Windows

A small Python/Tkinter desktop application that can:

- Paste plain Base64 text.
- Accept URL-safe Base64.
- Accept Base64 with missing `=` padding.
- Accept `data:...;base64,...` values.
- Decode Base64 to readable text.
- Decode Base64 and save the raw bytes as any file.
- Guess common file types such as PDF, PNG, JPG, ZIP, MP3, WAV and MP4.

## 1. Requirements

For running from source:

- Windows 10/11
- Python 3.10+ recommended
- Tkinter (included with the standard Windows installer from python.org)

For building:

- PyInstaller
- Inno Setup 6, only if you want a normal Windows Setup installer.

## 2. Run directly with Python

Open Command Prompt inside this folder and run:

    py base64_decoder_gui.py

If `py` is unavailable:

    python base64_decoder_gui.py

You can also double-click:

    run.bat

## 3. How to use

1. Copy your Base64 value.
2. Open Base64 Decoder.
3. Paste it into the upper box, or click **Paste Clipboard**.
4. For text:
   - Click **Decode / Preview Text**.
5. For a PDF, image, ZIP, audio file, document, or other binary:
   - Click **Decode & Save File**.
   - Choose the filename and location.

Example text Base64:

    SGVsbG8gV29ybGQh

The decoded text is:

    Hello World!

## 4. Build a standalone Windows EXE

Run:

    build_exe.bat

The build script installs PyInstaller and creates:

    dist\Base64Decoder.exe

The target computer does NOT need Python installed.

Equivalent manual command:

    py -m pip install pyinstaller
    py -m PyInstaller --noconfirm --clean --onefile --windowed --name Base64Decoder base64_decoder_gui.py

## 5. Build a Windows installer

### Step A - Install Inno Setup 6

You can install it manually from the official Inno Setup site, or with:

    winget install --id JRSoftware.InnoSetup -e -s winget -i

### Step B - Build the EXE

    build_exe.bat

### Step C - Build the installer

    build_installer.bat

The final installer will be:

    installer_output\Base64Decoder_Setup.exe

The installer provides:

- Installation under Program Files / user app directory as appropriate.
- Start Menu shortcut.
- Optional Desktop shortcut.
- Uninstaller entry in Windows.
- Optional app launch after setup.

## 6. Files

- `base64_decoder_gui.py` - main GUI application.
- `run.bat` - runs the Python source.
- `requirements.txt` - build dependency.
- `build_exe.bat` - builds a standalone EXE with PyInstaller.
- `installer.iss` - Inno Setup installer definition.
- `build_installer.bat` - builds the Setup EXE.
- `README.md` - this guide.

## 7. Important note

Base64 is only an encoding format. Decoding arbitrary Base64 can produce any type
of bytes. Only open decoded files when you trust their source.
