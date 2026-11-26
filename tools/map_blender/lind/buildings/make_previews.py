"""LIND-BUILD-01 review previews (PIL only): backdrop composite, 48/96 px game-scale downsamples,
an x4 nearest-neighbour inspection sheet, and a peaceful|burning pair sheet when both exist.

Usage: python3 tools/map_blender/lind/buildings/make_previews.py --run DIR
Writes into DIR/previews/ and appends SHA-256 of every preview to DIR/previews/previews_manifest.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os

from PIL import Image

BG = (196, 201, 190, 255)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def on_bg(im):
    bg = Image.new("RGBA", im.size, BG)
    bg.alpha_composite(im)
    return bg.convert("RGB")


def crop_alpha(im, pad=6):
    bb = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    out = os.path.join(a.run, "previews")
    os.makedirs(out, exist_ok=True)
    rec = {}
    pngs = sorted(f for f in os.listdir(a.run) if f.endswith("_game27.png"))
    for f in pngs:
        im = Image.open(os.path.join(a.run, f)).convert("RGBA")
        base = f[:-4]
        p = os.path.join(out, base + "_bg.png")
        on_bg(im).save(p)
        rec[os.path.basename(p)] = sha(p)
        c = crop_alpha(im)
        smalls = []
        for px in (96, 48):
            s = c.copy()
            s.thumbnail((px, px), Image.LANCZOS)
            sp = os.path.join(out, f"{base}_{px}px.png")
            on_bg(s).save(sp)
            rec[os.path.basename(sp)] = sha(sp)
            smalls.append(on_bg(s))
        # inspection sheet: 96 and 48 shown x4 nearest
        W = smalls[0].width * 4 + smalls[1].width * 4 + 30
        H = max(smalls[0].height, smalls[1].height) * 4 + 20
        sheet = Image.new("RGB", (W, H), BG[:3])
        sheet.paste(smalls[0].resize((smalls[0].width * 4, smalls[0].height * 4), Image.NEAREST), (10, 10))
        sheet.paste(smalls[1].resize((smalls[1].width * 4, smalls[1].height * 4), Image.NEAREST),
                    (20 + smalls[0].width * 4, 10))
        shp = os.path.join(out, f"{base}_gamescale_x4.png")
        sheet.save(shp)
        rec[os.path.basename(shp)] = sha(shp)
    for f in pngs:
        if "_peaceful_" in f:
            g = f.replace("_peaceful_", "_burning_")
            if g in pngs:
                a1 = on_bg(Image.open(os.path.join(a.run, f)).convert("RGBA"))
                a2 = on_bg(Image.open(os.path.join(a.run, g)).convert("RGBA"))
                pair = Image.new("RGB", (a1.width + a2.width, a1.height), BG[:3])
                pair.paste(a1, (0, 0))
                pair.paste(a2, (a1.width, 0))
                pair.thumbnail((1280, 1280))
                pp = os.path.join(out, f.replace("_peaceful_game27.png", "_continuity_pair.png"))
                pair.save(pp)
                rec[os.path.basename(pp)] = sha(pp)
    json.dump(rec, open(os.path.join(out, "previews_manifest.json"), "w"), indent=1)
    print(f"{len(rec)} previews")


if __name__ == "__main__":
    main()
