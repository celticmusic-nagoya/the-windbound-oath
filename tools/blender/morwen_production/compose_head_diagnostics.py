"""Compose MORWEN-HEAD-STRUCTURE-01 diagnostic renders into labelled contact sheets (Pillow only).

Reads render_output/morwen_head_structure/HEAD_DIAGNOSTIC_RENDER_QA.json and writes
  SHEET_<pass>.png        front | right | back | left for one pass
  HEAD_DIAGNOSTIC_OVERVIEW.png   every pass as one row
Sheets are derived evidence only; every input PNG keeps its own SHA-256 in SHEETS.json.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(os.environ.get("MORWEN_OUT", sys.argv[1] if len(sys.argv) > 1 else "render_output/morwen_head_structure"))
VIEWS = ("front", "right", "back", "left")
BG = (236, 236, 232, 255)
CELL = 384
LABEL_H = 22
MANIFEST = Path(os.environ.get("MORWEN_LAYER0_MANIFEST",
                               "tools/blender/production_mesh_08/layer0_reference_manifest.json"))
# head-only crop of the 384x1024 Layer 0 sheets; qualitative, NOT calibrated to the 3D camera
REF_CROP = (0, 0, 384, 300)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tile(path):
    im = Image.open(path).convert("RGBA").resize((CELL, CELL), Image.LANCZOS)
    base = Image.new("RGBA", (CELL, CELL), BG)
    base.alpha_composite(im)
    # fixed centre cross: every view shares the same camera anchor
    d = ImageDraw.Draw(base)
    c = CELL // 2
    d.line([(c - 6, c), (c + 6, c)], fill=(120, 120, 120, 255))
    d.line([(c, c - 6), (c, c + 6)], fill=(120, 120, 120, 255))
    return base


def row(pass_name):
    img = Image.new("RGBA", (CELL * 4, CELL + LABEL_H), BG)
    d = ImageDraw.Draw(img)
    for i, v in enumerate(VIEWS):
        img.alpha_composite(tile(OUT / pass_name / f"{v}.png"), (i * CELL, LABEL_H))
        d.text((i * CELL + 6, 5), f"{pass_name} / {v}", fill=(20, 20, 20, 255))
    return img


def canonical_row(info):
    """Head crops of the protected Layer 0 four-view references (read-only, SHA verified)."""
    if not MANIFEST.is_file():
        info["canonical_layer0"] = "MANIFEST_MISSING"
        return None
    man = json.loads(MANIFEST.read_text())
    root = MANIFEST.parent / "references"
    by_view = {i["view"]: i for i in man["images"]}
    img = Image.new("RGBA", (CELL * 4, CELL + LABEL_H), BG)
    d = ImageDraw.Draw(img)
    checks = {}
    for i, v in enumerate(VIEWS):
        meta = by_view[v]
        f = root / meta["filename"]
        actual = sha(f)
        checks[meta["filename"]] = {"view": v, "expected": meta["sha256"], "actual": actual,
                                    "match": actual == meta["sha256"]}
        crop = Image.open(f).convert("RGBA").crop(REF_CROP)
        crop.thumbnail((CELL, CELL), Image.LANCZOS)
        cell = Image.new("RGBA", (CELL, CELL), BG)
        cell.alpha_composite(crop, ((CELL - crop.width) // 2, (CELL - crop.height) // 2))
        img.alpha_composite(cell, (i * CELL, LABEL_H))
        d.text((i * CELL + 6, 5), f"canonical Layer0 {meta['filename']} / {v} (uncalibrated crop)",
               fill=(20, 20, 20, 255))
    info["canonical_layer0"] = checks
    assert all(c["match"] for c in checks.values()), "Layer 0 reference SHA mismatch"
    return img


def main():
    qa = json.loads((OUT / "HEAD_DIAGNOSTIC_RENDER_QA.json").read_text())
    passes = list(dict.fromkeys(r["pass"] for r in qa["renders"]))
    rows, info = [], {"inputs": {}, "sheets": {}}
    ref = canonical_row(info)
    if ref is not None:
        cmp_rows = [ref, row("clay"), row("original")]
        cmp = Image.new("RGB", (CELL * 4, sum(r.height for r in cmp_rows)), BG[:3])
        y = 0
        for r in cmp_rows:
            cmp.paste(r.convert("RGB"), (0, y))
            y += r.height
        dst = OUT / "HEAD_VS_CANONICAL_LAYER0_UNCALIBRATED.png"
        cmp.save(dst)
        info["sheets"][dst.name] = sha(dst)
    for p in passes:
        for v in VIEWS:
            f = OUT / p / f"{v}.png"
            info["inputs"][f"{p}/{v}.png"] = sha(f)
        r = row(p)
        dst = OUT / f"SHEET_{p}.png"
        r.convert("RGB").save(dst)
        info["sheets"][dst.name] = sha(dst)
        rows.append(r)
    ov = Image.new("RGB", (CELL * 4, sum(r.height for r in rows)), BG[:3])
    y = 0
    for r in rows:
        ov.paste(r.convert("RGB"), (0, y))
        y += r.height
    dst = OUT / "HEAD_DIAGNOSTIC_OVERVIEW.png"
    ov.save(dst)
    info["sheets"][dst.name] = sha(dst)
    (OUT / "SHEETS.json").write_text(json.dumps(info, indent=2) + "\n")
    print("sheets:", len(info["sheets"]))


if __name__ == "__main__":
    main()
