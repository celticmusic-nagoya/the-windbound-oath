"""Occlusion-invariant VRoid hair-guide support measurement (independent analysis, W121A).

Read-only image analysis. No GUI operation, no native file access, no network.

Why: the W107/W108/W110 support test measures the Chebyshev distance from each
projected blueprint point to *currently visible* colour-keyed guide wire pixels.
Strands already drawn are rendered over the guide and hide wire pixels, so the
old metric degrades as production advances, even when the guide geometry is
unchanged (see ANALYSIS_W121A_JA.md, real W108 sequence 1795 -> 1202 pixels).

This module separates two questions that the old metric conflated:
  1. Is the guide geometry unchanged?  Compare live visible wire pixels with a
     clean reference wire mask mapped through the measured camera registration.
     Live pixels must be (almost) a subset of the mapped reference; pixels that
     disappeared must be explained by occlusion, not by a moved guide.
  2. Does the guide surface support the path?  Use the *filled* silhouette of
     the clean reference guide (wire cells closed and holes filled), because a
     brush stroke projects onto the guide surface, not onto its wire lines.

Decision rule (repository policy): residual r, uncertainty u, tolerance t.
PASS if r+u <= t, OUTSIDE if r-u > t, otherwise HOLD.  Here r is the worst
signed distance of a path point from the silhouette boundary (negative = inside),
t = -margin (required inside depth) and u covers registration and pixel
quantisation.  This is a 2D screen-space proxy, not a 3D contact certificate.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

SCREEN = (1024, 768)
VIEW = (315, 170, 710, 685)  # x0, y0, x1(excl), y1(excl) editor viewport used by W107/W108
GUIDE_KEY = ((194, 8), (217, 8), (65, 12))  # identical colour key to W107/W108


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_rgb(path) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    if im.size != SCREEN:
        raise ValueError("screen resolution")
    return np.asarray(im, dtype=np.int16)


def guide_mask(rgb: np.ndarray) -> np.ndarray:
    """Exact W107/W108 colour key restricted to the same viewport."""
    m = np.ones(rgb.shape[:2], bool)
    for c, (v, tol) in enumerate(GUIDE_KEY):
        m &= np.abs(rgb[:, :, c] - v) <= tol
    view = np.zeros_like(m)
    x0, y0, x1, y1 = VIEW
    view[y0:y1, x0:x1] = True
    return m & view


def map_mask(mask: np.ndarray, ref_reg: dict, live_reg: dict) -> np.ndarray:
    """Map a reference-screen mask into the live screen with the measured
    similarity transform (centre + uniform scale).  Nearest-pixel forward map
    followed by a 1 px closing to avoid holes from rounding."""
    (rcx, rcy), rs = ref_reg["center_px"], ref_reg["scale"]
    (lcx, lcy), ls = live_reg["center_px"], live_reg["scale"]
    k = ls / rs
    ys, xs = np.nonzero(mask)
    X = np.rint(lcx + (xs - rcx) * k).astype(int)
    Y = np.rint(lcy + (ys - rcy) * k).astype(int)
    ok = (X >= 0) & (X < SCREEN[0]) & (Y >= 0) & (Y < SCREEN[1])
    out = np.zeros_like(mask)
    out[Y[ok], X[ok]] = True
    if abs(k - 1) > 1e-9:
        out = ndimage.binary_closing(out, np.ones((3, 3), bool))
    return out


def filled_silhouette(wire: np.ndarray, close_px: int) -> np.ndarray:
    """Close the wire grid cells and fill holes -> projected guide surface."""
    st = ndimage.generate_binary_structure(2, 1)
    closed = ndimage.binary_closing(wire, st, iterations=close_px, border_value=0)
    filled = ndimage.binary_fill_holes(closed)
    # keep components touching wire only (closing cannot create islands, but be explicit)
    lab, n = ndimage.label(filled)
    keep = np.zeros(n + 1, bool)
    keep[np.unique(lab[wire & filled])] = True
    keep[0] = False
    return keep[lab]


def grid_spacing(wire: np.ndarray) -> float:
    """Median spacing between wire runs along rows inside the guide bbox."""
    ys, xs = np.nonzero(wire)
    if len(xs) == 0:
        return float("nan")
    gaps = []
    for y in range(ys.min(), ys.max() + 1):
        row = np.nonzero(wire[y])[0]
        if len(row) < 2:
            continue
        d = np.diff(row)
        gaps.extend(d[d > 1].tolist())
    return float(np.median(gaps)) if gaps else float("nan")


def signed_distance(sil: np.ndarray) -> np.ndarray:
    """Euclidean signed distance (px): negative inside, positive outside."""
    inside = ndimage.distance_transform_edt(sil)
    outside = ndimage.distance_transform_edt(~sil)
    return np.where(sil, -(inside - 0.5), outside - 0.5)


def lane_path(blueprint: dict, lane: str, reg: dict, step: float = 2.4):
    """Identical projection and 2.4 px resampling to W107/W108."""
    (cx, cy), s = reg["center_px"], reg["scale"] * 29 / 51
    t, = [g for g in blueprint["view_lanes"]["front"] if g["id"] == lane]
    ctl = [(cx + (x - 212.5) * s, cy + (y - 125) * s) for x, y in t["points_px"]]
    path = [ctl[0]]
    for a, b in zip(ctl, ctl[1:]):
        n = max(1, math.ceil(math.dist(a, b) / step))
        path.extend((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1))
    return path


def legacy_distance(wire: np.ndarray, path) -> list[int]:
    """Reproduction of the W108 Chebyshev distance to the nearest visible wire pixel."""
    ys, xs = np.nonzero(wire)
    out = []
    for x, y in path:
        X, Y = round(x), round(y)
        out.append(int(np.min(np.maximum(np.abs(xs - X), np.abs(ys - Y)))))
    return out


def sample(field: np.ndarray, x: float, y: float) -> float:
    """Bilinear sample of a distance field."""
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - x0, y - y0
    f = field
    return float((1 - fx) * (1 - fy) * f[y0, x0] + fx * (1 - fy) * f[y0, x0 + 1]
                 + (1 - fx) * fy * f[y0 + 1, x0] + fx * fy * f[y0 + 1, x0 + 1])


def decide(r: float, u: float, t: float) -> str:
    if r + u <= t:
        return "PASS"
    if r - u > t:
        return "OUTSIDE"
    return "HOLD"


def analyse(reference_png, reference_reg, live_png, live_reg, blueprint, lanes,
            margin_px: float = 1.0, uncertainty_px: float | None = None,
            moved_px_limit: int = 12, moved_dilate: int = 1,
            min_on_wire_fraction: float = 0.9) -> dict:
    rreg = json.loads(Path(reference_reg).read_text())
    lreg = json.loads(Path(live_reg).read_text())
    bp = json.loads(Path(blueprint).read_text())
    ref_wire = guide_mask(load_rgb(reference_png))
    live_wire = guide_mask(load_rgb(live_png))
    if not 250 <= ref_wire.sum() <= 45000:
        raise ValueError("reference guide not established")
    mapped = map_mask(ref_wire, rreg, lreg)
    # 1. Guide geometry consistency: live wire must lie on the mapped reference wire.
    near = ndimage.binary_dilation(mapped, iterations=moved_dilate)
    stray = live_wire & ~near
    occluded = mapped & ~ndimage.binary_dilation(live_wire, iterations=moved_dilate)
    # A dense grid makes any shifted grid look 'near' a wire, so require that the live
    # visible wire lies on the mapped wire (+-1 px) almost everywhere, and never outside
    # the mapped silhouette.  Occlusion only removes pixels, it never moves them.
    on_wire = float((live_wire & near).sum() / max(1, live_wire.sum()))
    geometry = ("UNCHANGED" if stray.sum() <= moved_px_limit and on_wire >= min_on_wire_fraction
                else "MOVED_OR_NEW_GUIDE")
    # 2. Surface support on the filled clean silhouette.
    spacing = grid_spacing(mapped)
    close_px = int(math.ceil((spacing if math.isfinite(spacing) else 6) / 2)) + 1
    sil = filled_silhouette(mapped, close_px)
    sdf = signed_distance(sil)
    outside_sil = int((live_wire & ~ndimage.binary_dilation(sil, iterations=1)).sum())
    if outside_sil > moved_px_limit:
        geometry = "MOVED_OR_NEW_GUIDE"
    k = lreg["scale"] / rreg["scale"]
    if uncertainty_px is None:
        # 0.5 px registration grid (W110 uses 0.5 px fine steps) + 0.5 px pixel quantisation
        # + boundary blur of the closing (half a grid cell at most is already absorbed by fill).
        uncertainty_px = 1.0
    lanes_out = {}
    for lane in lanes:
        path = lane_path(bp, lane, lreg)
        d = [sample(sdf, x, y) for x, y in path]
        legacy = legacy_distance(live_wire, path)
        r = max(d)
        lanes_out[lane] = dict(
            points=len(path), worst_signed_distance_px=round(r, 3),
            min_inside_depth_px=round(-r, 3),
            verdict=decide(r, uncertainty_px, -margin_px),
            legacy_max_chebyshev_px=max(legacy),
            legacy_unsupported_at_5px=sum(v > 5 for v in legacy),
            root_signed_distance_px=round(d[0], 3), tip_signed_distance_px=round(d[-1], 3))
    if geometry != "UNCHANGED":
        for v in lanes_out.values():
            v["verdict"] = "HOLD_GUIDE_GEOMETRY"
    ys, xs = np.nonzero(sil)
    return dict(
        schema="morwen_guide_support_v2_w121a",
        status="INDEPENDENT_2D_SCREEN_PROXY_NOT_3D_CONTACT",
        reference_sha256=sha256(reference_png), live_sha256=sha256(live_png),
        camera_scale_ratio=round(k, 6),
        reference_wire_px=int(ref_wire.sum()), mapped_wire_px=int(mapped.sum()),
        live_wire_px=int(live_wire.sum()),
        visible_fraction=round(float((live_wire & near).sum()) / max(1.0, float(ref_wire.sum()) * k * k), 4),
        occluded_wire_px=int(occluded.sum()), stray_live_wire_px=int(stray.sum()),
        live_on_mapped_wire_fraction=round(on_wire, 4), live_wire_outside_silhouette_px=outside_sil,
        guide_geometry=geometry, wire_grid_spacing_px=spacing, silhouette_close_px=close_px,
        silhouette_px=int(sil.sum()),
        silhouette_bounds_px=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        margin_px=margin_px, uncertainty_px=uncertainty_px, tolerance_rule="PASS r+u<=-margin; OUTSIDE r-u>-margin; else HOLD",
        lanes=lanes_out)


def main(argv):
    if len(argv) < 6:
        raise SystemExit("usage: guide_support_v2.py REF.png REF_REG.json LIVE.png LIVE_REG.json BLUEPRINT.json OUT.json [LANE ...]")
    ref, rreg, live, lreg, bp, out, *lanes = argv
    lanes = lanes or ["F01", "F02", "F03", "F04", "F05", "F06"]
    res = analyse(ref, rreg, live, lreg, bp, lanes)
    with Path(out).open("x") as f:
        json.dump(res, f, indent=2)
    print(json.dumps({k: v["verdict"] for k, v in res["lanes"].items()}))


if __name__ == "__main__":
    main(sys.argv[1:])
