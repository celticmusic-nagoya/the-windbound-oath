#!/usr/bin/env python3
"""MORWEN-REAL-CANON-FINAL-04 mechanical QA (read-only on assets).

Usage: python3 scripts/qa_morwen_final04.py [--write]
  --write  regenerates FOUR_DIRECTION_COMPARISON.png and MANIFEST.json in the candidate dir.
Design/visual judgements are recorded in QA_REPORT.md (visual QA), separate from this script.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import qa_morwen_final_align as fa  # noqa: E402  (reuses colour/skin helpers)

DIR = ROOT / "assets/candidates/morwen/real-canon-final-04"
CANON_BACK = DIR / "morwen_back_final_canonical.png"
CANON_BACK_SHA = "f3e640782e2d24f782d9b729d47fff65cbce01057f60e3aaec639deb6679eea2"
OFF = ROOT / "assets/official/characters/morwen/hd-v2/originals/real"
RAW = {"front": OFF / "front.png", "right": OFF / "right.png", "back": CANON_BACK, "left": OFF / "left.png"}
DIRS = ("front", "right", "back", "left")
AX, AY, TOL = 600, 1540, 4
# landmark rows measured on the aligned images (visual reading, +-5 px); see QA_REPORT.md
# boot top after FIX-01 (visual reading at 3x, rim top at the boot centre line)
FIX01_BOOT_TOP = {"right": 1270, "back": 1270, "left": 1271}
# (side views: top edge of the band/cuff where it crosses the leg's centre line; perspective adds ~+-5 px)
LANDMARKS = {"sock_top": {"front": 905, "right": 924, "back": 908, "left": 911},
             "boot_top": {"front": 1270, "right": 1280, "back": 1295, "left": 1289}}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv):
    rows = []

    def rec(c, r, d=""):
        rows.append({"check": c, "result": r, "detail": d})

    # 1. canonical back preserved byte-for-byte + real transparency
    rec("canonical back sha256", "PASS" if sha(CANON_BACK) == CANON_BACK_SHA else "FAIL", sha(CANON_BACK))
    im = Image.open(CANON_BACK)
    a = np.asarray(im.convert("RGBA")).astype(int)
    al = a[..., 3]
    rec("canonical back format", "PASS" if (im.mode, im.size) == ("RGBA", (1024, 1536)) else "FAIL", f"{im.mode} {im.size}")
    border = int(max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max()))
    rec("canonical back background alpha = 0", "PASS" if border == 0 and (al == 0).mean() > 0.4 else "FAIL",
        f"alpha-0 share {(al == 0).mean():.3f}, border alpha max {border}, max alpha {al.max()}")
    outer = (al > 0) & (ndi.distance_transform_edt(al < 128) > 0)
    L = a[..., :3].mean(-1)
    white = int((outer & (L > 235)).sum())
    # checkerboard test: alternating light/grey blocks in the alpha>0 outer band
    rec("canonical back no white/checker pixels in the outline band", "PASS" if white == 0 else "FAIL", f"near-white outline px {white}")
    faint = int(((al > 0) & (al <= 12)).sum())
    lab, _ = ndi.label(al > 0, structure=np.ones((3, 3)))
    sz = np.bincount(lab.ravel()); sz[0] = 0
    det = int(((lab != sz.argmax()) & (al > 0)).sum())
    rec("canonical back faint haze / detached specks (info)", "INFO",
        f"alpha 1-12 px {faint}; detached px {det}. Invisible, but trimmed in the aligned derivative; the canonical file is kept unmodified.")

    cl = DIR / "morwen_back_final_canonical_alpha_clean.png"
    c = np.asarray(Image.open(cl).convert("RGBA")).astype(int)
    ca = c[..., 3]
    cb = int(max(ca[0].max(), ca[-1].max(), ca[:, 0].max(), ca[:, -1].max()))
    vis = (al > 12)
    same_rgb = bool(np.array_equal(c[..., :3][ca > 0], a[..., :3][ca > 0]))
    same_alpha_vis = bool(np.array_equal(ca[ca > 0], al[ca > 0]))
    rec("alpha-clean back: background alpha = 0, visible pixels unchanged",
        "PASS" if cb == 0 and not ((ca > 0) & (ca <= 12)).any() and same_rgb and same_alpha_vis else "FAIL",
        f"border {cb}; alpha 1-12 px {int(((ca > 0) & (ca <= 12)).sum())}; kept pixels RGB/alpha identical={same_rgb and same_alpha_vis}; removed px {int((vis & (ca == 0)).sum())} with alpha>12 (detached specks)")

    # 2. aligned derivatives
    fin = {}
    for d in DIRS:
        p = DIR / "aligned" / f"morwen_{d}_aligned.png"
        im = Image.open(p)
        x = np.asarray(im)
        A = x[..., 3]
        rec(f"aligned {d} format", "PASS" if (im.mode, im.size) == ("RGBA", (1200, 1600)) else "FAIL", f"{im.mode} {im.size}")
        b = int(max(A[0].max(), A[-1].max(), A[:, 0].max(), A[:, -1].max()))
        lab, _ = ndi.label(A > 0, structure=np.ones((3, 3)))
        sz = np.bincount(lab.ravel()); sz[0] = 0
        det = int(((lab != sz.argmax()) & (A > 0)).sum())
        haze = int(((A > 0) & (ndi.distance_transform_edt(A < 128) > 2)).sum())
        rec(f"aligned {d} transparency/edges", "PASS" if b == 0 and det <= 5 and haze <= 100 and not ((A > 0) & (A <= 12)).any() else "FAIL",
            f"border {b}; detached {det}; faint >2px outside {haze}")
        fin[d] = x
        m = A >= 128
        bot = int(np.nonzero(m.any(1))[0].max())
        segs = [(s + 470, e + 470) for s, e in fa.runs(m[bot - 6, 470:740]) if e - s > 12]
        lows = [int(np.nonzero(m[:, s:e + 1].any(1))[0].max()) for s, e in segs]
        cx = (segs[0][0] + segs[-1][1]) / 2
        ok = abs(bot - AY) <= 1 and len(segs) >= 2 and all(AY - l <= TOL for l in lows) and abs(cx - AX) <= TOL
        rec(f"ground contact {d}", "PASS" if ok else "FAIL", f"segments {segs} lowest {lows}; sole-span centre {cx}")
        if d in ("right", "left"):
            mids = (segs[0][1] + segs[-1][0]) / 2
            rec(f"ground contact {d} heel/forefoot midpoint (info)", "INFO", f"midpoint x {mids} (offset {mids - AX:+.1f})")

    # 3. proportions (landmark rows) against front
    for k, v in LANDMARKS.items():
        for d in ("right", "back", "left"):
            r = (AY - v[d]) / (AY - v["front"]) - 1
            rec(f"baseline {k} height vs front {d}", "PASS" if abs(r) <= 0.03 else "FAIL", f"row {v[d]} vs {v['front']} ({r * 100:+.1f}% of sole distance)")

    # 4. colour (aligned derivatives; back/left vs front/right)
    ref = [fa.class_stats(DIR / "aligned" / f"morwen_{d}_aligned.png") for d in ("front", "right")]
    pooled = {}
    for name in {k for r in ref for k in r}:
        acc = [r[name] for r in ref if name in r]
        n = sum(s["n"] for s in acc)
        pooled[name] = {k: sum(s[k] * s["n"] for s in acc) / n for k in ("mL", "mC")}
    for d in ("back", "left"):
        for label, path in (("raw", RAW[d]), ("aligned", DIR / "aligned" / f"morwen_{d}_aligned.png")):
            st = fa.class_stats(path)
            det, bad = [], []
            for name, r in sorted(pooled.items()):
                if name not in st or name in ("green", "skin"):
                    continue
                dl = st[name]["mL"] - r["mL"]; cr = st[name]["mC"] / r["mC"] - 1
                det.append(f"{name} dL{dl:+.1f} dC{cr * 100:+.0f}%")
                if abs(dl) > fa.TOL_L or abs(cr) > fa.TOL_C:
                    bad.append(name)
            res = ("PASS" if not bad else "FAIL") if label == "aligned" else "INFO"
            rec(f"baseline colour {label} {d} vs front/right", res, "; ".join(det) + (f" | out: {bad}" if bad else ""))
    rsk = [fa.skin_stats(fin[d]) for d in ("front", "right")]
    rL = sum(r[0] * r[2] for r in rsk) / sum(r[2] for r in rsk); rC = sum(r[1] * r[2] for r in rsk) / sum(r[2] for r in rsk)
    for d in ("back", "left"):
        L_, C_, n = fa.skin_stats(fin[d])
        rec(f"baseline skin {d}", "PASS" if abs(L_ - rL) <= fa.TOL_L and abs(C_ / rC - 1) <= fa.TOL_C else "FAIL", f"L {L_:.1f} vs {rL:.1f}; C {C_:.1f} vs {rC:.1f}; {n} px")

    # 4b. FIX-01 candidates (boot raise + colour fine-tune), back and left
    FIX = DIR / "fix01"
    BOOT = {"right": (512, 640), "back": (510, 690), "left": (505, 688)}
    fixed = {"front": fin["front"]}
    for d in ("right", "back", "left"):
        p = FIX / f"morwen_{d}_fix01.png"
        im = Image.open(p); x = np.asarray(im); A = x[..., 3]
        fixed[d] = x
        b = int(max(A[0].max(), A[-1].max(), A[:, 0].max(), A[:, -1].max()))
        rec(f"fix01 {d} format/border", "PASS" if (im.mode, im.size) == ("RGBA", (1200, 1600)) and b == 0 else "FAIL", f"{im.mode} {im.size} border {b}")
        prev = fin[d][..., 3]
        x0, x1 = BOOT[d]
        outside = np.ones(A.shape, bool); outside[1240:1440, x0:x1] = False
        same_out = bool(np.array_equal(A[outside], prev[outside]))
        same_low = bool(np.array_equal(A[1440:], prev[1440:]))
        rec(f"fix01 {d} geometry only changed inside the boot box", "PASS" if same_out and same_low else "FAIL",
            f"alpha identical outside box x{x0}-{x1} y1240-1439: {same_out}; rows >= 1440 (lower strap, heel, sole): {same_low}")
        m = A >= 128
        bot = int(np.nonzero(m.any(1))[0].max())
        rec(f"fix01 {d} ground row", "PASS" if bot == AY else "FAIL", f"lowest solid row {bot}")
    for d, row in FIX01_BOOT_TOP.items():
        r = (AY - row) / (AY - LANDMARKS["boot_top"]["front"]) - 1
        rec(f"fix01 boot_top vs front {d}", "PASS" if abs(r) <= 0.03 else "FAIL", f"row {row} (was {LANDMARKS['boot_top'][d]}) vs front {LANDMARKS['boot_top']['front']} ({r * 100:+.1f}%)")
    for d in ("back", "left"):
        st = fa.class_stats(FIX / f"morwen_{d}_fix01.png")
        det, bad = [], []
        for name, r in sorted(pooled.items()):
            if name not in st or name in ("green", "skin"):
                continue
            dl = st[name]["mL"] - r["mL"]; cr = st[name]["mC"] / r["mC"] - 1
            det.append(f"{name} dL{dl:+.1f} dC{cr * 100:+.0f}%")
            if abs(dl) > fa.TOL_L or abs(cr) > fa.TOL_C:
                bad.append(name)
        rec(f"fix01 colour {d} vs front/right", "PASS" if not bad else "FAIL", "; ".join(det) + (f" | out: {bad}" if bad else ""))
        L_, C_, n = fa.skin_stats(fixed[d])
        rec(f"fix01 skin {d}", "PASS" if abs(L_ - rL) <= fa.TOL_L and abs(C_ / rC - 1) <= fa.TOL_C else "FAIL", f"L {L_:.1f} vs {rL:.1f}; C {C_:.1f} vs {rC:.1f}")
    globals()["_FIXED"] = fixed

    # 5. protected files
    reg = json.loads((ROOT / "data/morwen-hd-canonical-v2.json").read_text(encoding="utf-8"))
    bad = [k for k, v in reg["assets"].items() if sha(ROOT / v["path"]) != v["sha256"]]
    rec("registered canonical originals unchanged", "PASS" if not bad else "FAIL", ",".join(bad) or f"{len(reg['assets'])} files")
    for sub, manf, key in (("real-canon-v3", "MANIFEST_V3.json", "filename"), ("real-canon-final-align-01", "MANIFEST.json", "file")):
        man = json.loads((ROOT / "assets/candidates/morwen" / sub / manf).read_text(encoding="utf-8"))
        badm = [f[key] for f in man["files"] if sha(ROOT / "assets/candidates/morwen" / sub / f[key]) != f["sha256"]]
        rec(f"{sub} unchanged", "PASS" if not badm else "FAIL", ",".join(badm) or f"{len(man['files'])} files")

    if "--write" in argv:
        write_fix01(globals()["_FIXED"])
        write(fin)
    mp = DIR / "MANIFEST.json"
    if mp.exists():
        man = json.loads(mp.read_text(encoding="utf-8"))
        badm = [f["file"] for f in man["files"] if sha(DIR / f["file"]) != f["sha256"]]
        rec("MANIFEST.json sha256", "PASS" if not badm else "FAIL", ",".join(badm) or f"{len(man['files'])} files")
    fails = [r for r in rows if r["result"] == "FAIL"]
    cur = [r for r in fails if not r["check"].startswith("baseline") and r["check"] != "canonical back background alpha = 0"]
    out = {"task": "MORWEN-REAL-CANON-FINAL-04 (+FIX-01)", "scope": "mechanical QA only", "result": "FAIL" if fails else "PASS",
           "result_fix01_set": "FAIL" if cur else "PASS",
           "note": "'baseline' rows = FINAL-04 aligned set before FIX-01 (kept as history); the raw canonical back is kept as received and its alpha-clean copy is checked separately",
           "checks": len([r for r in rows if r["result"] != "INFO"]), "fail_count": len(fails), "rows": rows,
           "not_run": ["human third-party QA", "Android device", "in-game scale"]}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 1 if fails else 0


def write_fix01(fixed):
    th = (360, 480)
    labels = ("FRONT official", "RIGHT fix01", "BACK fix01", "LEFT fix01")
    sheet = Image.new("RGB", (4 * th[0], th[1] + 300 + 60), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    for i, d in enumerate(DIRS):
        img = Image.new("RGBA", (1200, 1600), (255, 255, 255, 255))
        img.alpha_composite(Image.fromarray(fixed[d], "RGBA"))
        t = img.convert("RGB").resize(th, Image.LANCZOS)
        td = ImageDraw.Draw(t)
        for y, col in ((AY, (220, 0, 0)), (1270, (0, 110, 255)), (905, (0, 160, 0))):
            yy = round(y * th[1] / 1600); td.line([(0, yy), (th[0], yy)], fill=col)
        sheet.paste(t, (i * th[0], 24))
        z = img.crop((460, 1230, 740, 1545)).convert("RGB").resize((th[0], 300 * 1), Image.LANCZOS)
        zd = ImageDraw.Draw(z); yy = round((1270 - 1230) * 300 / 315); zd.line([(0, yy), (th[0], yy)], fill=(0, 110, 255))
        sheet.paste(z, (i * th[0], 24 + th[1]))
        dr.text((i * th[0] + 6, 6), labels[i], fill=(0, 0, 0))
    dr.text((6, 24 + th[1] + 300 + 10), "top: 4 directions after FIX-01; bottom: boots zoom. blue = front boot top 1270, red = ground 1540, green = sock top 905", fill=(0, 0, 0))
    sheet.save(DIR / "FOUR_DIRECTION_COMPARISON_FIX01.png", optimize=True)


def write(fin, name="FOUR_DIRECTION_COMPARISON.png", label2=None):
    """Baseline comparison (originals vs aligned) + MANIFEST.json."""
    th = (360, 480)
    labels = ("FRONT official", "RIGHT official", "BACK canonical 11/11", "LEFT official")
    sheet = Image.new("RGB", (4 * th[0], 2 * th[1] + 70), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    for i, d in enumerate(DIRS):
        raw = Image.open(RAW[d]).convert("RGBA")
        meta = json.loads((DIR / "aligned/PROCESSING.json").read_text(encoding="utf-8"))[d]
        c = Image.new("RGBA", (1200, 1600), (255, 255, 255, 255))
        ox, oy = meta["offset"]
        c.alpha_composite(raw.crop((max(0, -ox), max(0, -oy), raw.width, raw.height)), (max(0, ox), max(0, oy)))
        for r, img in ((0, c), (1, None)):
            if img is None:
                img = Image.new("RGBA", (1200, 1600), (255, 255, 255, 255))
                img.alpha_composite(Image.fromarray(fin[d], "RGBA"))
            t = img.convert("RGB").resize(th, Image.LANCZOS)
            td = ImageDraw.Draw(t)
            for y, col in ((AY, (220, 0, 0)), (1270, (0, 110, 255)), (905, (0, 160, 0))):
                yy = round(y * th[1] / 1600)
                td.line([(0, yy), (th[0], yy)], fill=col)
            sheet.paste(t, (i * th[0], 24 + r * th[1]))
        dr.text((i * th[0] + 6, 6), labels[i], fill=(0, 0, 0))
    dr.text((6, 24 + 2 * th[1] + 8), "row 1: originals, translation only   " + (label2 or "row 2: aligned derivatives (colour matched to front/right; right heel fix)"), fill=(0, 0, 0))
    dr.text((6, 24 + 2 * th[1] + 26), "lines: red = ground 1540 (anchor x 600), blue = front boot top 1270, green = front sock top 905", fill=(0, 0, 0))
    sheet.save(DIR / name, optimize=True)
    files = ["morwen_back_final_canonical.png", "morwen_back_final_canonical_alpha_clean.png", "FOUR_DIRECTION_COMPARISON.png", "DESIGN_SPEC.md", "QA_REPORT.md",
             "QA_TECH_REPORT.json", "INDEPENDENT_AI_QA.md", "aligned/PROCESSING.json"] + [f"aligned/morwen_{d}_aligned.png" for d in DIRS] + \
            ["QA_REPORT_FIX01.md", "FOUR_DIRECTION_COMPARISON_FIX01.png", "fix01/morwen_right_fix01.png", "fix01/morwen_back_fix01.png", "fix01/morwen_left_fix01.png",
             "fix01/PROCESSING_FIX01.json", "fix01/EDIT_MASK_back_hair_below_395.png", "fix01/EDIT_MASK_back_hair_preview.png", "fix01/HAIR_EDIT_SPEC.md"]
    man = {"task": "MORWEN-REAL-CANON-FINAL-04", "status": "CANDIDATE_NOT_PRODUCTION",
           "canonical_back": {"file": "morwen_back_final_canonical.png", "sha256": CANON_BACK_SHA, "processing": "none (bytes as received)",
                              "format": "RGBA 1024x1536, background alpha 0 (verified)"},
           "references": {d: {"path": str(RAW[d].relative_to(ROOT)), "sha256": sha(RAW[d])} for d in DIRS},
           "display": {"canvas": [1200, 1600], "anchor": [AX, AY]},
           "files": [{"file": f, "sha256": sha(DIR / f)} for f in dict.fromkeys(files) if (DIR / f).exists() and f != "QA_TECH_REPORT.json"]}
    (DIR / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
