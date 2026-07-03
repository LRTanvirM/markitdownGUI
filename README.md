# MarkItDown GUI — v1.0

A local **native desktop app** to convert files to clean Markdown using Microsoft's [MarkItDown](https://github.com/microsoft/markitdown), plus **offline OCR** for images. Dark UI.

- **UI:** native Qt (PySide6) window — drag-and-drop one or many files, checkbox selection, live Markdown preview, native Save dialogs.
- **Documents:** PDF, Word (DOCX), PowerPoint (PPTX), Excel (XLSX/XLS), HTML, CSV, JSON, XML, EPUB, ZIP → via MarkItDown.
- **Images** (PNG, JPG, BMP, TIFF, WEBP, GIF) → text extracted with **RapidOCR** (onnxruntime, fully offline).
- Everything runs on your machine; nothing is uploaded. No audio support.

```
markitdown-gui/
  app.py                 # PySide6 desktop app (entry point)
  convert.py             # conversion engine: MarkItDown (docs) + RapidOCR (images)
  make_icon.py           # generates icon.ico (the red ".md" logo)
  MarkItDownGUI.spec     # PyInstaller build recipe
  version_info.txt       # exe version resource (1.0)
  build.bat              # one-shot: deps -> icon -> exe (-> installer if Inno Setup present)
  install.bat            # install the built exe on this PC (no tooling needed)
  Install-MarkItDown.ps1 # the installer/uninstaller logic
  installer.iss          # optional: Inno Setup script for a shareable Setup.exe
  requirements.txt
```

## 🚀 Download

Grab a release asset — no Python needed:

| File | What it is |
|---|---|
| `MarkItDown-Setup.exe` | installer — Start Menu/Desktop shortcuts, clean uninstall |
| `MarkItDownGUI-portable-onedir.zip` | portable folder build, unzip and run — fast launch |
| `MarkItDown-Portable-Standalone.exe` | single-file portable exe — slower first launch (self-extracts) |

## 🛠️ Build

Needs Python 3.10+ and internet once (to install dependencies). The resulting builds need neither.

```bat
build.bat
```

Produces three things in `dist\`:

| Output | What it is | Launch time |
|---|---|---|
| `MarkItDownGUI.exe` | single-file portable exe | slower — self-extracts to a temp dir every launch |
| `MarkItDownGUI\` (folder) | onedir build, same app | fast — no extraction step |
| `MarkItDownGUI-portable.zip` | the onedir folder, zipped for sharing | fast |

Both are the same app built from the same `MarkItDownGUI.spec`; pick whichever you prefer — a single file to copy around, or the folder/zip for a snappier launch. No Python, no install, works offline (including OCR) either way.

Manual equivalent:

```powershell
pip install -r requirements.txt
python make_icon.py
python -m PyInstaller --noconfirm MarkItDownGUI.spec
```

## 💾 Install it (optional)

To add Start Menu + Desktop shortcuts and an entry in **Apps & features** (per-user, no admin), pick one:

- **Shareable `Setup.exe`** (recommended): install [Inno Setup 6](https://jrsoftware.org/isdl.php) once (`winget install JRSoftware.InnoSetup`), then `build.bat` also produces `dist\MarkItDown-1.0-Setup.exe`. It installs the fast onedir build to `%LOCALAPPDATA%\Programs\MarkItDown`.
- **No extra tooling:** run `install.bat` — copies the portable exe to `%LOCALAPPDATA%\Programs\MarkItDown` instead. Uninstall from *Apps & features*, or run `Install-MarkItDown.ps1 -Uninstall`.

## 💻 Run from source

```powershell
pip install -r requirements.txt
python app.py                 # opens the window
python app.py --selftest      # headless engine check (docs + OCR)
```

## 📖 Using it

1. Drag files onto the window (or **Add files…**).
2. Each file converts automatically; click one to preview it (Preview / Markdown tabs).
3. **Download .md** saves the current file via a native Save dialog. Tick files and use **Merge & save** (one combined `.md`) or **Save each** (pick a folder). **Merged view** previews the combined result.

## ⚠️ Notes & caveats

- **Size:** ~215 MB either way. It bundles PySide6, OpenCV + ONNX OCR models, `onnxruntime`, and `pandas`. That's the cost of a fully offline, install-free build.
- **OCR scope:** RapidOCR is strong on printed/screen text; accuracy on handwriting or noisy scans varies. English + Latin scripts work out of the box.
- **First image** takes ~1–2 s extra while the OCR models load; subsequent images are fast.
- No WebView2 / browser dependency (the app is fully native now).

## 🙏 Acknowledgments

This GUI is a native wrapper around two open-source projects:

- **[MarkItDown](https://github.com/microsoft/markitdown)** by Microsoft (MIT License) — the document conversion engine.
- **[RapidOCR](https://github.com/RapidAI/RapidOCR)** (Apache-2.0 License) — offline OCR for images.
