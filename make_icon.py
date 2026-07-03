"""Generate icon.ico (the app icon) — a red rounded square with white ".md".
Run:  python make_icon.py   ->  icon.ico  (+ icon_preview.png to eyeball)
"""
from PIL import Image, ImageDraw, ImageFont

RED = (250, 0, 0, 255)
SIZES = [256, 128, 64, 48, 32, 16]


def _font(px):
    for name in ("arialbd.ttf", "segoeuib.ttf"):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def render(size):
    scale = 4  # supersample for crisp edges, then downscale
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = round(s * 0.05)
    d.rounded_rectangle([pad, pad, s - pad, s - pad], radius=round(s * 0.17), fill=RED)

    text = ".md"
    font = _font(round(s * 0.46))
    box = d.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text(((s - tw) / 2 - box[0], (s - th) / 2 - box[1]), text, font=font, fill=(255, 255, 255, 255))
    return img.resize((size, size), Image.LANCZOS)


def main():
    frames = [render(s) for s in SIZES]
    frames[0].save("icon.ico", format="ICO",
                   sizes=[(s, s) for s in SIZES], append_images=frames[1:])
    render(256).save("icon_preview.png")
    print("wrote icon.ico and icon_preview.png")


if __name__ == "__main__":
    main()
