"""MORWEN-EYELID-RETOPO-05: lid-margin target curves on the protected Layer 0 front view.

Read-only (numpy + Pillow), deterministic. The reference is SHA-verified through the LANDMARK-02
loader. Each eye is measured independently:

  opening pixel  sclera (LANDMARK-02 rule) or violet iris (any brightness; the dark pupil
                 top is rejected later as an outlier because it sits under the lash line)
  canthus        innermost / outermost column that contains opening pixels; y = middle of the
                 opening run in that column (the inner end is blunt, ~7 px tall, so the
                 LANDMARK-02 "nearest sclera pixel" (top row) is not used as the canthus)
  margins        per column, first (upper) and last (lower) opening row; fitted with a degree-4
                 Bernstein curve whose end points are fixed at the canthi; two passes, samples
                 with residual > 1.5 px dropped (pupil/hair columns)

Symmetry rule (task requirement: never treat a 1 px difference as intended design):
  for each quantity the R and L values are compared after mirroring; |difference| <= 1 px
  (the measurement uncertainty) -> one shared value (mean, SYMMETRIC_WITHIN_UNCERTAINTY);
  larger -> kept per side (MEASURED_ASYMMETRY_UNCONFIRMED: needs art review before it is
  treated as a design decision).

Output: $MORWEN_OUT/EYE_TARGETS_05.json (+ EYE_TARGETS_05_OVERLAY.png)
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "head_landmark"))
import measure_canonical_landmarks_2d as C  # noqa: E402  (SHA-verified loader + colour masks)

OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_eyelid_retopo_05"))
CAN2D = HERE.parent / "_qa" / "head_landmark_02" / "CANONICAL_LANDMARKS_2D.json"
UNC = C.PIXEL_UNCERTAINTY
ROI_Y = (108, 140)
N_SAMPLES = 33  # curve samples per margin (t = 0..1)


def bern(t, n=4):
    from math import comb
    t = np.asarray(t, float)
    return np.stack([comb(n, k) * t ** k * (1 - t) ** (n - k) for k in range(n + 1)], -1)


def fit_margin(ts, ys, y0, y1, degree=4):
    """Bernstein curve with fixed ends (returned as degree-4 coefficients); kept-sample mask."""
    keep = np.ones(len(ts), bool)
    for _ in range(2):
        B = bern(ts[keep], degree)
        rhs = ys[keep] - B[:, 0] * y0 - B[:, degree] * y1
        c, *_ = np.linalg.lstsq(B[:, 1:degree], rhs, rcond=None)
        coef = np.array([y0, *c, y1])
        res = np.abs(bern(ts, degree) @ coef - ys)
        keep = res <= 1.5
    if degree == 3:  # exact degree elevation 3 -> 4
        c = coef
        coef = np.array([c[0], (c[0] + 3 * c[1]) / 4, (c[1] + c[2]) / 2, (3 * c[2] + c[3]) / 4, c[3]])
    return coef, keep


def measure_eye(m, x_lo, x_hi, inner_is_hi):
    """x_lo..x_hi = the x extent of this eye's validated sclera blobs (LANDMARK-02 eye_regions)."""
    opening = m["sclera"] | m["violet"]
    cols = [x for x in range(x_lo, x_hi + 1) if opening[ROI_Y[0]:ROI_Y[1], x].any()]
    # opening columns must be contiguous with the eye (drop isolated hair-violet columns at ROI top)
    runs, sclera_top = {}, {}
    for x in cols:
        r = np.nonzero(opening[ROI_Y[0]:ROI_Y[1], x])[0] + ROI_Y[0]
        r = r[(r >= 116) & (r <= 136)]  # rows above the lash band are hair
        if len(r):
            runs[x] = (int(r.min()), int(r.max()))
            # the iris is tucked under the (violet) lash band, so the upper margin is only
            # observable where the first opening pixel below the lash is sclera
            if m["sclera"][r.min(), x]:
                sclera_top[x] = int(r.min())
    xs = sorted(runs)
    x_in, x_out = (xs[-1], xs[0]) if inner_is_hi else (xs[0], xs[-1])
    c_in = (x_in, (runs[x_in][0] + runs[x_in][1]) / 2)
    c_out = (x_out, (runs[x_out][0] + runs[x_out][1]) / 2)
    width = abs(x_in - x_out)
    ts = np.array([abs(x - x_in) / width for x in xs])
    up = np.array([runs[x][0] for x in xs], float)
    lo = np.array([runs[x][1] for x in xs], float)
    # lash band top: first dark row in 112..122 followed by two more dark-or-violet rows (all columns)
    band = m["dark"] | m["violet"]
    lash_top = {}
    for x in xs:
        for y in range(112, 123):
            if m["dark"][y, x] and band[y + 1, x] and band[y + 2, x]:
                lash_top[x] = y
                break
    # lash thickness where the margin is observable (sclera wedges), linear in t across the iris
    th = [(abs(x - x_in) / width, sclera_top[x] - lash_top[x]) for x in xs if x in sclera_top and x in lash_top]
    th_in = [d for t_, d in th if t_ < 0.5]
    th_out = [d for t_, d in th if t_ >= 0.5]
    tau_in = float(np.median(th_in)) if th_in else float(np.median([d for _, d in th]))
    tau_out = float(np.median(th_out)) if th_out else tau_in
    up = np.array([lash_top[x] + tau_in + (tau_out - tau_in) * abs(x - x_in) / width if x in lash_top else np.nan
                   for x in xs], float)
    ok = ~np.isnan(up)
    cu, ku_s = fit_margin(ts[ok], up[ok], c_in[1], c_out[1])
    ku = np.zeros(len(xs), bool)
    ku[np.nonzero(ok)[0]] = ku_s
    cl, kl = fit_margin(ts, lo, c_in[1], c_out[1])
    return {"canthus_inner_px": [float(c_in[0]), float(c_in[1])], "canthus_outer_px": [float(c_out[0]), float(c_out[1])],
            "width_px": float(width), "upper_coef": cu.tolist(), "lower_coef": cl.tolist(),
            "upper_rule": "lash-band top (every column) + lash thickness measured on the sclera wedges (inner/outer median, "
                          "linear across the iris, which is tucked under the lash); degree-4 Bernstein, ends fixed",
            "lash_thickness_px": {"inner": tau_in, "outer": tau_out},
            "samples": {"x": xs, "upper": [None if np.isnan(u) else u for u in up], "lower": lo.tolist(),
                        "upper_kept": ku.tolist(), "lower_kept": kl.tolist()}}


def curve(e, which, t):
    return bern(t) @ np.array(e[f"{which}_coef"])


def compute(write=True):
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
    a, meta = C.load("front")
    m = C.masks(a)
    can = json.loads(CAN2D.read_text())["views"]["front"]
    U_px, eye_y, mid_x = can["U_px"], can["eye_line_y"], can["mid_pupil_x"]
    lm = can["landmarks"]
    face_rows = can["face_outline_rows"]
    ext = C.eye_regions(m, min(r[1] for r in face_rows) - 4, max(r[2] for r in face_rows) + 5,
                        int(eye_y - 0.4 * U_px), int(eye_y + 0.3 * U_px), mid_x)
    assert len(ext) == 2, "two validated sclera groups expected"
    box = [(int(e["sclera"][1].min()), int(e["sclera"][1].max())) for e in ext]  # image-left first = R
    eyes = {"R": measure_eye(m, *box[0], True), "L": measure_eye(m, *box[1], False)}
    t = np.linspace(0, 1, N_SAMPLES)
    # mirrored comparison in eye-local coordinates (dx from the inner canthus, y)
    cmp = {}
    for which in ("upper", "lower"):
        d = curve(eyes["R"], which, t) - curve(eyes["L"], which, t)
        cmp[f"{which}_margin_max_abs_diff_px"] = round(float(np.abs(d).max()), 3)
    cmp["width_diff_px"] = eyes["R"]["width_px"] - eyes["L"]["width_px"]
    cmp["canthus_inner_y_diff_px"] = eyes["R"]["canthus_inner_px"][1] - eyes["L"]["canthus_inner_px"][1]
    cmp["canthus_outer_y_diff_px"] = eyes["R"]["canthus_outer_px"][1] - eyes["L"]["canthus_outer_px"][1]
    cmp["inner_canthus_offset_from_mid_diff_px"] = (mid_x - eyes["R"]["canthus_inner_px"][0]) - (eyes["L"]["canthus_inner_px"][0] - mid_x)
    pupils = {s: lm[f"pupil_{s}"]["px"] for s in ("R", "L")}
    cmp["pupil_y_diff_px"] = round(pupils["R"][1] - pupils["L"][1], 3)
    decision = {k: ("SYMMETRIC_WITHIN_UNCERTAINTY" if abs(v) <= UNC else "MEASURED_ASYMMETRY_UNCONFIRMED") for k, v in cmp.items()}

    # design targets per side (eye-local), shared where symmetric
    def shared(which):
        return decision[f"{which}_margin_max_abs_diff_px"] == "SYMMETRIC_WITHIN_UNCERTAINTY"
    design = {}
    for s in ("R", "L"):
        e = eyes[s]
        o = "L" if s == "R" else "R"
        cu = e["upper_coef"] if not shared("upper") else ((np.array(e["upper_coef"]) + np.array(eyes[o]["upper_coef"])) / 2).tolist()
        cl = e["lower_coef"] if not shared("lower") else ((np.array(e["lower_coef"]) + np.array(eyes[o]["lower_coef"])) / 2).tolist()
        design[s] = {"upper_coef": cu, "lower_coef": cl}
    # pupil: shared fraction where the two sides agree within 1 px
    pf = {}
    for s in ("R", "L"):
        e = eyes[s]
        xi, xo = e["canthus_inner_px"][0], e["canthus_outer_px"][0]
        pf[s] = abs(pupils[s][0] - xi) / abs(xo - xi)
    frac_diff_px = abs(pf["R"] - pf["L"]) * eyes["R"]["width_px"]
    pupil_frac = {s: (pf["R"] + pf["L"]) / 2 if frac_diff_px <= UNC else pf[s] for s in ("R", "L")}
    pupil_y = {s: (pupils["R"][1] + pupils["L"][1]) / 2 if abs(cmp["pupil_y_diff_px"]) <= UNC else pupils[s][1] for s in ("R", "L")}

    def to3d(px, py, cal):
        return [cal["mid_x_m"] + (mid_x - px) / cal["s"], cal["eye_line_z_m"] - (py - eye_y) / cal["s"]]
    cal = {"s": U_px / 0.0915, "mid_x_m": 0.00026, "eye_line_z_m": 1.44589,
           "rule": "x = MID_X + (mid_pupil_x - px)/s, z = eye_line_z - (py - eye_line_y)/s; s = U_px / U_m (LANDMARK-02 calibration: "
                   "eye line = mean pupil, U = eye line to menton = 0.0915 m); image-left eye = character R (+x)"}
    # canthi in eye-local terms (offset from the centre line, y); shared where symmetric within 1 px
    loc = {s: {"in_off": abs(mid_x - eyes[s]["canthus_inner_px"][0]), "out_off": abs(mid_x - eyes[s]["canthus_outer_px"][0]),
               "in_y": eyes[s]["canthus_inner_px"][1], "out_y": eyes[s]["canthus_outer_px"][1]} for s in ("R", "L")}
    sym_canthi = all(decision[k] == "SYMMETRIC_WITHIN_UNCERTAINTY" for k in
                     ("width_diff_px", "canthus_inner_y_diff_px", "canthus_outer_y_diff_px", "inner_canthus_offset_from_mid_diff_px"))
    if sym_canthi:
        mean = {k: (loc["R"][k] + loc["L"][k]) / 2 for k in loc["R"]}
        loc = {"R": mean, "L": mean}
    for s in ("R", "L"):  # curve ends must coincide with the canthi used
        for which in ("upper", "lower"):
            design[s][f"{which}_coef"][0] = loc[s]["in_y"]
            design[s][f"{which}_coef"][-1] = loc[s]["out_y"]
    targets = {}
    for s in ("R", "L"):
        e = eyes[s]
        sg = -1 if s == "R" else 1  # image x direction away from the centre line
        xi, xo = mid_x + sg * loc[s]["in_off"], mid_x + sg * loc[s]["out_off"]
        e = dict(e, canthus_inner_px=[xi, loc[s]["in_y"]], canthus_outer_px=[xo, loc[s]["out_y"]], width_px=abs(xo - xi))
        xs = xi + (xo - xi) * t
        up, lo = bern(t) @ np.array(design[s]["upper_coef"]), bern(t) @ np.array(design[s]["lower_coef"])
        targets[s] = {
            "canthus_inner_xz": to3d(xi, e["canthus_inner_px"][1], cal),
            "canthus_outer_xz": to3d(xo, e["canthus_outer_px"][1], cal),
            "upper_xz": [to3d(x, y, cal) for x, y in zip(xs, up)],
            "lower_xz": [to3d(x, y, cal) for x, y in zip(xs, lo)],
            "pupil_xz": to3d(xi + (xo - xi) * pupil_frac[s], pupil_y[s], cal),
            "width_U": round(e["width_px"] / U_px, 4),
            "height_U": round(float((lo - up).max()) / U_px, 4),
        }
    targets["ipd_U"] = round(abs(targets["R"]["pupil_xz"][0] - targets["L"]["pupil_xz"][0]) * cal["s"] / U_px, 4)
    res = {"task_id": "MORWEN-EYELID-RETOPO-05", "source": meta, "pixel_uncertainty_px": UNC, "U_px": U_px,
           "eye_line_y_px": eye_y, "mid_pupil_x_px": mid_x, "calibration": cal, "measured": eyes,
           "mirror_comparison_px": cmp, "symmetry_decision": decision, "canthi_shared": sym_canthi, "canthi_local_px": loc, "pupil_fraction_from_inner": pf,
           "pupil_fraction_used": pupil_frac, "design_coef": design, "targets_3d": targets,
           "landmark02_note": "LANDMARK-02 eye_top_L (y 123) / eye_inner (top row of the blunt inner end) are mask artefacts "
                              "(bang strand over the L eye top; pupil darker than the iris threshold); not used as design targets"}
    if not write:
        return res
    (OUT / "EYE_TARGETS_05.json").write_text(json.dumps(res, indent=2) + "\n")
    # overlay for visual check (10x)
    img = Image.fromarray((a * 255).astype(np.uint8)).crop((166, 108, 262, 144))
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.alpha_composite(img)
    k = 10
    big = bg.convert("RGB").resize((img.size[0] * k, img.size[1] * k), Image.NEAREST)
    dr = ImageDraw.Draw(big)
    for s in ("R", "L"):
        e = eyes[s]
        xi, xo = e["canthus_inner_px"][0], e["canthus_outer_px"][0]
        for which, col in (("upper", (0, 200, 255)), ("lower", (255, 160, 0))):
            ys = bern(t) @ np.array(design[s][f"{which}_coef"])
            pts = [((xi + (xo - xi) * tt - 166 + 0.5) * k, (y - 108 + 0.5) * k) for tt, y in zip(t, ys)]
            dr.line(pts, fill=col, width=3)
        for c in (e["canthus_inner_px"], e["canthus_outer_px"]):
            x, y = (c[0] - 166 + 0.5) * k, (c[1] - 108 + 0.5) * k
            dr.ellipse((x - 6, y - 6, x + 6, y + 6), outline=(255, 0, 0), width=3)
    big.save(OUT / "EYE_TARGETS_05_OVERLAY.png")
    return res


def main():
    res = compute()
    cmp, decision, targets = res["mirror_comparison_px"], res["symmetry_decision"], res["targets_3d"]
    print(json.dumps({"comparison": cmp, "decision": decision,
                      "targets": {s: {k_: targets[s][k_] for k_ in ("width_U", "height_U")} for s in ("R", "L")},
                      "ipd_U": targets["ipd_U"]}, indent=1))


if __name__ == "__main__":
    main()
