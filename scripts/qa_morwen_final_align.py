#!/usr/bin/env python3
"""MORWEN-REAL-CANON-FINAL-ALIGN-01 technical QA (read-only on assets).

Usage: python3 scripts/qa_morwen_final_align.py [--write]
  --write  also writes comparison_4directions.png and MANIFEST.json into the candidate dir.
Visual judgements (identity, design, rendering density) are in QA_REPORT.md, not here.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "assets/candidates/morwen/real-canon-final-align-01"
sys.path.insert(0, str(ROOT / "scripts/morwen_final_align"))
import colormatch as cm  # noqa: E402

DIRS = ("front", "right", "back", "left")
AX, AY = 600, 1540
TOL = 4
REF = ROOT / "assets/official/characters/morwen/hd-v2/originals/real"
SOURCES = {"front": REF / "front.png", "right": REF / "right.png",
           "back": DIR / "source/morwen_back_provided_20261111_blackbg.png",
           "left": DIR / "source/morwen_left_provided_20261111_blackbg.png"}
SOURCE_SHA = {"front": "f9a0272c99059480", "right": "b435dde0b048b1d4",
              "back": "6cc28f0056afa7ca", "left": "3492dc1c8949dde4"}
# colour tolerance against the front+right reference, per material class
TOL_L, TOL_C = 3.0, 0.10


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def runs(row):
    xs = np.nonzero(row)[0]
    if not len(xs):
        return []
    out, s, q = [], xs[0], xs[0]
    for x in xs[1:]:
        if x != q + 1:
            out.append((int(s), int(q)))
            s = x
        q = x
    out.append((int(s), int(q)))
    return out


def skin_stats(a):
    from scipy import ndimage as ndi
    from skimage import color
    lab = color.rgb2lab(a[..., :3] / 255.0)
    sk = (a[..., 3] >= 250) & (lab[..., 0] > 65) & (lab[..., 1] > 4) & (lab[..., 1] < 24) & (lab[..., 2] > 0) & (lab[..., 2] < 18)
    sk = ndi.binary_opening(sk, iterations=1)
    lb, n = ndi.label(sk)
    sz = ndi.sum(sk, lb, range(1, n + 1))
    keep = np.isin(lb, np.nonzero(sz >= 300)[0] + 1)
    v = lab[keep]
    return float(v[:, 0].mean()), float(np.hypot(v[:, 1], v[:, 2]).mean()), int(keep.sum())


def class_stats(path):
    a, lab, hsv = cm.prep(str(path))
    m = a[..., 3] >= 240
    res = {}
    for name, rh, rl in cm.CLS:
        st = cm.stats(lab, cm.weights(lab, hsv, rh, rl), m)
        if st:
            res[name] = st
    return res


def main(argv):
    rows = []

    def rec(check, result, detail=""):
        rows.append({"check": check, "result": result, "detail": detail})

    for d in DIRS:
        rec(f"source sha {d}", "PASS" if sha(SOURCES[d]).startswith(SOURCE_SHA[d]) else "FAIL", sha(SOURCES[d]))
    finals = {}
    for d in DIRS:
        p = DIR / f"morwen_{d}_final.png"
        im = Image.open(p)
        rec(f"size+mode {d}", "PASS" if (im.mode, im.size) == ("RGBA", (1200, 1600)) else "FAIL", f"{im.mode} {im.size}")
        a = np.asarray(im)
        al = a[..., 3]
        border = int(max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max()))
        rec(f"transparent border / not cut {d}", "PASS" if border == 0 else "FAIL", f"border alpha max {border}")
        stray = int(((al > 0) & (al <= 12)).sum())
        rec(f"no faint specks (alpha 1-12) {d}", "PASS" if stray == 0 else "FAIL", f"{stray} px")
        from scipy import ndimage as ndi
        lab, _ = ndi.label(al > 0, structure=np.ones((3, 3)))
        sz = np.bincount(lab.ravel()); sz[0] = 0
        detached = int(((lab != sz.argmax()) & (al > 0)).sum())
        haze = int(((al > 0) & (ndi.distance_transform_edt(al < 128) > 2)).sum())
        # limits = level of the official front/right originals (2 / 77 px)
        rec(f"cut-out residue {d}", "PASS" if detached <= 5 and haze <= 100 else "FAIL",
            f"detached px {detached} (<=5); faint px >2px outside the outline {haze} (<=100)")
        finals[d] = a

    # ground contact: every contact segment (two boots, or heel + forefoot) must reach the ground line
    for d in DIRS:
        al = finals[d][..., 3] >= 128
        bottom = int(np.nonzero(al.any(1))[0].max())
        segs = [r for r in runs(al[bottom - 6, 470:740]) if r[1] - r[0] > 12]
        segs = [(x0 + 470, x1 + 470) for x0, x1 in segs]
        lows = [int(np.nonzero(al[:, x0:x1 + 1].any(1))[0].max()) for x0, x1 in segs]
        cx = (segs[0][0] + segs[-1][1]) / 2 if segs else -1
        ok = (abs(bottom - AY) <= 1 and len(segs) >= 2 and all(AY - l <= TOL for l in lows) and abs(cx - AX) <= TOL)
        rec(f"ground contact {d}", "PASS" if ok else "FAIL",
            f"bottom {bottom}; contact segments {segs} lowest rows {lows}; support centre x {cx} (anchor {AX},{AY}, tol {TOL})")

    # colour: back/left classes vs pooled front+right reference
    ref = [class_stats(DIR / f"morwen_{d}_final.png") for d in ("front", "right")]
    pooled = {}
    for name in {k for r in ref for k in r}:
        acc = [r[name] for r in ref if name in r]
        n = sum(s["n"] for s in acc)
        pooled[name] = {k: sum(s[k] * s["n"] for s in acc) / n for k in ("mL", "mC")}
    for d in ("back", "left"):
        for when, path in (("before", None), ("after", DIR / f"morwen_{d}_final.png")):
            if path is None:
                continue
            st = class_stats(path)
            bad, det = [], []
            for name, r in sorted(pooled.items()):
                # green: too few pixels for stable stats; skin: the hue class also catches orange-gold
                # highlights, so skin is measured separately on face/hand regions (skin_stats)
                if name not in st or name in ("green", "skin"):
                    continue
                dl = st[name]["mL"] - r["mL"]
                cr = st[name]["mC"] / r["mC"] - 1
                det.append(f"{name} dL{dl:+.1f} dC{cr * 100:+.0f}%")
                if abs(dl) > TOL_L or abs(cr) > TOL_C:
                    bad.append(name)
            rec(f"colour vs front/right {d}", "PASS" if not bad else "FAIL", "; ".join(det) + (f" | out of tolerance: {bad}" if bad else ""))

    # cape panels (purple cloth) region-to-region, canvas coords; legs excluded in front/back
    def cape(d):
        a, lab, hsv = cm.prep(str(DIR / f"morwen_{d}_final.png"))
        mm = np.zeros(a.shape[:2], bool); mm[980:1370, 140:1100] = True
        if d in ("front", "back"):
            mm[:, 515:690] = False
        return cm.stats(lab, cm.weights(lab, hsv, (275, 325), (0, 101)), (a[..., 3] >= 240) & mm)
    cf, cr_ = cape("front"), cape("right")
    for d in ("back", "left"):
        c = cape(d)
        okL = min(abs(c["mL"] - cf["mL"]), abs(c["mL"] - cr_["mL"])) <= TOL_L
        okC = min(abs(c["mC"] / cf["mC"] - 1), abs(c["mC"] / cr_["mC"] - 1)) <= TOL_C
        rec(f"cape purple vs front or right {d}", "PASS" if okL and okC else "FAIL",
            f"L {c['mL']:.1f} C {c['mC']:.1f} (front L {cf['mL']:.1f} C {cf['mC']:.1f}; right L {cr_['mL']:.1f} C {cr_['mC']:.1f})")

    ref_sk = [skin_stats(finals[d]) for d in ("front", "right")]
    rL = sum(r[0] * r[2] for r in ref_sk) / sum(r[2] for r in ref_sk)
    rC = sum(r[1] * r[2] for r in ref_sk) / sum(r[2] for r in ref_sk)
    for d in ("back", "left"):
        L, C, n = skin_stats(finals[d])
        ok = abs(L - rL) <= TOL_L and abs(C / rC - 1) <= TOL_C
        rec(f"skin (face/hands) vs front/right {d}", "PASS" if ok else "FAIL", f"L {L:.1f} vs {rL:.1f}, C {C:.1f} vs {rC:.1f}, {n} px")

    # protected files
    reg = json.loads((ROOT / "data/morwen-hd-canonical-v2.json").read_text(encoding="utf-8"))
    bad = [k for k, v in reg["assets"].items() if sha(ROOT / v["path"]) != v["sha256"]]
    rec("registered canonical originals unchanged", "PASS" if not bad else "FAIL", ",".join(bad) or f"{len(reg['assets'])} files")
    v3 = json.loads((ROOT / "assets/candidates/morwen/real-canon-v3/MANIFEST_V3.json").read_text(encoding="utf-8"))
    bad3 = [f["filename"] for f in v3["files"] if sha(ROOT / "assets/candidates/morwen/real-canon-v3" / f["filename"]) != f["sha256"]]
    rec("v3 candidates unchanged", "PASS" if not bad3 else "FAIL", ",".join(bad3) or "4 files")
    v2 = json.loads((ROOT / "assets/candidates/morwen/real-canon-v2/DELIVERY_MANIFEST_V2.json").read_text(encoding="utf-8"))
    bad2 = [f["direction"] for f in v2["files"] if sha(ROOT / f"assets/candidates/morwen/real-canon-v2/morwen_real_{f['direction']}_normalized_v2.png") != f["output_sha256"]]
    rec("v2 candidates unchanged", "PASS" if not bad2 else "FAIL", ",".join(bad2) or "4 files")

    if "--write" in argv:
        write_outputs(finals)
    man_p = DIR / "MANIFEST.json"
    if man_p.exists():
        man = json.loads(man_p.read_text(encoding="utf-8"))
        badm = [f["file"] for f in man["files"] if sha(DIR / f["file"]) != f["sha256"]]
        rec("MANIFEST.json sha256", "PASS" if not badm else "FAIL", ",".join(badm) or f"{len(man['files'])} files")

    fails = [r for r in rows if r["result"] == "FAIL"]
    rep = {"task": "MORWEN-REAL-CANON-FINAL-ALIGN-01", "result": "FAIL" if fails else "PASS",
           "checks": len(rows), "fail_count": len(fails), "rows": rows,
           "not_run": ["human third-party QA", "Android device", "in-game scale"]}
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 1 if fails else 0


def write_outputs(finals):
    # comparison: row 1 = inputs placed at native scale on the ground line; row 2 = finals; two backgrounds
    th = (400, 533)
    sheet = Image.new("RGB", (4 * th[0], 3 * th[1] + 60), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    labels = {"front": "FRONT (official)", "right": "RIGHT (official)", "back": "BACK (provided 11/11)", "left": "LEFT (provided 11/11)"}
    for i, d in enumerate(DIRS):
        src = Image.open(SOURCES[d]).convert("RGBA")
        if d in ("back", "left"):  # black background shown as delivered
            pass
        c = Image.new("RGBA", (1200, 1600), (255, 255, 255, 255))
        c.alpha_composite(src, ((1200 - src.width) // 2, 1540 - src.height + 26))
        sheet.paste(c.convert("RGB").resize(th, Image.LANCZOS), (i * th[0], 30))
        for r, col in ((1, (255, 255, 255)), (2, (34, 34, 42))):
            bg = Image.new("RGBA", (1200, 1600), col + (255,))
            bg.alpha_composite(Image.fromarray(finals[d], "RGBA"))
            t = bg.convert("RGB").resize(th, Image.LANCZOS)
            td = ImageDraw.Draw(t)
            y = round(1540 * th[1] / 1600)
            td.line([(0, y), (th[0], y)], fill=(230, 0, 0))
            x = round(600 * th[0] / 1200)
            td.line([(x - 10, y - 6), (x - 10 + 20, y - 6)], fill=(230, 0, 0))
            sheet.paste(t, (i * th[0], 30 + r * th[1]))
        dr.text((i * th[0] + 8, 8), labels[d], fill=(0, 0, 0))
    dr.text((8, 30 + 3 * th[1] + 10), "row 1: inputs (back/left delivered on black)  rows 2-3: finals, 1200x1600, anchor (600,1540) red line", fill=(0, 0, 0))
    sheet.save(DIR / "comparison_4directions.png", optimize=True)
    files = [f"morwen_{d}_final.png" for d in DIRS] + ["comparison_4directions.png", "QA_REPORT.md"]
    meta = json.loads((DIR / "compose_meta.json").read_text(encoding="utf-8"))
    man = {"task": "MORWEN-REAL-CANON-FINAL-ALIGN-01", "status": "CANDIDATE_NOT_PRODUCTION", "canvas": [1200, 1600], "anchor": [AX, AY],
           "files": [{"file": f, "sha256": sha(DIR / f)} for f in files if (DIR / f).exists()],
           "sources": {d: {"path": str(SOURCES[d].relative_to(ROOT)), "sha256": sha(SOURCES[d])} for d in DIRS},
           "processing": meta}
    (DIR / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
