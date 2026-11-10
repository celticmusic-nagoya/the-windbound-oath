#!/usr/bin/env python3
"""MORWEN-REAL-CANON-V3 candidate QA (read-only). Prints a JSON report; exit 1 on FAIL.

Checks only measurable items. Visual judgements (boot contact, design consistency, fringe)
are recorded separately in docs/qa/MORWEN_REAL_CANON_V3_QA_20261110.md.
Optional: --evidence DIR writes comparison PNGs (feet zoom with anchor, 4 backgrounds).
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "assets/candidates/morwen/real-canon-v2"
V3 = ROOT / "assets/candidates/morwen/real-canon-v3"
REG = ROOT / "data/morwen-hd-canonical-v2.json"
DIRS = ("front", "right", "back", "left")
EXPECTED_MOVES = {"front": (22, -18), "right": (-96, -18), "back": (36, -18), "left": (79, -18)}
ANCHOR = (600, 1540)
TOL_X = 4      # master px (= 0.25 screen px at 1/16)
TOL_Y = 4
# Contact segments in v3 coordinates (each must reach the ground line within TOL_Y):
# front/back = left and right boot; side views = block heel and forefoot sole.
CONTACT_SEGMENTS = {"front": ((526, 600), (602, 675)), "back": ((517, 598), (604, 684)),
                    "right": ((510, 563), (585, 691)), "left": ((511, 620), (643, 687))}
# Boot search windows (x range) chosen to exclude cape tips (v2 windows shifted by dx).
BOOT_X_V2 = {"front": (480, 700), "right": (590, 800), "back": (460, 680), "left": (420, 620)}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv):
    import numpy as np
    from PIL import Image

    rows = []

    def rec(name, result, detail=""):
        rows.append({"check": name, "result": result, "detail": detail})

    man = json.loads((V3 / "MANIFEST_V3.json").read_text(encoding="utf-8"))
    by = {f["direction"]: f for f in man["files"]}
    rec("manifest anchor target", "PASS" if tuple(man["anchor_target"]) == ANCHOR else "FAIL", str(man["anchor_target"]))
    v3 = {}
    for d in DIRS:
        f = by[d]
        p = V3 / f["filename"]
        rec(f"sha256 {d} vs MANIFEST_V3", "PASS" if sha(p) == f["sha256"] else "FAIL", f["sha256"])
        p2 = V2 / f"morwen_real_{d}_normalized_v2.png"
        rec(f"source v2 sha256 {d}", "PASS" if sha(p2) == f["source_v2_sha256"] else "FAIL", f["source_v2_sha256"])
        rec(f"move {d} matches spec", "PASS" if (f["dx"], f["dy"]) == EXPECTED_MOVES[d] else "FAIL", f"({f['dx']},{f['dy']})")
        im = Image.open(p)
        rec(f"size+mode {d}", "PASS" if (im.mode == "RGBA" and im.size == (1200, 1600)) else "FAIL", f"{im.mode} {im.size}")
        a = np.asarray(im)
        al = a[..., 3]
        border = int(max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max()))
        rec(f"transparent border / no clipping {d}", "PASS" if border == 0 else "FAIL", f"border alpha max {border}")
        b = np.asarray(Image.open(p2).convert("RGBA"))
        dx, dy = f["dx"], f["dy"]
        # pure translation: v3 == v2 shifted; nothing of v2 lost; nothing new appears
        exp = np.zeros_like(b)
        H, W = b.shape[:2]
        ys0, ys1 = max(0, dy), min(H, H + dy)
        xs0, xs1 = max(0, dx), min(W, W + dx)
        exp[ys0:ys1, xs0:xs1] = b[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        lost = int((b[..., 3] > 0).sum() - (exp[..., 3] > 0).sum())
        # compare un-premultiplied RGBA exactly where alpha>0, and alpha everywhere
        same_alpha = np.array_equal(exp[..., 3], a[..., 3])
        m = a[..., 3] > 0
        same_rgb = np.array_equal(exp[..., :3][m], a[..., :3][m])
        rec(f"pure translation of v2 {d}", "PASS" if (same_alpha and same_rgb and lost == 0) else "FAIL",
            f"alpha identical={same_alpha}, rgb identical={same_rgb}, pixels lost={lost}")
        v3[d] = a

    # anchor: ground row and boot span centre (alpha>=128)
    for d in DIRS:
        al = v3[d][..., 3]
        bottom = int(np.nonzero((al >= 128).any(1))[0].max())
        x0, x1 = (v + by[d]["dx"] for v in BOOT_X_V2[d])
        band = al[bottom - 40:bottom + 1, x0:x1] >= 128
        cols = np.nonzero(band.any(0))[0] + x0
        cx = (int(cols.min()) + int(cols.max())) / 2
        # per-boot lowest rows (sole contact) for the record
        lows = []
        for xa, xb in CONTACT_SEGMENTS[d]:
            sub = al[:, xa:xb + 1] >= 128
            lows.append(int(np.nonzero(sub.any(1))[0].max()))
        rec(f"ground row {d}", "PASS" if abs(bottom - ANCHOR[1]) <= 0 else "FAIL", f"lowest alpha>=128 row {bottom}")
        rec(f"boot contact {d}", "PASS" if (abs(cx - ANCHOR[0]) <= TOL_X and all(ANCHOR[1] - l <= TOL_Y for l in lows)) else "FAIL",
            f"boot span x {cols.min()}-{cols.max()} centre {cx}; lowest row per contact segment {dict(zip(map(str, CONTACT_SEGMENTS[d]), lows))} (tol x±{TOL_X}, y≤{TOL_Y})")

    # alpha profile (record only): body alpha 253 inherited from originals
    for d in DIRS:
        al = v3[d][..., 3]
        edge = (al > 0) & (al < 250)
        L = v3[d][..., :3].mean(-1)
        rec(f"alpha profile {d}", "INFO",
            f"max alpha {int(al.max())}; partial-alpha edge px {int(edge.sum())}; edge mean L {L[edge].mean():.1f} vs body {L[al >= 250].mean():.1f}")

    reg = json.loads(REG.read_text(encoding="utf-8"))
    bad = [k for k, v in reg["assets"].items() if sha(ROOT / v["path"]) != v["sha256"]]
    rec("registered canonical files unchanged", "PASS" if not bad else "FAIL", ",".join(bad) or f"{len(reg['assets'])} files")
    v2man = json.loads((V2 / "DELIVERY_MANIFEST_V2.json").read_text(encoding="utf-8"))
    bad2 = [f["direction"] for f in v2man["files"] if sha(V2 / f"morwen_real_{f['direction']}_normalized_v2.png") != f["output_sha256"]]
    rec("v2 candidates unchanged", "PASS" if not bad2 else "FAIL", ",".join(bad2) or "4 files")

    if "--evidence" in argv:
        out = Path(argv[argv.index("--evidence") + 1])
        out.mkdir(parents=True, exist_ok=True)
        from PIL import ImageDraw
        tiles = []
        for d in DIRS:
            im = Image.fromarray(v3[d]).crop((400, 1420, 800, 1560))
            bg = Image.new("RGBA", im.size, (150, 170, 150, 255))
            bg.alpha_composite(im)
            bg = bg.resize((im.width * 3, im.height * 3), Image.NEAREST)
            dr = ImageDraw.Draw(bg)
            ax, ay = (ANCHOR[0] - 400) * 3, (ANCHOR[1] - 1420) * 3 + 3
            dr.line([(ax, 0), (ax, bg.height)], fill=(255, 0, 0, 255))
            dr.line([(0, ay), (bg.width, ay)], fill=(0, 0, 255, 255))
            dr.text((6, 6), d, fill=(0, 0, 0, 255))
            tiles.append(bg)
        sheet = Image.new("RGBA", (tiles[0].width, sum(t.height for t in tiles)))
        y = 0
        for t in tiles:
            sheet.paste(t, (0, y))
            y += t.height
        sheet.save(out / "V3_FEET_ANCHOR_ZOOM.png", optimize=True)
        bgs = [(255, 255, 255), (40, 40, 48), (96, 140, 80), (150, 120, 90)]
        sheet = Image.new("RGBA", (1200, 1600))
        for r, col in enumerate(bgs):
            row = Image.new("RGBA", (1200, 400), col + (255,))
            dr = ImageDraw.Draw(row)
            for i, d in enumerate(DIRS):
                row.alpha_composite(Image.fromarray(v3[d]).resize((300, 400), Image.LANCZOS), (i * 300, 0))
                dr.line([(i * 300 + 140, 385), (i * 300 + 160, 385)], fill=(255, 0, 0, 255))
                dr.line([(i * 300 + 150, 378), (i * 300 + 150, 392)], fill=(255, 0, 0, 255))
            sheet.paste(row, (0, r * 400))
        sheet.save(out / "V3_LINEUP_4BG.png", optimize=True)

    fails = [r for r in rows if r["result"] == "FAIL"]
    report = {"task": "MORWEN-REAL-CANON-V3-REGISTER-01", "result": "FAIL" if fails else "PASS",
              "checks": len([r for r in rows if r["result"] != "INFO"]), "fail_count": len(fails), "rows": rows,
              "not_run": ["independent visual QA (separate document)", "human third-party QA", "Android device", "in-game scale"]}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
