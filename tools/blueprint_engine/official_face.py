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


def eyeline(path, roi, iris_x, sweep=None):
    """Upper lash line (eyeline) extent with a contrast-relative threshold.

    Stroke pixel: warm hue (outside hair 298-330 / iris 275-298), S >= 0.15 and
    V < skin_V - k * (skin_V - core_V), where skin_V is the ROI median skin value
    and core_V the 5th-percentile stroke value (k = 0.5 is a half-contrast edge).
    The component spanning the iris column gives the illustrated eye corners,
    matching VRoid FaceEyeline extent rather than the sclera opening. If the
    corner candidates split into separate clusters (> 3 px apart) the corner is
    reported as DEFINITION_AMBIGUOUS (e.g. a faint taper vs the main stroke).
    """
    _, px = _load(path)
    sweep = sweep or dict(k=(0.45, 0.5, 0.55), hue_lo=(325, 330, 335), hue_hi=(30, 40, 50))
    pix = [(x, y, *_hsv(px[x, y])) for x in range(roi[0], roi[2] + 1)
           for y in range(roi[1], roi[3] + 1)]
    skin = sorted(v for *_, h, s, v, a in pix if 8 <= h <= 35 and 0.12 <= s <= 0.32 and v > 0.8)
    warm = sorted(v for *_, h, s, v, a in pix if (h >= 330 or h <= 40) and s >= 0.15)
    if not skin or not warm:
        raise ValueError("eyeline reference values unavailable in ROI " + repr(roi))
    skin_v, core_v = skin[len(skin) // 2], warm[len(warm) // 20]
    lefts, rights = [], []
    for k, lo, hi in product(sweep["k"], sweep["hue_lo"], sweep["hue_hi"]):
        v_max = skin_v - k * (skin_v - core_v)
        mask = {(x, y) for x, y, h, s, v, a in pix
                if a >= 0.5 and v < v_max and (h >= lo or h <= hi) and s >= 0.15}
        seeds = {p for p in mask if abs(p[0] - iris_x) <= 2}
        comp = _component(mask, seeds)
        if comp and comp & seeds:
            xs = [p[0] for p in comp]
            lefts.append(min(xs))
            rights.append(max(xs))
    if not lefts:
        raise ValueError("eyeline segmentation failed in ROI " + repr(roi))
    mid = lambda v: (min(v) + max(v)) / 2
    half = lambda v: (max(v) - min(v)) / 2

    def clusters(values):
        values = sorted(set(values))
        groups = [[values[0], values[0]]]
        for v in values[1:]:
            if v - groups[-1][1] <= 3:
                groups[-1][1] = v
            else:
                groups.append([v, v])
        return groups

    widths = [r - l + 1 for l, r in zip(lefts, rights)]
    return dict(left=mid(lefts), left_u=half(lefts) + Q, right=mid(rights),
                right_u=half(rights) + Q, width=mid(widths), width_u=half(widths) + 2 * Q,
                left_candidates=clusters(lefts), right_candidates=clusters(rights),
                ambiguous=[s for s, v in (("left", lefts), ("right", rights))
                           if len(clusters(v)) > 1],
                skin_v=skin_v, core_v=core_v, runs=len(lefts))


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
    for side, outer, inner in (("left", "left_outer_eye", "left_inner_eye"),
                               ("right", "right_inner_eye", "right_outer_eye")):
        xs = (pts[outer][0], pts[inner][0])
        y = min(pts[outer][1], pts[inner][1])
        out[side + "_eyeline"] = eyeline(path, (min(xs) - 10, y - 10, max(xs) + 10, y + 2),
                                         out[side]["iris_x"])
    out["chin"] = chin(path, pts["chin"][0], (pts["chin"][1] - 10, pts["chin"][1] + 10))
    out["crown"] = crown(path)
    head = out["chin"]["y"] - out["crown"]["y"]
    head_u = out["chin"]["u"] + out["crown"]["u"]
    L, R = out["left"], out["right"]
    LE, RE = out["left_eyeline"], out["right_eyeline"]
    dists = dict(
        eye_width_left=(LE["width"], LE["width_u"]),
        eye_width_right=(RE["width"], RE["width_u"]),
        iris_center_distance=(R["iris_x"] - L["iris_x"], R["iris_u"] + L["iris_u"]),
        inner_eye_gap=(RE["left"] - LE["right"], RE["left_u"] + LE["right_u"]),
        sclera_width_left=(L["width"], L["width_u"]),
        sclera_width_right=(R["width"], R["width_u"]))
    ratios = {k: dict(px=d, u_px=u, ratio=d / head, u=u / head + abs(d) * head_u / head ** 2)
              for k, (d, u) in dists.items()}
    return dict(points=out, head_px=head, head_u_px=head_u, ratios=ratios)
