"""Headless conversion engine: MarkItDown for documents, RapidOCR for images."""
import os

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif"}

_md = None      # MarkItDown instance (lazy)
_ocr = None     # RapidOCR engine (lazy — loading models takes ~1-2s)


def _markitdown(path):
    global _md
    if _md is None:
        from markitdown import MarkItDown
        _md = MarkItDown()
    return _md.convert(path).text_content


def _ocr_image(path):
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    result, _elapse = _ocr(path)
    if not result:
        return "_No text found in image._"
    # result is a list of [box, text, score]; keep reading order as returned.
    lines = [row[1] for row in result if len(row) > 1 and row[1]]
    return "\n\n".join(lines) if lines else "_No text found in image._"


def convert_file(path):
    """Return {'markdown': str, 'error': str|None} for one file."""
    ext = os.path.splitext(path)[1].lower()
    try:
        md = _ocr_image(path) if ext in IMAGE_EXTS else _markitdown(path)
        return {"markdown": md, "error": None}
    except Exception as e:
        return {"markdown": "", "error": f"{type(e).__name__}: {e}"}


def merge(items):
    """items: list of (stem, markdown). Returns one merged markdown document."""
    return "\n\n---\n\n".join(f"# {stem}\n\n{md}" for stem, md in items)


def selftest():
    # ponytail: smallest end-to-end check of both paths (doc + OCR)
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as t:
        t.write("<h1>Hi</h1><p>hello world</p>")
        hp = t.name
    r = convert_file(hp)
    os.unlink(hp)
    assert r["error"] is None and "# Hi" in r["markdown"], r
    print("doc selftest ok:", r["markdown"].replace("\n", " "))

    try:
        from PIL import Image, ImageDraw
        ip = os.path.join(tempfile.gettempdir(), "_ocr_selftest.png")
        img = Image.new("RGB", (360, 90), "white")
        ImageDraw.Draw(img).text((12, 30), "HELLO OCR 123", fill="black")
        img.save(ip)
        r2 = convert_file(ip)
        os.unlink(ip)
        assert r2["error"] is None, r2
        print("ocr selftest ok:", repr(r2["markdown"]))
    except ImportError as e:
        print("ocr selftest skipped:", e)


if __name__ == "__main__":
    selftest()
