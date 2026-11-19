"""Write the two evidence sheets and decode their input images."""
import hashlib
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

root = Path(__file__).resolve().parents[1]
font = ImageFont.truetype("DejaVuSans.ttf", 25)


def sheet(destination, columns, rows):
    width, height = 600, 400
    surface = Image.new("RGB", (width * columns, height * len(rows)), "#181d22")
    draw = ImageDraw.Draw(surface)
    for row, panels in enumerate(rows):
        for column, (path, label) in enumerate(panels):
            x, y = column * width, row * height
            with Image.open(path) as image:
                image.load()
                panel = ImageOps.contain(image.convert("RGB"), (width - 18, height - 40))
            surface.paste(panel, (x + (width - panel.width) // 2, y + (height - 40 - panel.height) // 2))
            draw.text((x + 14, y + height - 35), label, font=font, fill="#f3f2ed")
    surface.save(destination)


def main():
    a, b = map(Path, sys.argv[3:5]) if len(sys.argv) == 5 else (root / "C9-A", root / "C9-B")
    previous = Path(sys.argv[1])
    reference = Path(sys.argv[2])
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == (
        "db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07"
    )
    sheet(a / "comparison.png", 2, [
        [(reference, "Approved CG"), (previous / "cg_review.png", "C8 low view")],
        [(a / "cg_review.png", "C9-A local rock-face sculpt"), (a / "cg_review_clay.png", "C9-A clay control")],
    ])
    sheet(b / "comparison.png", 3, [
        [(b / f"{label}_cg_review.png", title) for label, title in
         (("A", "A · C8 / original"), ("B", "B · C8 / new PBR"), ("C", "C · C9-A / same PBR"))],
        [(b / f"{label}_shore_detail.png", title) for label, title in
         (("A", "A · shoreline"), ("B", "B · shoreline"), ("C", "C · shoreline"))],
    ])


if __name__ == "__main__":
    main()
