# -*- mode: python ; coding: utf-8 -*-
# Build:  python -m PyInstaller --noconfirm MarkItDownGUI.spec
#   -> dist/MarkItDownGUI.exe (onefile) + dist/MarkItDownGUI/ (onedir, fast launch)
from PyInstaller.utils.hooks import collect_all, copy_metadata, collect_submodules

datas, binaries, hiddenimports = [], [], []

# Packages that ship data files (models/configs) or use dynamic imports.
for pkg in [
    "markitdown", "magika", "onnxruntime", "pdfminer", "pdfplumber",
    "pptx", "openpyxl", "pandas", "mammoth", "markdownify",
    "charset_normalizer", "docx",
    # OCR stack
    "rapidocr_onnxruntime", "cv2", "shapely", "pyclipper", "PIL",
]:
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

# markitdown discovers its converters/plugins via importlib.metadata entry points.
datas += copy_metadata("markitdown")
hiddenimports += collect_submodules("markitdown")

# app icon — bundled so QIcon(resource_path("icon.ico")) works in the frozen app.
datas += [("icon.ico", ".")]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "PyQt5", "PyQt6", "tkinter",
        # unused Qt modules — trims a lot of size
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
        "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQuickWidgets",
        "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.QtCharts", "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets", "PySide6.QtDataVisualization", "PySide6.QtPdf",
        "PySide6.QtBluetooth", "PySide6.QtPositioning", "PySide6.QtSql", "PySide6.QtTest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

# Onefile: dist\MarkItDownGUI.exe (single file; self-extracts to temp dir every launch)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MarkItDownGUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,          # windowed GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon="icon.ico",             # taskbar + Explorer icon
    version="version_info.txt",  # exe file-properties version = 1.0
)

# Onedir: dist\MarkItDownGUI\MarkItDownGUI.exe (folder; no self-extraction -> fast launch)
exe_dir = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="MarkItDownGUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # ponytail: skip UPX here, per-DLL decompress overhead at load with no launch-speed benefit
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon="icon.ico",
    version="version_info.txt",
)
coll = COLLECT(
    exe_dir,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MarkItDownGUI",
)
