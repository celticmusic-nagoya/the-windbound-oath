#!/usr/bin/env python3
"""MORWEN-REAL-CANON-V2 candidate QA (read-only). Prints a JSON report; exit 1 on FAIL.

PASS/FAIL only for measurable items. Anchor findings are reported as FAIL against the
registered display anchor (600,1540) without modifying any image.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "assets/candidates/morwen/real-canon-v2"
ORIG = ROOT / "assets/official/characters/morwen/hd-v2/originals/real"
REG = ROOT / "data/morwen-hd-canonical-v2.json"
DIRS = ("front", "right", "back", "left")
# Boot search windows (x range) chosen to exclude cape tips; measured on the delivered files.
BOOT_X = {"front": (480, 700), "right": (590, 800), "back": (460, 680), "left": (420, 620)}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    import numpy as np
    from PIL import Image

    rows = []

    def rec(name, result, detail=""):
        rows.append({"check": name, "result": result, "detail": detail})

    manifest = json.loads((CAND / "DELIVERY_MANIFEST_V2.json").read_text(encoding="utf-8"))
    by_dir = {f["direction"]: f for f in manifest["files"]}
    imgs, masks = {}, {}
    for d in DIRS:
        p = CAND / f"morwen_real_{d}_normalized_v2.png"
        ok = p.is_file() and sha(p) == by_dir[d]["output_sha256"]
        rec(f"sha256 {d}", "PASS" if ok else "FAIL", by_dir[d]["output_sha256"])
        im = Image.open(p)
        rec(f"size+mode {d}", "PASS" if (im.mode == "RGBA" and im.size == (1200, 1600)) else "FAIL", f"{im.mode} {im.size}")
        a = np.asarray(im)
        al = a[..., 3]
        corners = [int(al[0, 0]), int(al[0, -1]), int(al[-1, 0]), int(al[-1, -1])]
        border = int(max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max()))
        rec(f"transparent border {d}", "PASS" if border == 0 else "FAIL", f"corners {corners} border max {border}")
        imgs[d] = a

        def m(arr):
            msk = arr[..., 3] >= 128
            ys, xs = np.nonzero(msk)
            c = Image.fromarray((msk * 255).astype("uint8")).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
            return np.asarray(c.resize((80, 120))) > 127
        masks[d] = (m(a), m(np.asarray(Image.open(ORIG / f"{d}.png").convert("RGBA"))))

    # direction mix-up: silhouette IoU against the registered originals
    for d in DIRS:
        ious = {e: float((masks[d][0] & masks[e][1]).sum() / (masks[d][0] | masks[e][1]).sum()) for e in DIRS}
        best = max(ious, key=ious.get)
        rec(f"direction match {d}", "PASS" if best == d and ious[d] > 0.95 else "FAIL",
            "IoU " + ", ".join(f"{e}={v:.3f}" for e, v in ious.items()))

    # anchor
    bottoms, centres = {}, {}
    for d in DIRS:
        al = imgs[d][..., 3]
        bottoms[d] = int(np.nonzero((al >= 128).any(1))[0].max())
        x0, x1 = BOOT_X[d]
        cols = np.nonzero((al[bottoms[d] - 40:bottoms[d] + 1, x0:x1] >= 128).any(0))[0] + x0
        centres[d] = (int(cols.min()), int(cols.max()), (int(cols.min()) + int(cols.max())) / 2)
    same_bottom = len(set(bottoms.values())) == 1
    rec("ground row identical (alpha>=128)", "PASS" if same_bottom else "FAIL", str(bottoms))
    gx, gy = json.loads(REG.read_text(encoding="utf-8"))["display"]["ground_anchor"]
    rec("ground row vs registered anchor y", "PASS" if all(b == gy - 1 for b in bottoms.values()) else "FAIL",
        f"candidates {sorted(set(bottoms.values()))} vs registry y={gy} (manifest target_bottom_y {manifest.get('target_bottom_y')})")
    spread = max(c[2] for c in centres.values()) - min(c[2] for c in centres.values())
    rec("boot centre x vs anchor x", "PASS" if all(abs(c[2] - gx) <= 4 for c in centres.values()) else "FAIL",
        "; ".join(f"{d} {c[0]}-{c[1]} centre {c[2]}" for d, c in centres.items()) + f"; spread {spread}")

    # colour: front/right declared unchanged, back/left declared adjusted (mean of opaque pixels)
    for d in DIRS:
        o = np.asarray(Image.open(ORIG / f"{d}.png").convert("RGBA")).astype(float)
        n = imgs[d].astype(float)
        mo = o[..., :3][o[..., 3] >= 250].mean(0)
        mn = n[..., :3][n[..., 3] >= 250].mean(0)
        delta = float(np.abs(mo - mn).max())
        declared = by_dir[d]["color_adjusted"]
        ok = (delta > 2) if declared else (delta <= 1.0)
        rec(f"colour adjustment matches manifest {d}", "PASS" if ok else "FAIL",
            f"declared color_adjusted={declared}; mean RGB original {mo.round(1).tolist()} v2 {mn.round(1).tolist()}")

    # originals untouched
    reg = json.loads(REG.read_text(encoding="utf-8"))
    bad = [k for k, v in reg["assets"].items() if sha(ROOT / v["path"]) != v["sha256"]]
    rec("registered canonical files unchanged", "PASS" if not bad else "FAIL", ",".join(bad) or f"{len(reg['assets'])} files")

    fails = [r for r in rows if r["result"] == "FAIL"]
    report = {"task": "MORWEN-REAL-CANON-V2-UPLOAD-01", "result": "FAIL" if fails else "PASS",
              "checks": len(rows), "fail_count": len(fails), "rows": rows,
              "not_verified": ["full-silhouette halo inspection", "design equivalence at detail level (strap path, vials)",
                               "perceptual colour equivalence", "independent QA", "Android device", "in-game scale"]}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
