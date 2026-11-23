"""Research: algorithmic re-measurement of Layer0 front face points (read-only).

Replaces manual ESTIMATED clicks (+-3 px) with deterministic pixel measurements
(OFFICIAL_SOURCE_MEASURED) whose uncertainty is the measured sensitivity to the
segmentation parameters (half range over a fixed sweep) plus 0.5 px for
pixel quantisation / anti-aliasing. Manual points are used only to place search
windows, never as values. Definitions are chosen to match the VRoid adapter:
  eye opening = sclera (white) + iris pixels, inclusive x extent per side
  iris centre = centroid of purple iris pixels
  chin        = darkest outline row on the centre columns below the mouth (sub-pixel)
  crown       = topmost alpha crossing (sub-pixel), like the alpha bbox
Never infers depth. The source image stays private (no pixels are exported).
"""
import colorsys
from itertools import product

from PIL import Image

Q = 0.5   # quantisation / anti-aliasing term (px)


def _load(path):
    image = Image.open(path).convert("RGBA")
    return image, image.load()


def _hsv(px):
    r, g, b, a = px
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s, v, a / 255


def _component(mask, seed_points):
    """Largest 4-connected component touching any seed region."""
    seen, best = set(), set()
    for start in mask:
        if start in seen:
            continue
        stack, comp = [start], set()
        while stack:
            p = stack.pop()
            if p in seen or p not in mask:
                continue
            seen.add(p)
            comp.add(p)
            x, y = p
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        if len(comp) > len(best) and (not seed_points or comp & seed_points):
            best = comp
    return best


def eye(path, roi, sweep=None):
    """roi=(x0, y0, x1, y1) inclusive search window for one eye."""
    _, px = _load(path)
    # measured on the source: sclera S 0.06-0.13 / V >= 0.8; skin S ~0.21-0.24 (excluded);
    # iris hue 275-298 deg, S >= 0.45, V 0.15-0.62; hair hue ~303-305, S ~0.35 (excluded)
    sweep = sweep or dict(white_v=(0.78, 0.82, 0.86), white_s=(0.09, 0.12, 0.15),
                          iris_s=(0.45, 0.55, 0.65))
    widths, lefts, rights, irises = [], [], [], []
    for wv, ws, is_ in product(sweep["white_v"], sweep["white_s"], sweep["iris_s"]):
        iris, opening = set(), set()
        for x in range(roi[0], roi[2] + 1):
            for y in range(roi[1], roi[3] + 1):
                h, s, v, a = _hsv(px[x, y])
                if a < 0.5:
                    continue
                if 275 <= h <= 298 and s >= is_ and v >= 0.08:
                    iris.add((x, y))
                    opening.add((x, y))
                elif v >= wv and s <= ws:
                    opening.add((x, y))
        iris = _component(iris, None)
        opening = _component(opening, iris)
        if not iris or not opening:
            continue
        xs = [p[0] for p in opening]
        lefts.append(min(xs))
        rights.append(max(xs))
        widths.append(max(xs) - min(xs) + 1)
        irises.append(sum(p[0] for p in iris) / len(iris))
    if not widths:
        raise ValueError("eye segmentation failed in ROI " + repr(roi))
    mid = lambda v: (min(v) + max(v)) / 2
    half = lambda v: (max(v) - min(v)) / 2
    return dict(width=mid(widths), width_u=half(widths) + 2 * Q, left=mid(lefts),
                left_u=half(lefts) + Q, right=mid(rights), right_u=half(rights) + Q,
                iris_x=mid(irises), iris_u=half(irises) + Q, sweep_runs=len(widths))


def chin(path, x_centre, y_range, half_widths=(0, 1, 2, 4)):
    _, px = _load(path)
    found = []
    for hw in half_widths:
        lum = {}
        for y in range(y_range[0], y_range[1] + 1):
            vals = [_hsv(px[x, y])[2] for x in range(x_centre - hw, x_centre + hw + 1)]
            lum[y] = sum(vals) / len(vals)
        y0 = min(lum, key=lum.get)
        a, b, c = lum.get(y0 - 1, lum[y0]), lum[y0], lum.get(y0 + 1, lum[y0])
        den = a - 2 * b + c
        found.append(y0 + (0.5 * (a - c) / den if den > 0 else 0.0))
    return dict(y=(min(found) + max(found)) / 2, u=(max(found) - min(found)) / 2 + Q,
                runs=len(found))


def crown(path, thresholds=(0.25, 0.5, 0.75)):
    image, px = _load(path)
    width, height = image.size
    found = []
    for t in thresholds:
        best = None
        for x in range(width):
            prev = 0.0
            for y in range(height):
                a = px[x, y][3] / 255
                if a >= t:
                    yy = y - 1 + (t - prev) / (a - prev) if y and a > prev else float(y)
                    best = yy if best is None else min(best, yy)
                    break
                prev = a
        found.append(best)
    return dict(y=(min(found) + max(found)) / 2, u=(max(found) - min(found)) / 2 + Q,
                runs=len(found))


def remeasure(path, manual):
    """manual: face_front_review points (search windows only)."""
    pts = manual
    out = {}
    for side, outer, inner in (("left", "left_outer_eye", "left_inner_eye"),
                               ("right", "right_inner_eye", "right_outer_eye")):
        xs = (pts[outer][0], pts[inner][0])
        ys = (pts[outer][1], pts[inner][1])
        roi = (min(xs) - 8, min(ys) - 12, max(xs) + 8, max(ys) + 16)
        out[side] = eye(path, roi)
    out["chin"] = chin(path, pts["chin"][0], (pts["chin"][1] - 10, pts["chin"][1] + 10))
    out["crown"] = crown(path)
    head = out["chin"]["y"] - out["crown"]["y"]
    head_u = out["chin"]["u"] + out["crown"]["u"]
    L, R = out["left"], out["right"]
    dists = dict(
        eye_width_left=(L["width"], L["width_u"]),
        eye_width_right=(R["width"], R["width_u"]),
        iris_center_distance=(R["iris_x"] - L["iris_x"], R["iris_u"] + L["iris_u"]),
        inner_eye_gap=(R["left"] - L["right"], R["left_u"] + L["right_u"]))
    ratios = {k: dict(px=d, u_px=u, ratio=d / head, u=u / head + abs(d) * head_u / head ** 2)
              for k, (d, u) in dists.items()}
    return dict(points=out, head_px=head, head_u_px=head_u, ratios=ratios)
