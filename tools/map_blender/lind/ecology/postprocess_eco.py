"""LIND-ECO-01 post-processing of renders (pure PIL/numpy, no bpy).

  python3 tools/map_blender/lind/ecology/postprocess_eco.py
Produces in renders/:
  eco_icons_96px_sheet.png / eco_icons_48px_sheet.png  : game-camera icons downsampled (LANCZOS) on ground tone
  eco_vignette_gamescale_48.png / _96.png              : vignette downsampled so a 1.7 m figure would be ~48 / 96 px
  eco_windpair_sheet.png                               : 2x2 wind1/wind0 x f12/f30 with labels
  eco_windpair_diff_wind1.png / _wind0.png             : |f12 - f30| amplified x8
  eco_water_module_diff_wind0.png                      : water flows while wind=0
  eco_lineup_large_labeled.png                         : status labels (blockout marked)
and appends their SHA-256 + pixel-diff statistics to renders.json.
"""
import hashlib
import json
import pathlib

import numpy as np
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
R = REPO / "assets" / "candidates" / "LIND-ECO-01" / "eco_kit_v1" / "renders"
GROUND = (52, 70, 30, 255)


def load(n):
    return Image.open(R / n)


def diff(a, b, name):
    x = np.asarray(load(a).convert("RGB")).astype(np.int16)
    y = np.asarray(load(b).convert("RGB")).astype(np.int16)
    d = np.abs(x - y).max(axis=2)
    Image.fromarray(np.clip(d * 8, 0, 255).astype(np.uint8), "L").save(R / name)
    return {"max": int(d.max()), "mean": round(float(d.mean()), 4), "changed_px_gt8": int((d > 8).sum()),
            "changed_frac_gt8": round(float((d > 8).mean()), 5)}


def label(img, text, xy=(8, 6), fill=(255, 255, 255), bg=(0, 0, 0, 160)):
    d = ImageDraw.Draw(img, "RGBA")
    w = int(d.textlength(text)) + 10
    d.rectangle([xy[0] - 4, xy[1] - 3, xy[0] + w, xy[1] + 14], fill=bg)
    d.text(xy, text, fill=fill)


def main():
    stats = {}
    icons = sorted(R.glob("icon256_*.png"))
    for px in (96, 48):
        cols = 8
        rows = (len(icons) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * (px + 6) + 6, rows * (px + 6) + 6), (30, 30, 30, 255))
        for i, f in enumerate(icons):
            ic = Image.open(f).convert("RGBA").resize((px, px), Image.LANCZOS)
            tile = Image.new("RGBA", (px, px), GROUND)
            tile.alpha_composite(ic)
            sheet.paste(tile, (6 + (i % cols) * (px + 6), 6 + (i // cols) * (px + 6)))
        sheet.save(R / ("eco_icons_%dpx_sheet.png" % px))
    stats["icon_order"] = [f.stem.replace("icon256_", "") for f in icons]

    gv = R / "eco_gameview_28deg_ortho_wind1_f12.png"
    if gv.exists():
        # ortho_scale 30 m over 1280 px -> 42.7 px/m; a 1.75 m figure = 74.7 px. Scale so it is 48 / 96 px.
        im = Image.open(gv).convert("RGB")
        for tgt in (48, 96):
            f = tgt / (1.75 * 1280 / 30.0)
            if f > 1.0:  # would be an upsample (no information): skip, native render is ~75 px/figure
                stats["gameview_figure%dpx" % tgt] = "SKIPPED_UPSAMPLE (native ~75 px per 1.75 m figure)"
                continue
            im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS).save(
                R / ("eco_gameview_figure%dpx.png" % tgt))
    v = R / "eco_farmland_vignette_wind1_f12.png"
    if v.exists():
        im = Image.open(v).convert("RGB")
        for tgt in (48, 96):
            # vignette camera: a 1.7 m figure at the fence line spans ~70 px at 1280 wide (measured from
            # the 1.1 m fence posts ~45 px). Scale so that figure would be tgt px tall.
            f = tgt / 70.0
            if f > 1.0:
                stats["vignette_gamescale_%d" % tgt] = "SKIPPED_UPSAMPLE"
                continue
            im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS).save(
                R / ("eco_vignette_gamescale_%d.png" % tgt))

    names = ["eco_windpair_wind1_f12.png", "eco_windpair_wind1_f30.png", "eco_windpair_wind0_f12.png", "eco_windpair_wind0_f30.png"]
    if all((R / n).exists() for n in names):
        w, h = load(names[0]).size
        s = 0.5
        tw, th = int(w * s), int(h * s)
        sheet = Image.new("RGB", (tw * 2 + 6, th * 2 + 6), (20, 20, 20))
        for i, n in enumerate(names):
            t = load(n).convert("RGB").resize((tw, th), Image.LANCZOS)
            label(t, n.replace("eco_windpair_", "").replace(".png", "").replace("_", "  "))
            sheet.paste(t, ((i % 2) * (tw + 6), (i // 2) * (th + 6)))
        sheet.save(R / "eco_windpair_sheet.png")
        stats["windpair_diff_wind1"] = diff(names[0], names[1], "eco_windpair_diff_wind1.png")
        stats["windpair_diff_wind0"] = diff(names[2], names[3], "eco_windpair_diff_wind0.png")
    wn = ["eco_water_module_wind0_f12.png", "eco_water_module_wind0_f30.png"]
    if all((R / n).exists() for n in wn):
        stats["water_module_diff_wind0"] = diff(wn[0], wn[1], "eco_water_module_diff_wind0.png")

    lg = R / "eco_lineup_large_wind0.png"
    if lg.exists():
        im = Image.open(lg).convert("RGBA")
        label(im, "LIND-ECO-01 eco_kit_v1 CANDIDATE - wind=0 - preview ground/sky are staging only")
        label(im, "eco_cow_blockout + eco_chicken_hen_blockout: STRUCTURAL_BLOCKOUT_NOT_ART | grey figure = 1.75 m scale proxy", (8, 26), fill=(255, 210, 120))
        im.convert("RGB").save(R / "eco_lineup_large_labeled.png")

    reg_p = R / "renders.json"
    reg = json.loads(reg_p.read_text()) if reg_p.exists() else {"files": {}}
    for stale in ("eco_gameview_figure96px.png", "eco_vignette_gamescale_96.png"):
        (R / stale).unlink(missing_ok=True)
        reg["files"].pop(stale, None)
    for f in sorted(R.glob("*.png")):
        if f.name in reg["files"] and reg["files"][f.name].get("shot") != "postprocess":
            continue
        reg["files"][f.name] = {"sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "shot": "postprocess",
                                "engine": "PIL"}
    reg["postprocess_stats"] = stats
    reg_p.write_text(json.dumps(reg, indent=1, sort_keys=True))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
