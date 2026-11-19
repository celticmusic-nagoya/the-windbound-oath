"""Produce an ungraded contact sheet for independent cliff C art review."""
import argparse
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

CG_SHA = "db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    assert hashlib.sha256(args.reference.read_bytes()).hexdigest() == CG_SHA
    sheet = Image.new("RGB", (1920, 1330), "#15202a")
    draw = ImageDraw.Draw(sheet)
    title = ImageFont.truetype("DejaVuSans.ttf", 38)
    label = ImageFont.truetype("DejaVuSans.ttf", 23)
    draw.text((30, 22), "Windwaiting Cliff C2 | independent review", font=title, fill="#f1ece1")

    def panel(path, caption, box):
        x, y, width, height = box
        draw.text((x, y), caption, font=label, fill="#d6dce2")
        with Image.open(path) as image:
            fitted = ImageOps.contain(image.convert("RGB"), (width, height), Image.Resampling.LANCZOS)
            sheet.paste(fitted, (x + (width - fitted.width) // 2, y + 37))

    panel(args.reference, "Approved CG | full composition", (30, 95, 1030, 583))
    panel(args.out / "sunset.png", "Candidate | sunset review", (1090, 95, 800, 583))
    for index, (file, name) in enumerate((("front", "front"), ("left", "left"), ("right", "right"), ("elevated", "elevated"))):
        panel(args.out / (file + ".png"), f"Candidate | {name}", (30 + index * 472, 782, 450, 400))
    draw.text((30, 1268), "Provisional scale and studio cameras. Compare cliff shape, strata and jointing.", font=label, fill="#b2bdc8")
    sheet.save(args.out / "comparison.png")


if __name__ == "__main__":
    main()
