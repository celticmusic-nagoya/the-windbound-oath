#!/usr/bin/env python3
"""Build the Morwen Layer0 hair precision blueprint (2D design stage) from the verified four-view originals.

usage: build_l0_hair_blueprint.py SRC_DIR OUT_DIR
SRC_DIR holds 7807-7810.png from artifact 14602858760 (verified by SHA-256 before use; never copied into the repo).
Writes morwen_hair_l0_blueprint_v1.json next to this script; diagrams to OUT_DIR. Diagrams that contain source pixels
(overlays) are marked "contains_source_pixels" and are not committed (public repository; publication needs approval).
No 3D value is asserted: depth, scalp, thickness and the top view are ESTIMATED or HOLD."""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from observed_locks_l0 import LOCKS, POINTS, VIEWS  # noqa: E402

HEAD_H_PX = 180 - 18  # front crown (208,18) to chin (214,180): layer0_landmarks_v1, unc 2 px / 3 px
REGION_DEFAULTS = {  # ESTIMATED sections (not visible in 2D): thickness/width ratio at mid, taper tip/mid, layer order
    "fringe": {"aspect_mid": (0.25, 0.10), "taper": (0.35, 0.15), "layer": 4},
    "temple": {"aspect_mid": (0.35, 0.12), "taper": (0.40, 0.15), "layer": 3},
    "flick": {"aspect_mid": (0.60, 0.20), "taper": (0.30, 0.15), "layer": 3},
    "side": {"aspect_mid": (0.45, 0.15), "taper": (0.45, 0.15), "layer": 2},
    "back": {"aspect_mid": (0.40, 0.15), "taper": (0.45, 0.15), "layer": 2},
    "nape": {"aspect_mid": (0.40, 0.15), "taper": (0.50, 0.15), "layer": 1},
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def catmull(pts, n=60):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (np.array(P[j], float) for j in (i - 1, i, i + 1, i + 2))
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(P[-2], float))
    return np.array(out)


def resample(c, m=101):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    s = np.linspace(0, d[-1], m)
    return np.c_[np.interp(s, d, c[:, 0]), np.interp(s, d, c[:, 1])], d[-1]


def metrics(pts):
    if len(pts) < 3:
        return None
    c, L = resample(catmull(pts))
    k = {}
    for u in (0.25, 0.5, 0.75):
        i = int(u * 100)
        a, b, cc = c[i - 8], c[i], c[i + 8]
        A, B, C = np.linalg.norm(b - a), np.linalg.norm(cc - b), np.linalg.norm(cc - a)
        cr = (b - a)[0] * (cc - b)[1] - (b - a)[1] * (cc - b)[0]
        k[u] = 2 * cr / (A * B * C) * HEAD_H_PX  # signed, per head-height (+ = turning clockwise in image)
    chord = np.linalg.norm(c[-1] - c[0])
    return {"arc_px": L, "chord_px": chord, "sag_ratio": 1 - chord / L, "kappa_25": k[0.25], "kappa_50": k[0.5],
            "kappa_75": k[0.75], "tip_dx_px": c[-1][0] - c[0][0], "tip_dy_px": c[-1][1] - c[0][1]}


def mc(pts, unc, n=300, seed=7):
    rnd = random.Random(seed)
    base = metrics(pts)
    if base is None:
        return None, None
    samples = []
    for _ in range(n):
        q = [(x + rnd.gauss(0, unc / 2), y + rnd.gauss(0, unc / 2)) for x, y in pts]
        samples.append(metrics(q))
    sd = {k: float(np.std([s[k] for s in samples])) for k in base}
    return base, sd


def hair_mask(path):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(float) / 255
    rgb, al = a[..., :3], a[..., 3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    s = (mx - mn) / (mx + 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m = (al > 0.5) & (b > g + 0.05) & (r > g + 0.03) & (mx < 0.80) & (s > 0.18)
    m[205:] = False  # straps below the hem
    # keep the largest 4-connected component (drops irises and strap fragments)
    from collections import deque
    lab = np.zeros(m.shape, int)
    best, best_n, cur = 0, 0, 0
    for y, x in zip(*np.nonzero(m)):
        if lab[y, x]:
            continue
        cur += 1
        q, n = deque([(y, x)]), 0
        lab[y, x] = cur
        while q:
            yy, xx = q.popleft()
            n += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v, u = yy + dy, xx + dx
                if 0 <= v < m.shape[0] and 0 <= u < m.shape[1] and m[v, u] and not lab[v, u]:
                    lab[v, u] = cur
                    q.append((v, u))
        if n > best_n:
            best, best_n = cur, n
    return lab == best


def silhouette_rows(mask, step=5):
    rows = []
    for y in range(0, 205, step):
        xs = np.nonzero(mask[y])[0]
        if len(xs):
            rows.append([y, int(xs.min()), int(xs.max())])
    return rows


def main(src, out):
    src, out = Path(src), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    srcs = {}
    for v, (f, want) in VIEWS.items():
        got = sha(src / f)
        if got != want:
            raise SystemExit(f"SHA mismatch {f}: {got}")
        srcs[v] = {"image": f, "sha256": got, "size_px": list(Image.open(src / f).size)}
    masks = {v: hair_mask(src / f) for v, (f, _) in VIEWS.items()}
    sil = {}
    for v, m in masks.items():
        ys, xs = np.nonzero(m)
        sil[v] = {"class": "observed_2d", "method": "purple-hue threshold on alpha>0.5, largest component, y<205",
                  "mask_sha256": hashlib.sha256(np.packbits(m).tobytes()).hexdigest(), "area_px": int(m.sum()),
                  "bbox_px": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                  "rows_y_xmin_xmax": silhouette_rows(m), "uncertainty_px": 2}
    locks = {}
    for lid, (region, obs) in LOCKS.items():
        d = REGION_DEFAULTS[region]
        rec = {"region": region, "views": {}, "estimated": {
            "section": "lens (flattened ellipse), thicker on the outer side",
            "thickness_over_width_mid": {"value": d["aspect_mid"][0], "uncertainty": d["aspect_mid"][1]},
            "taper_tip_over_mid": {"value": d["taper"][0], "uncertainty": d["taper"][1]},
            "layer_rank": d["layer"], "class": "estimated",
            "basis": "not visible in 2D; anime-bob convention + silhouette offset; verify with VRoid/HairHarpy native section"}}
        for v, (pts, unc, w) in obs.items():
            base, sd = mc(pts, unc)
            e = {"class": "observed_2d", "points_px": [list(p) for p in pts], "unc_px": unc,
                 "width_mid_px": w, "width_class": "observed_2d" if w else "undetermined"}
            if base:
                e["metrics"] = {k: round(float(val), 4) for k, val in base.items()}
                e["metrics_sd"] = {k: round(float(val), 4) for k, val in sd.items()}
                e["metrics"]["arc_hh"] = round(base["arc_px"] / HEAD_H_PX, 4)
            rec["views"][v] = e
        locks[lid] = rec
    # relations (order front->back); 'over' = drawn occluding; 'estimated' where hidden
    rel = [("BG_C", "over", "BG_CR1", "observed_2d"), ("BG_C", "over", "BG_CL1", "observed_2d"),
           ("BG_CR1", "over", "BG_CR2", "observed_2d"), ("BG_CL1", "over", "BG_CL2", "observed_2d"),
           ("BG_CR2", "over", "FF_CR", "observed_2d"), ("BG_CL2", "over", "FF_CL", "observed_2d"),
           ("FF_CR", "front_of", "ear_right", "observed_2d"), ("FF_CL", "front_of", "ear_left", "observed_2d"),
           ("SD_CR", "behind", "ear_right", "observed_2d"), ("SD_CL", "behind", "ear_left", "observed_2d"),
           ("FF_CR", "over", "SD_CR", "observed_2d"), ("FF_CL", "over", "SD_CL", "observed_2d"),
           ("SD_CR", "over", "BK_CR3", "estimated"), ("SD_CL", "over", "BK_CL3", "estimated"),
           ("BK_C_CR", "over", "BK_CR1", "observed_2d"), ("BK_C_CL", "over", "BK_CL1", "observed_2d"),
           ("BK_CR1", "over", "BK_CR2", "observed_2d"), ("BK_CL1", "over", "BK_CL2", "observed_2d"),
           ("BK_CR2", "over", "BK_CR3", "observed_2d"), ("BK_CL2", "over", "BK_CL3", "observed_2d"),
           ("BK_CR3", "over", "NP_CR", "estimated"), ("BK_CL3", "over", "NP_CL", "estimated"),
           ("TS_CR", "over", "FF_CR", "observed_2d"), ("TS_CL", "over", "FF_CL", "observed_2d"),
           ("BG_CR2", "over", "TS_CR", "observed_2d"), ("BG_CL2", "over", "TS_CL", "observed_2d"),
           ("SD_CR", "over", "SB_CR", "estimated"), ("SD_CL", "over", "SB_CL", "estimated"),
           ("SB_CR", "over", "BK_CR3", "estimated"), ("SB_CL", "over", "BK_CL3", "estimated"),
           ("FL_CR", "outside_of", "SD_CR", "observed_2d"), ("FL_CL", "outside_of", "SD_CL", "observed_2d"),
           ("BK_C_CL", "meets", "BK_C_CR", "observed_2d")]
    roots = {"parting_point": {"members": ["BG_C", "BG_C2", "BG_CR1", "BG_CR2", "BG_CL1", "BG_CL2"],
                               "anchor": "parting_point_front", "class": "observed_2d (front); 3D position estimated"},
             "crown_whorl": {"members": ["BK_C_CL", "BK_C_CR", "BK_CR1", "BK_CR2", "BK_CR3", "BK_CL1", "BK_CL2", "BK_CL3"],
                             "anchor": "whorl_back", "class": "observed_2d (back); 3D position estimated"},
             "temple_line": {"members": ["FF_CR", "FF_CL", "TS_CR", "TS_CL", "SD_CR", "SD_CL", "SB_CR", "SB_CL"], "class": "estimated (hairline hidden)"},
             "nape_line": {"members": ["NP_CR", "NP_CL", "BK_C_CL", "BK_C_CR"], "class": "estimated"}}
    asym = [
        {"id": "fringe_centre_lean", "observed": "BG_C tip (203,116) is 10 px to image-left (character right) of the "
         "parting point (213,33)", "class": "observed_2d", "keep": True},
        {"id": "fringe_side_lengths", "observed": "BG_CR2 tip y112 vs BG_CL2 tip y112; BG_CR1 y112 vs BG_CL1 y104 "
         "(CL inner shorter by 8 px)", "class": "observed_2d", "keep": True},
        {"id": "hem_heights", "observed": "front hem CR (148,190) vs CL (277,189): equal within uncertainty",
         "class": "observed_2d"},
        {"id": "outer_flicks", "observed": "outward flick on both sides (FL_CR, FL_CL); CL front flick wider "
         "(silhouette x 306 vs 114 about centre 213: CL +93 px, CR -99 px)", "class": "observed_2d"},
    ]
    vroid = {
        "fringe (BG_*)": {"status": "VROID_FEASIBLE_UNPROVEN", "method": "hand-drawn bang guides from one parting point"},
        "temple (FF_*)": {"status": "VROID_FEASIBLE_UNPROVEN", "method": "front side guides, in front of ear"},
        "side mass (SD_*) + tucked ear": {"status": "VROID_FEASIBLE_UNPROVEN", "method": "side guides behind ear"},
        "back + nape V (BK_*, NP_*)": {"status": "VROID_FEASIBLE_UNPROVEN", "method": "back guides from whorl"},
        "outer flicks (FL_*)": {"status": "UNDETERMINED", "method": "thin separate guides; HairHarpy candidate only if VRoid fails"},
        "crown notch (213,21)": {"status": "UNDETERMINED", "method": "VRoid base hair + guide; HairHarpy candidate only if VRoid fails"},
        "scalp coverage / base": {"status": "VROID_FEASIBLE_UNPROVEN", "method": "VRoid base hair"},
        "note": "no part is VRoid-PROVEN yet: requires the current VRoid native/head copy from #427 (HOLD)"}
    accept = {
        "G1_design": ["four-view silhouette IoU >= 0.92 per view against these masks after registration (mask_sha256)",
                      "parting point / whorl / nape notch within 3 px; hem points within 4 px",
                      "each observed lock tip within max(4 px, 1.5 x unc_px); root within max(5 px, 2 x unc_px)",
                      "kappa_50 within 2 x metrics_sd + 0.5 per head-height (2D projected), sign preserved",
                      "all asymmetries marked keep=True reproduced with sign",
                      "lock IDs and relations complete; ear exposure pattern (FF in front, SD behind) preserved"],
        "G2_art": ["independent art QA on four views + three-quarter + top (estimated) + face close-up",
                   "fringe tuft reads as one fan from the parting point, no scalp visible in any view",
                   "hem flicks read as outward, not broken geometry; volume matches silhouette"],
        "G3_structure": ["closed manifold lock meshes, UV V root->tip, material direction along the centreline",
                         "penetration / contact thresholds: HOLD - to be set at design review from the native head "
                         "(the neutral-head values 1 mm / root zone 0.15 / 30 % are NOT carried over)",
                         "native save + reopen, protected-scope fingerprint unchanged"],
        "HOLD": ["absolute 3D dimensions (mm)", "scalp connection measurements", "VRoid native response"]}
    bp = {"schema": "two-morwen-hair-l0-blueprint/v1", "status": "DESIGN_2D_PROVISIONAL_NOT_ADOPTED",
          "pr": 474, "source": {"artifact_id": 14602858760, "run_id": 44679568515,
                                "artifact_digest": "sha256:d7e006a37dbc739a68d3a409c6ceafd038306d856bb445c8c8c60d4e18c3d29d",
                                "views": srcs, "landmarks": {"path": "tools/morwen_authored_sculpt/layer0_landmarks_v1.json",
                                                            "blob": "93eefba2426f33b5033d07ba7d7c751a99a12292"},
                                "precision_blueprint_v2_blob": "ea55e2bcaf5cddc4af3b012e738d075a83ae66b1"},
          "coordinate_system": "original px, origin top-left, x right, y down, unmirrored; CR/CL = character right/left",
          "units": {"px": "source pixel", "hh": f"front head height crown->chin = {HEAD_H_PX} px",
                    "kappa": "signed curvature x head height (2D projected)", "mm": "HOLD"},
          "value_classes": ["observed_2d", "native_measured (none yet)", "estimated", "undetermined"],
          "silhouettes": sil, "points": {k: {"view": v, "xy_px": list(p), "unc_px": u, "class": "observed_2d"}
                                         for k, (v, p, u) in POINTS.items()},
          "locks": locks, "relations": [{"a": a, "rel": r, "b": b, "class": c} for a, r, b, c in rel],
          "root_groups": roots, "asymmetry": asym, "vroid_feasibility": vroid, "acceptance": accept,
          "invisible_parts": {"top_view": "ESTIMATED: fringe fans forward from the parting point just in front of the "
                              "vertex; back locks radiate from the crown whorl; side masses from the temple line",
                              "sections": "ESTIMATED per region (see locks.*.estimated)",
                              "verification": "VRoid native top/section renders + native lock measurement after #427 supply"},
          "not_carried_over": "neutral-head 24 locks, 1 mm penetration threshold, root zone 0.15, 30 % curvature tolerance"}
    # design-completeness self-check: share of the hair mask farther than 14 px from every lock centreline
    from scipy.ndimage import distance_transform_edt
    cov = {}
    for v, m in masks.items():
        lines = np.zeros(m.shape, bool)
        for L in locks.values():
            if v in L["views"]:
                for x, y in catmull([tuple(p) for p in L["views"][v]["points_px"]], 40):
                    lines[int(round(y)), int(round(x))] = True
        un = m & (distance_transform_edt(~lines) > 14)
        cov[v] = round(float(un.sum() / m.sum()), 4)
    bp["self_check"] = {"uncovered_mask_fraction_gt14px": cov, "criterion": "<= 0.10 per view",
                        "pass": all(x <= 0.10 for x in cov.values()),
                        "note": "completeness of the lock registry against the observed silhouette; not an art judgement"}
    (HERE / "morwen_hair_l0_blueprint_v1.json").write_text(json.dumps(bp, indent=1, ensure_ascii=False) + "\n")
    draw(src, out, masks, bp)
    print(len(locks), "locks", sum(len(l["views"]) for l in locks.values()), "view observations")


COL = {"fringe": (220, 40, 40), "temple": (240, 140, 0), "side": (30, 110, 230), "flick": (200, 0, 200),
       "back": (20, 150, 60), "nape": (0, 150, 160)}


def draw(src, out, masks, bp):
    order = ["front", "right", "back", "left"]
    x0 = {"front": 90, "right": 70, "back": 50, "left": 60}
    W, H, S = 240, 215, 3
    over = Image.new("RGB", (W * S * 4, H * S), "white")
    sch = Image.new("RGB", (W * S * 4, H * S), "white")
    for k, v in enumerate(order):
        im = Image.open(src / VIEWS[v][0]).convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        a = bg.convert("RGB").crop((x0[v], 0, x0[v] + W, H)).resize((W * S, H * S), Image.LANCZOS)
        b = Image.new("RGB", (W * S, H * S), "white")
        m = masks[v][:H, x0[v]:x0[v] + W]
        edge = m ^ np.roll(m, 1, 0) | m ^ np.roll(m, 1, 1)
        bd = ImageDraw.Draw(b)
        for yy, xx in zip(*np.nonzero(edge)):
            bd.rectangle([xx * S, yy * S, xx * S + S - 1, yy * S + S - 1], fill=(150, 150, 150))
        for img in (a, b):
            d = ImageDraw.Draw(img)
            for lid, L in bp["locks"].items():
                if v not in L["views"]:
                    continue
                e = L["views"][v]
                c = catmull([tuple(p) for p in e["points_px"]], 20)
                P = [((x - x0[v]) * S, y * S) for x, y in c]
                col = COL[L["region"]]
                if e["width_mid_px"]:
                    d.line(P, fill=tuple(int(0.35 * q + 165) for q in col), width=max(2, int(e["width_mid_px"] * S)), joint="curve")
                d.line(P, fill=col, width=3)
                r0 = P[0]
                d.ellipse([r0[0] - 5, r0[1] - 5, r0[0] + 5, r0[1] + 5], outline=col, width=2)
                d.text((P[-1][0] + 4, P[-1][1] - 4), lid, fill=(0, 0, 0))
            for pid, p in bp["points"].items():
                if p["view"] == v:
                    x, y = p["xy_px"]
                    X, Y, r = (x - x0[v]) * S, y * S, p["unc_px"] * S
                    d.ellipse([X - r, Y - r, X + r, Y + r], outline=(0, 0, 0), width=1)
            d.text((6, 6), f"{v}  {VIEWS[v][0]}  sha {VIEWS[v][1][:12]}", fill=(0, 0, 0))
        over.paste(a, (k * W * S, 0))
        sch.paste(b, (k * W * S, 0))
    over.save(out / "l0_hair_overlay_contains_source_pixels.png")
    sch.save(out / "l0_hair_schematic_lines_only.png")
    # estimated top view + sections (schematic, no source pixels)
    T = Image.new("RGB", (900, 450), "white")
    d = ImageDraw.Draw(T)
    cx, cy, R = 220, 225, 170
    d.ellipse([cx - R, cy - R * 1.15, cx + R, cy + R * 1.15], outline=(120, 120, 120), width=2)
    d.text((10, 8), "TOP VIEW - ESTIMATED (not observed). front = up. CR = image left", fill=(200, 0, 0))
    part, whorl = (cx, cy - 70), (cx, cy + 25)
    for lid, L in bp["locks"].items():
        reg = L["region"]
        az = {"BG_C": -90, "BG_C2": -80, "BG_CR1": -105, "BG_CR2": -125, "BG_CL1": -70, "BG_CL2": -55, "FF_CR": -150,
              "FF_CL": -30, "SD_CR": 180, "SD_CL": 0, "FL_CR": 160, "FL_CL": 20, "BK_C_CL": 92, "BK_C_CR": 88,
              "BK_CR1": 105, "BK_CR2": 125, "BK_CR3": 145, "BK_CL1": 75, "BK_CL2": 55, "BK_CL3": 35, "NP_CR": 115,
              "NP_CL": 65, "TS_CR": -140, "TS_CL": -40, "SB_CR": 165, "SB_CL": 15}[lid]
        o = part if reg == "fringe" else whorl if reg in ("back", "nape") else (cx, cy - 20)
        t = math.radians(az)
        tip = (cx + R * 1.05 * math.cos(t), cy + R * 1.2 * math.sin(t))
        d.line([o, tip], fill=COL[reg], width=3)
        d.text((tip[0] + 3, tip[1] - 5), lid, fill=(0, 0, 0))
    for p, n in ((part, "parting point"), (whorl, "whorl")):
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=(0, 0, 0))
        d.text((p[0] + 8, p[1] - 6), n, fill=(0, 0, 0))
    d.text((470, 8), "SECTIONS - ESTIMATED (mid-length, width normalised)", fill=(200, 0, 0))
    y = 50
    for reg, dd in REGION_DEFAULTS.items():
        w, a = 160, dd["aspect_mid"][0]
        d.text((470, y), f"{reg}: t/w {a:.2f}+-{dd['aspect_mid'][1]:.2f}, taper {dd['taper'][0]:.2f}", fill=(0, 0, 0))
        d.ellipse([700, y - 2, 700 + w, y - 2 + w * a], outline=COL[reg], width=3)
        y += 62
    T.save(out / "l0_hair_top_sections_estimated.png")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
