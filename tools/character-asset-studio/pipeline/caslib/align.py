"""Internal coordinate normalisation / alignment (no UI). Writes a NEW candidate file only.

1. If the image size differs from the canvas, it is placed with the studio's placement() rule
   (uniform scale, bottom-centred; never anisotropic).
2. The ground contact (lowest alpha>=128 row; x = centre of the outer sole span at bottom-6) is measured
   and the image is translated by whole pixels so the contact lands on the anchor.
3. If the translation would push opaque pixels off the canvas, nothing is written (FAIL).
"""
from pathlib import Path

from .core import REPO_ROOT, PolicyError, alignment_offset, guard_write, placement, rel, sha256_file
from .imageqa import measure


def align(src, dst, canvas, anchor_px, align_x=True, repo_root=REPO_ROOT):
    from PIL import Image
    src = Path(src)
    out = guard_write(dst, repo_root)            # never overwrites, never writes protected paths
    with Image.open(src) as im0:
        im = im0.convert("RGBA")
    W, H = canvas["width"], canvas["height"]
    pl = placement(im.width, im.height, canvas)
    if not pl["exact"]:
        im = im.resize((round(pl["w"]), round(pl["h"])), Image.LANCZOS)
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        base.alpha_composite(im, (round(pl["x"]), round(pl["y"])))
        im = base
    m = measure(im)
    if not m.get("bbox"):
        raise PolicyError("no opaque content to align")
    contact = [m["contact"]["x"], m["contact"]["bottomRow"]]
    dx, dy = alignment_offset(contact, anchor_px)
    if not align_x:
        dx = 0
    x0, y0, x1, y1 = m["bbox"]
    if x0 + dx < 0 or y0 + dy < 0 or x1 + dx >= W or y1 + dy >= H:
        return {"result": "FAIL", "reason": "translation would clip opaque pixels", "offset": [dx, dy], "bbox": m["bbox"], "written": None}
    shifted = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shifted.alpha_composite(im, (dx, dy)) if dx >= 0 and dy >= 0 else shifted.paste(im, (dx, dy), im)
    out.parent.mkdir(parents=True, exist_ok=True)
    shifted.save(out, optimize=True)
    return {"result": "PASS", "source": rel(src, repo_root), "sourceSha256": sha256_file(src), "placement": pl,
            "contactBefore": contact, "anchor": list(anchor_px), "offset": [dx, dy],
            "written": {"path": rel(out, repo_root), "sha256": sha256_file(out)}, "status": "UNAPPROVED_CANDIDATE"}
