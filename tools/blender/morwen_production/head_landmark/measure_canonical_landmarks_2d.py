"""MORWEN-HEAD-LANDMARK-02: measure head landmarks on the protected Layer 0 four-view references.

Read-only image analysis (numpy + Pillow + scipy.ndimage, no randomness). Every reference file is
SHA-verified against tools/blender/production_mesh_08/layer0_reference_manifest.json first.

Coordinates are image pixels (x right, y down) of the 384x1024 sheets. Status values:
  MEASURED                deterministic colour/silhouette rule
  ESTIMATED               drawn mark or occluded geometry; approximation, never a measured fact
  NOT_MEASURABLE          occluded by hair/clothing in this view (value is null)
Each rule is written next to the value. Left/right are measured independently: the canonical hair
is asymmetric and must not be mirrored.

Output: $MORWEN_OUT/CANONICAL_LANDMARKS_2D.json
"""
import colorsys
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

MANIFEST = Path(os.environ.get("MORWEN_LAYER0_MANIFEST",
                               "tools/blender/production_mesh_08/layer0_reference_manifest.json"))
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_head_landmark_02"))
PIXEL_UNCERTAINTY = 1.0  # +/- px for every MEASURED point (anti-aliased line art)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(view):
    man = json.loads(MANIFEST.read_text())
    meta = next(i for i in man["images"] if i["view"] == view)
    f = MANIFEST.parent / "references" / meta["filename"]
    actual = sha(f)
    assert actual == meta["sha256"], f"{f}: SHA mismatch"
    a = np.asarray(Image.open(f).convert("RGBA")).astype(np.float32) / 255.0
    return a, {"file": meta["filename"], "sha256": actual, "view": view}


def hsv(a):
    rgb = a[..., :3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6.0
    return h, s, v


def masks(a):
    h, s, v = hsv(a)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    alpha = a[..., 3] > 0.78
    skin = alpha & (r > 0.745) & (r > g + 0.03) & (g > b - 0.02) & (s < 0.45) & (s > 0.05)
    violet = alpha & (h > 0.68) & (h < 0.95) & (s > 0.25) & (v > 0.30)
    dark = alpha & (v < 0.35)
    sclera = alpha & (s < 0.13) & (v > 0.85)
    return {"alpha": alpha, "skin": skin, "violet": violet, "dark": dark, "sclera": sclera, "v": v}


def eye_regions(m, x0, x1, y0, y1, split_x=None, pad=0):
    """Eye opening = all sclera blobs in the ROI (the iris splits each sclera into inner/outer wedges),
    grouped by side of split_x; blobs < 30% of the largest blob or without skin directly below are rejected; iris = violet pixels inside each group's padded box."""
    roi = np.zeros_like(m["sclera"])
    roi[y0:y1, x0:x1] = True
    lab, n = ndimage.label(m["sclera"] & roi)
    groups = {}
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)) if n else [0]
    floor = 0.3 * max(sizes)  # specular specks/strand highlights are far smaller than sclera wedges
    for i in range(1, n + 1):
        sy, sx = np.nonzero(lab == i)
        if len(sy) < max(2, floor):
            continue
        # an eye's sclera sits on the lower lid: skin within 5 px below it (bang highlights have hair below)
        below = m["skin"][sy.max() + 1:sy.max() + 6, sx.min():sx.max() + 1]
        if not below.any():
            continue
        g = 0 if split_x is None else int(sx.mean() > split_x)
        groups.setdefault(g, []).append((sy, sx))
    eyes = []
    for g in sorted(groups):
        sy = np.concatenate([b[0] for b in groups[g]])
        sx = np.concatenate([b[1] for b in groups[g]])
        box = np.zeros_like(roi)
        box[sy.min():sy.max() + 3, sx.min() - pad:sx.max() + 1 + pad] = True
        # iris: violet AND brighter than the hair/lash shadow that borders the eye top
        vy, vx = np.nonzero(box & m["violet"] & (m["v"] > 0.42))
        eyes.append({"sclera": (sy, sx), "iris": (vy, vx),
                     "open": (np.concatenate([sy, vy]), np.concatenate([sx, vx]))})
    return eyes


def pt(x, y, status, method, unc=PIXEL_UNCERTAINTY):
    if x is None:
        return {"px": None, "status": "NOT_MEASURABLE", "method": method}
    return {"px": [round(float(x), 2), round(float(y), 2)], "status": status, "method": method,
            "uncertainty_px": unc if status == "MEASURED" else None}


def head_component(skin, H, prefer=None):
    lab, n = ndimage.label(skin)
    best, best_n = None, 0
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if ys.mean() > 0.22 * H or len(ys) < 150:
            continue
        if prefer is not None and not prefer(xs, ys):
            continue
        if len(ys) > best_n:
            best, best_n = lab == i, len(ys)
    assert best is not None, "face skin component not found"
    return best


def front(a):
    m = masks(a)
    H, W = m["alpha"].shape
    face = head_component(m["skin"], H)
    ys, xs = np.nonzero(face)
    chin_y = ys.max()
    chin_x = xs[ys == chin_y].mean()
    filled = ndimage.binary_fill_holes(face)
    holes, n = ndimage.label(filled & ~face)
    sizes = ndimage.sum(np.ones_like(holes), holes, range(1, n + 1))
    order = [i + 1 for i in np.argsort(-sizes)]
    face_top = ys.min()
    eyes = eye_regions(m, xs.min() - 4, xs.max() + 5, face_top - 4, int(face_top + 0.55 * (chin_y - face_top)), chin_x)
    assert len(eyes) == 2, "two eye openings expected in front view"
    out = {}
    # image-left eye in a front view is the character's RIGHT eye
    for side, e in zip(("R", "L"), eyes):
        sy, sx = e["sclera"]
        oy, ox = e["open"]
        vy, vx = e["iris"]
        inner_i = np.argmax(sx) if side == "R" else np.argmin(sx)
        outer_i = np.argmin(sx) if side == "R" else np.argmax(sx)
        out[f"eye_inner_{side}"] = pt(sx[inner_i], sy[inner_i], "MEASURED", "sclera pixel nearest the centre line")
        out[f"eye_outer_{side}"] = pt(sx[outer_i], sy[outer_i], "MEASURED", "sclera pixel farthest from the centre line")
        out[f"pupil_{side}"] = pt(vx.mean(), vy.mean(), "MEASURED", "centroid of violet iris pixels in the eye box")
        out[f"eye_top_{side}"] = pt(ox[np.argmin(oy)], oy.min(), "MEASURED", "top of sclera+iris opening")
        out[f"eye_bottom_{side}"] = pt(ox[np.argmax(oy)], oy.max(), "MEASURED", "bottom of sclera+iris opening")
    eye_y = (out["pupil_R"]["px"][1] + out["pupil_L"]["px"][1]) / 2
    mid_x = (out["pupil_R"]["px"][0] + out["pupil_L"]["px"][0]) / 2
    U = chin_y - eye_y
    out["menton"] = pt(chin_x, chin_y, "MEASURED", "lowest pixel of the face skin region (jaw line separates neck)")
    # mouth: darkest row of a 7 px centre column band between nose and chin
    y0 = int(eye_y + 0.55 * U)
    y1 = int(chin_y - 0.12 * U)
    band = m["v"][y0:y1, int(mid_x) - 3:int(mid_x) + 4].mean(1)
    my = y0 + int(np.argmin(band))
    face_v = np.median(m["v"][face])
    row = np.nonzero((m["v"][my] < face_v - 0.06) & filled[my])[0]
    row = row[np.abs(row - mid_x) < 0.5 * U]
    if len(row):
        out["stomion"] = pt(mid_x, my, "MEASURED", "darkest row of centre column between 0.55U below eye and 0.12U above chin")
        out["mouth_corner_R"] = pt(row.min(), my, "ESTIMATED", "low-contrast lip line: leftmost darker pixel on stomion row")
        out["mouth_corner_L"] = pt(row.max(), my, "ESTIMATED", "low-contrast lip line: rightmost darker pixel on stomion row")
    # nose: anime nose is a faint shade; darkest centre-column row between eye line+0.15U and mouth-0.15U
    n0, n1 = int(eye_y + 0.15 * U), int(my - 0.15 * U)
    nb = m["v"][n0:n1, int(mid_x) - 2:int(mid_x) + 3].mean(1)
    ny = n0 + int(np.argmin(nb))
    out["pronasale"] = pt(mid_x, ny, "ESTIMATED",
                          "drawn nose shade (no contour): darkest centre-column row 0.15U below eye line to 0.15U above mouth")
    # face outline per row (left/right separately) and occlusion flag
    width = []
    for y in range(int(eye_y), int(chin_y) + 1):
        xs_r = np.nonzero(filled[y])[0]
        if len(xs_r) == 0:
            continue
        lx, rx = xs_r.min(), xs_r.max()
        occ_l = bool(m["alpha"][y, max(lx - 2, 0)] and not m["skin"][y, max(lx - 2, 0)])
        occ_r = bool(m["alpha"][y, min(rx + 2, W - 1)] and not m["skin"][y, min(rx + 2, W - 1)])
        width.append([y, int(lx), int(rx), occ_l, occ_r])
    ny_ = out["pronasale"]["px"][1]
    wrow = min(width, key=lambda w: abs(w[0] - ny_))
    out["cheek_R"] = pt(wrow[1], wrow[0], "MEASURED", "face outline at nose-mark row (image-left = character right)"
                        + ("; adjacent pixel is hair: OCCLUSION_POSSIBLE" if wrow[3] else ""))
    out["cheek_L"] = pt(wrow[2], wrow[0], "MEASURED", "face outline at nose-mark row"
                        + ("; adjacent pixel is hair: OCCLUSION_POSSIBLE" if wrow[4] else ""))
    for k in ("temple_R", "temple_L"):
        out[k] = pt(None, None, None, "covered by bangs/side hair in front view")
    for k in ("ear_center_R", "ear_center_L"):
        out[k] = pt(None, None, None, "covered by hair in front view")
    out["vertex_skull"] = pt(None, None, None, "skull top hidden by hair")
    ay, ax = np.nonzero(m["alpha"][: int(eye_y)])
    out["hair_top"] = pt(ax[ay == ay.min()].mean(), ay.min(), "MEASURED", "topmost opaque pixel (hair silhouette)")
    ny2 = int(chin_y + 0.3 * U)
    neck = np.nonzero(m["skin"][ny2])[0]
    neck = neck[np.abs(neck - mid_x) < 0.6 * U]
    out["neck_left_edge"] = pt(neck.min(), ny2, "MEASURED", "skin run at chin+0.3U (image-left)")
    out["neck_right_edge"] = pt(neck.max(), ny2, "MEASURED", "skin run at chin+0.3U (image-right)")
    return out, {"U_px": float(U), "eye_line_y": float(eye_y), "mid_pupil_x": float(mid_x),
                 "face_outline_rows": width}


def side(a, facing):
    """facing=+1: face points to image right (character right side view)."""
    m = masks(a)
    H, W = m["alpha"].shape
    alpha = m["alpha"]
    ys_a = np.nonzero(alpha.any(1))[0]
    top = ys_a.min()
    # face = skin component touching the front-most silhouette in the head band
    lab, n = ndimage.label(m["skin"])
    cand = []
    for i in range(1, n + 1):
        yy, xx = np.nonzero(lab == i)
        if yy.mean() < 0.22 * H and len(yy) > 150:
            cand.append((xx.mean() * facing, i, yy, xx))
    cand.sort(reverse=True)
    _, fi, fy, fx = cand[0]
    face = lab == fi
    ear = None
    front_x = fx.max() if facing > 0 else fx.min()
    for _, i, yy, xx in cand[1:]:
        behind = (front_x - xx.mean()) * facing
        if behind > 0.6 * (fy.max() - fy.min()) and fy.min() <= yy.mean() <= fy.max():
            if ear is None or len(yy) > len(ear[0]):
                ear = (yy, xx)
    eyes = eye_regions(m, fx.min() - 4, fx.max() + 5, fy.min() - 4, int(fy.min() + 0.55 * (fy.max() - fy.min())), pad=8)
    assert eyes, "eye opening not found in side view"
    e = eyes[0]
    vy, vx = e["iris"]
    sy, sx = e["sclera"]
    out = {}
    sfx = "R" if facing > 0 else "L"
    out[f"pupil_{sfx}"] = pt(vx.mean(), vy.mean(), "MEASURED", "centroid of violet iris pixels in the eye box")
    bi_ = np.argmin(sx * facing)
    out[f"eye_outer_{sfx}"] = pt(sx[bi_], sy[bi_], "MEASURED", "back-most sclera pixel (outer corner in profile)")
    eye_y = vy.mean()
    # profile = front-most face skin pixel per row
    prof = {}
    for y in range(int(eye_y), fy.max() + 1):
        xs_r = np.nonzero(face[y])[0]
        if len(xs_r):
            prof[y] = xs_r.max() if facing > 0 else xs_r.min()
    rows = sorted(prof)
    fwd = lambda y: prof[y] * facing  # noqa: E731
    chin_y = fy.max()
    chin_rows = [y for y in rows if y >= chin_y - 3]
    cy = max(chin_rows, key=fwd)
    out["menton"] = pt(prof[cy], cy, "MEASURED", "lowest face-skin rows (jaw line separates neck): front-most pixel")
    U = cy - eye_y
    nose_rows = [y for y in rows if eye_y + 0.15 * U < y < eye_y + 0.7 * U]
    ny = max(nose_rows, key=fwd)
    out["pronasale"] = pt(prof[ny], ny, "MEASURED", "front-most face-skin profile pixel 0.15U-0.7U below eye line")
    # lip seam: darkest pixel 2-12 px behind the profile between 0.25U below the nose tip and 0.15U above the chin
    best = None
    for y in rows:
        if not (ny + 0.25 * U < y < cy - 0.15 * U):
            continue
        xs_ = [prof[y] - facing * d for d in range(2, 13)]
        for x in xs_:
            if face[y, x] or m["skin"][y, x]:
                if best is None or m["v"][y, x] < best[0]:
                    best = (m["v"][y, x], x, y)
    if best:
        out["stomion"] = pt(best[1], best[2], "ESTIMATED",
                            "lip seam drawn as a short low-contrast line: darkest skin pixel 2-12 px behind profile")
    out["nasion"] = pt(None, None, None, "profile above the eye line is covered by bangs")
    if ear:
        yy, xx = ear
        out[f"ear_center_{sfx}"] = pt(xx.mean(), yy.mean(), "MEASURED", "centroid of skin island enclosed by hair")
        out[f"ear_top_{sfx}"] = pt(xx[yy == yy.min()].mean(), yy.min(), "MEASURED", "ear island top")
        out[f"ear_bottom_{sfx}"] = pt(xx[yy == yy.max()].mean(), yy.max(), "MEASURED", "ear island bottom")
    else:
        out[f"ear_center_{sfx}"] = pt(None, None, None, "no enclosed ear skin island found")
    out["hair_top"] = pt(np.nonzero(alpha[top])[0].mean(), top, "MEASURED", "topmost opaque pixel")
    xs_head = np.nonzero(alpha[top:int(eye_y)].any(0))[0]
    out["hair_back"] = {"px": [float(xs_head.min() if facing > 0 else xs_head.max()), None],
                        "status": "MEASURED", "uncertainty_px": PIXEL_UNCERTAINTY,
                        "method": "back-most opaque column above the eye line (x only)"}
    return out, {"U_px": float(U), "eye_line_y": float(eye_y),
                 "profile_rows": [[int(y), int(prof[y])] for y in rows]}


def back(a):
    m = masks(a)
    H, _ = m["alpha"].shape
    alpha = m["alpha"]
    top = np.nonzero(alpha.any(1))[0].min()
    out = {"hair_top": pt(np.nonzero(alpha[top])[0].mean(), top, "MEASURED", "topmost opaque pixel")}
    head_rows = range(top, int(0.25 * H))
    widths = [(y, *np.nonzero(alpha[y])[0][[0, -1]]) for y in head_rows if alpha[y].any()]
    wy = max(widths, key=lambda w: w[2] - w[1])
    out["hair_max_width_left"] = pt(wy[1], wy[0], "MEASURED", "widest hair row, image-left (character left in back view)")
    out["hair_max_width_right"] = pt(wy[2], wy[0], "MEASURED", "widest hair row, image-right")
    lab, n = ndimage.label(m["skin"])
    nape = None
    for i in range(1, n + 1):
        yy, xx = np.nonzero(lab == i)
        if len(yy) > 150 and yy.min() < 0.3 * H:
            if nape is None or yy.min() < nape[0].min():
                nape = (yy, xx)
    if nape:
        yy, xx = nape
        out["nape_hair_edge"] = pt(xx[yy == yy.min()].mean(), yy.min(), "MEASURED", "top of visible neck skin under hair")
    out["ear_center_R"] = pt(None, None, None, "covered by hair in back view")
    out["ear_center_L"] = pt(None, None, None, "covered by hair in back view")
    return out, {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"task_id": "MORWEN-HEAD-LANDMARK-02", "coordinate_frame": "image px, x right, y down",
           "pixel_uncertainty_px": PIXEL_UNCERTAINTY, "views": {}}
    a, meta = load("front")
    lm_, extra = front(a)
    res["views"]["front"] = {"source": meta, "landmarks": lm_, **extra}
    for view, facing in (("right", 1), ("left", -1)):
        a, meta = load(view)
        lm_, extra = side(a, facing)
        res["views"][view] = {"source": meta, "facing_image_direction": facing, "landmarks": lm_, **extra}
    a, meta = load("back")
    lm_, extra = back(a)
    res["views"]["back"] = {"source": meta, "landmarks": lm_, **extra}
    Us = {v: res["views"][v].get("U_px") for v in ("front", "right", "left")}
    res["scale_consistency"] = {"U_px_by_view": Us,
                                "max_relative_spread": round((max(Us.values()) - min(Us.values())) / Us["front"], 4),
                                "note": "U = chin y - eye-line y in px; same sheet scale is assumed only if spread is small"}
    (OUT / "CANONICAL_LANDMARKS_2D.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    print("canonical 2D landmarks written; U px:", Us)


if __name__ == "__main__":
    main()
