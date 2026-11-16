"""AIDAN-MASONRY-ART-02 — game-scale reduction + alpha QA for the scan-carved corner.

Input: RGBA render (shadow catcher keeps contact shadow in alpha).
Output: 48x48 and 96x96 RGBA (Lanczos), x8/x4 nearest-neighbour inspection previews,
and the same thumbnails composited over a field-ground colour, plus a JSON report.
Usage: python3 aidan_masonry_game_scale.py <render_rgba.png> <outdir>
"""
import hashlib
import json
import os
import sys

from PIL import Image


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(src, out):
    os.makedirs(out, exist_ok=True)
    im = Image.open(src)
    assert im.mode == "RGBA", "render must be RGBA, got %s" % im.mode
    a = im.getchannel("A")
    hist = a.histogram()
    n = im.width * im.height
    report = dict(source=os.path.basename(src), source_sha256=sha(src), size=im.size,
                  alpha_zero_ratio=round(hist[0] / n, 4), alpha_full_ratio=round(hist[255] / n, 4),
                  alpha_partial_ratio=round(1 - (hist[0] + hist[255]) / n, 4))
    # crop to the solid object (ignore faint shadow pixels for framing), keep shadow inside the crop
    solid = a.point(lambda v: 255 if v > 200 else 0)
    x0, y0, x1, y1 = solid.getbbox()
    pad = int(0.06 * max(x1 - x0, y1 - y0))
    side = max(x1 - x0, y1 - y0) + 2 * pad
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
    crop = im.crop(box)
    report["crop_box"] = box
    ground = (104, 112, 74, 255)  # neutral field-grass tone for context preview only
    for px, zoom in ((48, 8), (96, 4)):
        t = crop.resize((px, px), Image.LANCZOS)
        p = os.path.join(out, "corner_game_%dpx.png" % px)
        t.save(p)
        g = Image.new("RGBA", t.size, ground)
        g.alpha_composite(t)
        pg = os.path.join(out, "corner_game_%dpx_on_ground.png" % px)
        g.save(pg)
        big = g.resize((px * zoom, px * zoom), Image.NEAREST)
        pb = os.path.join(out, "corner_game_%dpx_on_ground_x%d_nearest.png" % (px, zoom))
        big.save(pb)
        ta = t.getchannel("A").histogram()
        report["%dpx" % px] = dict(file=os.path.basename(p), sha256=sha(p), mode=t.mode, size=t.size,
                                   alpha_zero_px=ta[0], alpha_full_px=ta[255],
                                   on_ground=os.path.basename(pg), inspect=os.path.basename(pb))
    json.dump(report, open(os.path.join(out, "game_scale_report.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
