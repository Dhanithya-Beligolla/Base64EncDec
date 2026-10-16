# Base64EncDec

Windows desktop apps for encoding and decoding Base64 text and files. They're written in Python/Tkinter and ship as standalone EXEs.

## Download

Get the latest version from **[Releases](https://github.com/Dhanithya-Beligolla/Base64EncDec/releases/latest)**.

| Version | App | File to download |
| --- | --- | --- |
| **v2.0.0** (current) | Base64 Encode / Decode Tool | `Base64Tool-2.0.0-setup.exe` (installer) or `Base64Tool-2.0.0-portable.exe` (no install) |
| v1.0.0 | Base64 Decoder (decode only) | `Base64Decoder-1.0.0-portable.exe` |

Runs on Windows 10/11 (64-bit) and does not need Python. The EXEs are not code-signed, so SmartScreen may warn on first launch: click **More info → Run anyway**.

## Apps

### Base64 Encode / Decode Tool v2 (`Base64ToolGUI_v2/`)

- Encodes text or any file to Base64, and decodes Base64 to text or to a file.
- Supports standard and URL-safe Base64 and `data:` URLs, restores missing padding, and has an optional strict validation mode.
- Processes large files in chunks on multiple threads, with a progress bar. Worker count, chunk size, text encoding and line wrapping can all be configured.

Full guide: [Base64ToolGUI_v2/README.md](Base64ToolGUI_v2/README.md)

### Base64 Decoder v1 (`Base64DecoderGUI/`)

- Decodes Base64 to a text preview, or saves the decoded bytes as a file. The file type is detected to suggest an extension.

Full guide: [Base64DecoderGUI/README.md](Base64DecoderGUI/README.md)

## Run or build from source

Needs Python 3.10+ with Tkinter on Windows. In an app folder:

| Script | What it does |
| --- | --- |
| `run.bat` | Runs the app from source. |
| `build_exe.bat` | Builds `dist\<App>.exe` with PyInstaller. |
| `build_installer.bat` | Builds a Setup EXE into `installer_output\` with [Inno Setup 6](https://jrsoftware.org/isinfo.php). |

## Repository layout

```
Base64ToolGUI_v2/        v2 source and build scripts
Base64DecoderGUI/        v1 source and build scripts
releases/vX.Y.Z/         published binaries (Git LFS) + SHA256SUMS.txt
.github/release-notes/   release notes, one file per tag
.github/workflows/       publishes a GitHub Release when a tag is pushed
```

## Publishing a release

`*.exe` and `*.zip` files are stored with [Git LFS](https://git-lfs.com), so run `git lfs install` once before cloning or committing.

1. Set the version in the app's `.py` file (`APP_VERSION`) and in `installer.iss` (`MyAppVersion`).
2. Build with `build_exe.bat` and, if needed, `build_installer.bat`.
3. Copy the build outputs into `releases/vX.Y.Z/` (for example `<App>-X.Y.Z-portable.exe`, `<App>-X.Y.Z-setup.exe`). Then write the checksums from Git Bash:
   ```bash
   cd releases/vX.Y.Z && sha256sum *.exe *.zip > SHA256SUMS.txt
   ```
4. Add `.github/release-notes/vX.Y.Z.md`. Its first line `# <title>` becomes the release title.
5. Commit, tag and push:
   ```bash
   git tag -a vX.Y.Z -m "<App> vX.Y.Z"
   git push origin main vX.Y.Z
   ```
   The **Publish release** workflow checks the checksums and creates the GitHub Release with every file from `releases/vX.Y.Z/` attached. Only the highest version is marked *Latest*. The workflow can also be re-run for an existing tag from the **Actions** tab.

## License

[MIT](LICENSE). Base64 is an encoding, not encryption, so only open decoded files from sources you trust.
