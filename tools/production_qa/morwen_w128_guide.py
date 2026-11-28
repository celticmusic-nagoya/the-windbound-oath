"""W128 Claude: independent new Freehand guide (G2) measurement and guards.

Runner-side, numpy + Pillow only (no scipy).  Read-only image analysis; GUI actions stay
in the shell worker.  Method from W121A (tools/morwen_hair_analysis/guide_support_v2.py):
filled guide silhouette, signed distance, r/u/t.  Empirical projection evidence:
W120 F06 drew COMPLETE at r=+4.3 px; W108 F01 truncated where r>=+5 px.  Drawing in a new
group therefore requires r <= DRAW_LIMIT (+2.0 px), a >2 px margin from the observed success.

Commands
  groups  ROWS.json                    -> prints "g1x g1y g2x g2y" normalized; exactly two groups
  guide   PNG ROWS.json REG.json BP.json OUT.json   (G2 selected, brush active)
  points  GUIDE.json LANE              -> normalized stroke arguments
  complete BEFORE.png AFTER.png REG.json BP.json LANE OUT.json   (exit 3 unless COMPLETE)
  newlabel BEFORE.txt AFTER.txt         -> the one new "Hair N" occurrence
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SCREEN = (1024, 768)
VIEW = (315, 170, 710, 685)
KEY = ((194, 8), (217, 8), (65, 12))
LANES = ("F01", "F02", "F03", "F04", "F05", "F06")
DRAW_LANES = ("F06", "F01")
DRAW_LIMIT = 2.0
UNCERTAINTY = 1.0


def require(v, msg):
    if not v:
        raise ValueError(msg)


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rgb(path) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    require(im.size == SCREEN, "screen resolution")
    return np.asarray(im, dtype=np.int16)


def guide_mask(a: np.ndarray) -> np.ndarray:
    m = np.ones(a.shape[:2], bool)
    for c, (v, t) in enumerate(KEY):
        m &= np.abs(a[:, :, c] - v) <= t
    out = np.zeros_like(m)
    x0, y0, x1, y1 = VIEW
    out[y0:y1, x0:x1] = m[y0:y1, x0:x1]
    return out


def _shift_or(m, r):
    out = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if abs(dx) + abs(dy) == 1:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def dilate(m, n):
    for _ in range(n):
        m = _shift_or(m, 1)
    return m


def erode(m, n):
    return ~dilate(~m, n)


def fill_holes(m):
    """Background reachable from the image border via 4-connectivity stays background."""
    bg = ~m
    reach = np.zeros_like(m)
    reach[0, :] = bg[0, :]; reach[-1, :] = bg[-1, :]; reach[:, 0] = bg[:, 0]; reach[:, -1] = bg[:, -1]
    while True:
        nxt = _shift_or(reach, 1) & bg
        if (nxt == reach).all():
            return ~reach
        reach = nxt


def grid_spacing(wire):
    gaps = []
    ys = np.nonzero(wire.any(1))[0]
    for y in ys:
        row = np.nonzero(wire[y])[0]
        if len(row) > 1:
            d = np.diff(row)
            gaps.extend(d[d > 1].tolist())
    return float(np.median(gaps)) if gaps else float("nan")


def silhouette(wire):
    sp = grid_spacing(wire)
    k = int(math.ceil((sp if math.isfinite(sp) else 6) / 2)) + 1
    # crop for speed; padded so closing cannot touch the border
    ys, xs = np.nonzero(wire)
    y0, y1, x0, x1 = max(ys.min() - 3 * k, 0), min(ys.max() + 3 * k + 1, SCREEN[1]), max(xs.min() - 3 * k, 0), min(xs.max() + 3 * k + 1, SCREEN[0])
    w = np.zeros((y1 - y0 + 2, x1 - x0 + 2), bool)
    w[1:-1, 1:-1] = wire[y0:y1, x0:x1]
    closed = erode(dilate(w, k), k)
    filled = fill_holes(closed)
    out = np.zeros_like(wire)
    out[y0:y1, x0:x1] = filled[1:-1, 1:-1]
    return out, sp, k


def signed_distance_at(sil, pts):
    """Exact Euclidean distance to the nearest pixel of the opposite class (pixel centres),
    minus 0.5, negative inside.  Identical convention to the scipy EDT version."""
    ins = np.argwhere(sil)
    outs_y, outs_x = np.nonzero(~sil)
    # restrict outside candidates to a band around the silhouette for speed
    band = dilate(sil, 40) & ~sil
    oy, ox = np.nonzero(band)
    res = []
    for x, y in pts:
        X, Y = int(round(x)), int(round(y))
        if sil[Y, X]:
            d = np.sqrt((oy - y) ** 2 + (ox - x) ** 2).min()
            res.append(float(-(d - 0.5)))
        else:
            d = np.sqrt((ins[:, 0] - y) ** 2 + (ins[:, 1] - x) ** 2).min()
            res.append(float(d - 0.5))
    return res


def lane_path(bp, lane, reg, step=2.4):
    (cx, cy), s = reg["center_px"], reg["scale"] * 29 / 51
    t, = [g for g in bp["view_lanes"]["front"] if g["id"] == lane]
    ctl = [(cx + (x - 212.5) * s, cy + (y - 125) * s) for x, y in t["points_px"]]
    path = [ctl[0]]
    for a, b in zip(ctl, ctl[1:]):
        n = max(1, math.ceil(math.dist(a, b) / step))
        path.extend((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1))
    return path, cy, s


def groups(rows_path):
    d = json.loads(Path(rows_path).read_text())
    labels = [r["label"] for r in d["rows"]]
    require(labels == ["Freehand Group 1", "Freehand Group 2"], "expected exactly G1 and new G2: %r" % labels)
    g1, g2 = d["rows"]
    require(110 <= g1["x"] <= 255 and 110 <= g2["x"] <= 255 and g2["y"] > g1["y"] + 30, "group row geometry")
    return g1, g2


def blue_count(a, x0, x1, y0, y1):
    r, g, b = a[y0:y1, x0:x1, 0], a[y0:y1, x0:x1, 1], a[y0:y1, x0:x1, 2]
    return int(((b > 170) & (g > 80) & (b - r > 90) & (r < 60)).sum())


def guide(png, rows, reg_path, bp_path, out, tool="brush"):
    d = json.loads(Path(rows).read_text())
    require(d["screenshot_sha256"] == sha(png), "stale row capture")
    g1, g2 = groups(rows)
    a = rgb(png)
    y = int(round(g2["y"]))
    require(blue_count(a, 51, 85, y - 10, y + 10) >= 420, "G2 selection not verified")
    require(blue_count(a, 51, 85, int(g1["y"]) - 10, int(g1["y"]) + 10) < 120, "G1 still selected")
    xlo, xhi = (351, 379) if tool == "brush" else (315, 348)
    require(tool in ("brush", "select") and blue_count(a, xlo, xhi, 125, 150) >= 120, "brush inactive" if tool == "brush" else "select tool inactive")
    reg = json.loads(Path(reg_path).read_text())
    require(reg.get("jacket_mae", 99) <= 8 and reg["screenshot_sha256"] == sha(png), "registration identity")
    bp = json.loads(Path(bp_path).read_text())
    require(bp["schema"] == "morwen_hair_blueprint_w92_v1", "design identity")
    wire = guide_mask(a)
    require(250 <= wire.sum() <= 45000, "G2 guide not established")
    sil, sp, k = silhouette(wire)
    ys, xs = np.nonzero(sil)
    lanes = {}
    for lane in LANES:
        path, cy, s = lane_path(bp, lane, reg)
        require(all(315 <= x <= 710 and 170 <= y <= 685 for x, y in path), "path bounds")
        require(max(y for _, y in path) <= cy - 2 * s, "path crosses iris line")
        dist = signed_distance_at(sil, path)
        r = float(max(dist))
        lanes[lane] = dict(points=len(path), worst_signed_distance_px=round(r, 3),
                           root_deficit_px=round(float(max(dist[:3])), 3),
                           body_deficit_px=round(float(max(dist[3:])), 3),
                           outside_fraction=round(float(sum(v > 0 for v in dist)) / len(dist), 3),
                           draw_eligible=lane in DRAW_LANES and r <= DRAW_LIMIT,
                           verdict="PASS" if r + UNCERTAINTY <= -1 else "OUTSIDE" if r - UNCERTAINTY > -1 else "HOLD",
                           normalized_points=[[round(x / 1024, 8), round(y / 768, 8)] for x, y in path])
    res = dict(schema="morwen_w128_g2_guide", status="NEW_INDEPENDENT_GUIDE_MEASURED_2D_PROXY",
               screenshot_sha256=sha(png), guide_wire_px=int(wire.sum()), wire_grid_spacing_px=sp,
               silhouette_close_px=k, silhouette_px=int(sil.sum()),
               silhouette_bounds_px=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
               draw_limit_px=DRAW_LIMIT, uncertainty_px=UNCERTAINTY, registration=str(reg_path),
               g2_row=[g2["x"], g2["y"]], tool=tool, lanes=lanes,
               draw=[l for l in DRAW_LANES if lanes[l]["draw_eligible"]])
    with Path(out).open("x") as f:
        json.dump(res, f, indent=2)
    print(" ".join(res["draw"]) or "NONE")


def points(guide_json, lane):
    d = json.loads(Path(guide_json).read_text())
    require(lane in d["draw"], "lane not eligible")
    pts = d["lanes"][lane]["normalized_points"]
    require(12 <= len(pts) <= 256, "point count")
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        require(0 < math.hypot((x1 - x0) * 1024, (y1 - y0) * 768) <= 3.05, "segment spacing")
    print(" ".join(f"{x:.8f} {y:.8f}" for x, y in pts))


def complete(before, after, reg_path, bp_path, lane, out, window=3, threshold=40, minimum=0.9):
    a, b = rgb(before), rgb(after)
    reg = json.loads(Path(reg_path).read_text())
    bp = json.loads(Path(bp_path).read_text())
    noise = int(np.abs(a[450:560, 450:575] - b[450:560, 450:575]).max())
    path, _, _ = lane_path(bp, lane, reg)
    prof = []
    for x, y in path:
        X, Y = round(x), round(y)
        prof.append(int(np.abs(a[Y - window:Y + window + 1, X - window:X + window + 1]
                               - b[Y - window:Y + window + 1, X - window:X + window + 1]).max()))
    hit = [v > threshold for v in prof]
    start = next((i for i, h in enumerate(hit) if h), None)
    last = -1
    if start is not None:
        last = start
        while last + 1 < len(hit) and hit[last + 1]:
            last += 1
    frac = (last + 1) / len(path) if last >= 0 else 0.0
    verdict = ("HOLD_FRAME_DRIFT" if noise > 0 else "NOT_DRAWN" if start is None else
               "ROOT_GAP" if start > 2 else "COMPLETE" if frac >= minimum else "TRUNCATED")
    res = dict(schema="morwen_w128_stroke_completion", lane=lane, verdict=verdict,
               completion_fraction=round(frac, 4), invariant_region_max_diff=noise,
               first_drawn_index=start, last_contiguous_index=last, points=len(path),
               before_sha256=sha(before), after_sha256=sha(after), per_point_max_diff=prof)
    with Path(out).open("x") as f:
        json.dump(res, f, indent=2)
    print(verdict, res["completion_fraction"])
    return verdict


def newlabel(before, after):
    pat = re.compile(r"\bHair \d+\b")
    b = collections.Counter(pat.findall(Path(before).read_text()))
    a = collections.Counter(pat.findall(Path(after).read_text()))
    require(not (b - a), "existing hair label disappeared")
    diff = a - b
    require(sum(diff.values()) == 1, "expected exactly one new hair label")
    print(next(iter(diff)))


# ---- W129 additions: temporary G1 visibility and W108-qualified crown handles on G2 ----
FRINGE = (480, 318, 545, 380)  # x0, y0, x1, y1 fringe root box at the W108/W128 framing
HANDLES = {"center": (511, 329, 0, -18), "left": (498, 332, 0, -17), "right": (525, 332, 0, -17)}
BASE_CENTER, BASE_SCALE = (511.5, 385.5), 1.28


def hair_px(a, box=FRINGE):
    x0, y0, x1, y1 = box
    r, g, b = a[y0:y1, x0:x1, 0], a[y0:y1, x0:x1, 1], a[y0:y1, x0:x1, 2]
    return int(((r - g >= 20) & (b - g >= 20) & (np.abs(r - b) <= 20) & (r < 170)).sum())


def eye(png, rows_path, group):
    """Normalized click point of an unselected group's eye icon, verified on pixels."""
    d = json.loads(Path(rows_path).read_text())
    require(d["screenshot_sha256"] == sha(png), "stale row capture")
    g1, g2 = groups(rows_path)
    row = g1 if group == "1" else g2
    a = rgb(png)
    x, y = 275, int(round(row["y"])) + 8
    patch = a[y - 6:y + 7, x - 8:x + 9].sum(2)
    bg = float(np.median(patch))
    require(bg >= 700, "eye row is selected or not on a white row")
    dark = int((patch < bg - 60).sum())
    require(25 <= dark <= 160, "eye icon not verified (%d)" % dark)
    print(f"{x/1024:.8f} {y/768:.8f}")


def hidden(before, after):
    a, b = hair_px(rgb(before)), hair_px(rgb(after))
    require(a >= 300 and b <= 0.4 * a, "G1 strands not hidden (%d -> %d)" % (a, b))
    print(a, b)


def shown(prehide, hidden_png, preshow, after):
    """Restoration measured in the same overlay state: the gain on re-show must be at least
    60% of the loss observed when G1 was hidden."""
    a, h, p, b = (hair_px(rgb(x)) for x in (prehide, hidden_png, preshow, after))
    loss = a - h
    require(loss >= 200, "hide loss not established")
    require(b - p >= 0.6 * loss, "G1 strands not restored (gain %d, loss %d)" % (b - p, loss))
    print(a, h, p, b)


def handle(png, rows_path, reg_path, which):
    d = json.loads(Path(rows_path).read_text())
    require(d["screenshot_sha256"] == sha(png), "stale row capture")
    g1, g2 = groups(rows_path)
    a = rgb(png)
    y2 = int(round(g2["y"]))
    require(blue_count(a, 51, 85, y2 - 10, y2 + 10) >= 420, "G2 selection not verified")
    require(blue_count(a, 315, 348, 125, 150) >= 120, "select tool inactive")
    f = json.loads(Path(reg_path).read_text())
    require(f["screenshot_sha256"] == sha(png) and f.get("jacket_mae", 99) <= 8, "registration identity")
    x, y, dx, dy = HANDLES[which]
    cx, cy = f["center_px"]
    ratio = f["scale"] / BASE_SCALE
    x = round(cx + (x - BASE_CENTER[0]) * ratio)
    y = round(cy + (y - BASE_CENTER[1]) * ratio)
    require(460 <= x <= 565 and 280 <= y <= 365 and .75 <= ratio <= 1.5, "unqualified crown location")
    white = a.min(2) >= 245
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g > 145) & (g - r > 60) & (g - b > 50)
    cands = []
    for yy in range(y - 4, y + 5):
        for xx in range(x - 4, x + 5):
            nw = int(white[yy - 1:yy + 2, xx - 1:xx + 2].sum())
            ng = int(green[yy - 6:yy + 7, xx - 6:xx + 7].sum())
            if nw >= 7 and ng >= 7:
                cands.append((math.dist((x, y), (xx, yy)), -nw, -ng, xx, yy))
    require(cands, "expected crown control point not visible")
    _, _, _, hx, hy = min(cands)
    tx, ty = round(hx + dx * ratio), round(hy + dy * ratio)
    require(450 <= tx <= 575 and 250 <= ty <= 365 and 10 <= hy - ty <= 27, "bounded crown movement")
    print(f"{hx/1024:.8f} {hy/768:.8f} {tx/1024:.8f} {ty/768:.8f} 0.65")


def control_points(a):
    """White control-point blobs (min channel >= 245) with a green rim inside the viewport."""
    x0, y0, x1, y1 = VIEW
    white = np.zeros(a.shape[:2], bool)
    white[y0:y1, x0:x1] = a[y0:y1, x0:x1].min(2) >= 245
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g > 145) & (g - r > 60) & (g - b > 50)
    seen = np.zeros_like(white)
    pts = []
    for sy, sx in zip(*np.nonzero(white)):
        if seen[sy, sx]:
            continue
        stack, comp = [(sy, sx)], []
        seen[sy, sx] = True
        while stack:
            y, x = stack.pop()
            comp.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if white[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if not 6 <= len(comp) <= 80:
            continue
        cy = sum(p[0] for p in comp) / len(comp)
        cx = sum(p[1] for p in comp) / len(comp)
        ring = int(green[int(cy) - 7:int(cy) + 8, int(cx) - 7:int(cx) + 8].sum())
        if ring >= 8:
            pts.append((cx, cy, len(comp), ring))
    return sorted(pts, key=lambda t: (t[1], t[0]))


def crown(png, rows_path, reg_path, guide_json, out, margin=2.0, max_lift=27.0):
    """Lift for the three top control points so every lane root gets r <= -margin.
    Measured lift = worst root signed distance + margin, bounded; drags returned one per line."""
    d = json.loads(Path(rows_path).read_text())
    require(d["screenshot_sha256"] == sha(png), "stale row capture")
    g1, g2 = groups(rows_path)
    a = rgb(png)
    y2 = int(round(g2["y"]))
    require(blue_count(a, 51, 85, y2 - 10, y2 + 10) >= 420, "G2 selection not verified")
    require(blue_count(a, 315, 348, 125, 150) >= 120, "select tool inactive")
    f = json.loads(Path(reg_path).read_text())
    require(f["screenshot_sha256"] == sha(png) and f.get("jacket_mae", 99) <= 8, "registration identity")
    gd = json.loads(Path(guide_json).read_text())
    require(gd["screenshot_sha256"] == sha(png) and gd.get("tool") == "select", "guide measurement identity")
    ratio = f["scale"] / BASE_SCALE
    pts = control_points(a)
    require(len(pts) >= 12, "control points not established (%d)" % len(pts))
    top = min(p[1] for p in pts)
    row = sorted([p for p in pts if p[1] <= top + 4], key=lambda p: p[0])
    cx = f["center_px"][0]
    require(len(row) == 3 and abs(row[1][0] - cx) <= 6 * ratio and row[0][0] < row[1][0] < row[2][0], "crown row not unique: %r" % (row,))
    require(all(460 <= p[0] <= 565 and 280 <= p[1] <= 380 for p in row), "unqualified crown location")
    need = max(gd["lanes"][l]["root_deficit_px"] for l in LANES)
    lift = need + margin
    require(lift > 0.5, "no crown lift needed")
    require(lift <= max_lift * ratio, "lift %.1f exceeds bound" % lift)
    drags = [[p[0] / 1024, p[1] / 768, p[0] / 1024, (p[1] - lift) / 768, 0.65] for p in (row[1], row[0], row[2])]
    res = dict(schema="morwen_w130_crown_lift", screenshot_sha256=sha(png), control_points=len(pts),
               crown_row=[[round(p[0], 1), round(p[1], 1)] for p in row], worst_lane_px=need,
               lift_px=round(lift, 2), ratio=ratio, drags=drags)
    with Path(out).open("x") as fo:
        json.dump(res, fo, indent=2)
    for dr in drags:
        print(" ".join(f"{v:.8f}" for v in dr))


def shoulder(png, rows_path, reg_path, guide_json, out, margin=2.0, max_move=10.0):
    """Move the second-row shoulder control points outward-up (unit (-+0.6, -0.8)) by the flank
    lane body deficit + margin (F01 -> left, F06 -> right), bounded. One drag per needy side."""
    d = json.loads(Path(rows_path).read_text())
    require(d["screenshot_sha256"] == sha(png), "stale row capture")
    g1, g2 = groups(rows_path)
    a = rgb(png)
    y2 = int(round(g2["y"]))
    require(blue_count(a, 51, 85, y2 - 10, y2 + 10) >= 420, "G2 selection not verified")
    require(blue_count(a, 315, 348, 125, 150) >= 120, "select tool inactive")
    f = json.loads(Path(reg_path).read_text())
    require(f["screenshot_sha256"] == sha(png) and f.get("jacket_mae", 99) <= 8, "registration identity")
    gd = json.loads(Path(guide_json).read_text())
    require(gd["screenshot_sha256"] == sha(png) and gd.get("tool") == "select", "guide measurement identity")
    ratio = f["scale"] / BASE_SCALE
    cx = f["center_px"][0]
    pts = control_points(a)
    require(len(pts) >= 12, "control points not established")
    top = min(p[1] for p in pts)
    drags, sides = [], {}
    for side, lane, sgn in (("left", "F01", -1), ("right", "F06", 1)):
        deficit = gd["lanes"][lane]["body_deficit_px"]
        amount = deficit + margin
        if amount <= 0.5:
            sides[side] = dict(deficit=deficit, move=0)
            continue
        require(amount <= max_move * ratio, "%s shoulder move %.1f exceeds bound" % (side, amount))
        cand = [p for p in pts if sgn * (p[0] - cx) >= 15 * ratio and top + 10 * ratio <= p[1] <= top + 45 * ratio]
        require(cand, "%s shoulder point not visible" % side)
        p = min(cand, key=lambda q: (q[1], -sgn * q[0]))
        tx, ty = p[0] + sgn * 0.6 * amount, p[1] - 0.8 * amount
        require(460 <= tx <= 565 and 280 <= ty <= 380, "unqualified shoulder target")
        drags.append([p[0] / 1024, p[1] / 768, tx / 1024, ty / 768, 0.65])
        sides[side] = dict(deficit=deficit, move=round(amount, 2), point=[round(p[0], 1), round(p[1], 1)], target=[round(tx, 1), round(ty, 1)])
    require(drags, "no shoulder move needed")
    with Path(out).open("x") as fo:
        json.dump(dict(schema="morwen_w131_shoulder", screenshot_sha256=sha(png), sides=sides, drags=drags), fo, indent=2)
    for dr in drags:
        print(" ".join(f"{v:.8f}" for v in dr))


def plan(guide_json):
    """W132 adjustment choice: crown only while some lane root is outside the guide; otherwise a
    shoulder move while a flank lane body exceeds DRAW_LIMIT - 0.5; else none."""
    gd = json.loads(Path(guide_json).read_text())
    if max(gd["lanes"][l]["root_deficit_px"] for l in LANES) > 0:
        print("crown")
    elif max(gd["lanes"][l]["body_deficit_px"] for l in DRAW_LANES) > DRAW_LIMIT - 0.5:
        print("shoulder")
    else:
        print("none")


def main(argv):
    cmd, *args = argv
    if cmd == "groups":
        g1, g2 = groups(*args)
        print(f"{g1['x']/1024:.8f} {g1['y']/768:.8f} {g2['x']/1024:.8f} {g2['y']/768:.8f}")
    elif cmd == "guide":
        guide(*args)
    elif cmd == "crown":
        crown(*args)
    elif cmd == "shoulder":
        shoulder(*args)
    elif cmd == "plan":
        plan(*args)
    elif cmd == "points":
        points(*args)
    elif cmd == "complete":
        if complete(*args) != "COMPLETE":
            raise SystemExit(3)
    elif cmd == "newlabel":
        newlabel(*args)
    elif cmd == "eye":
        eye(*args)
    elif cmd == "hidden":
        hidden(*args)
    elif cmd == "shown":
        shown(*args)
    elif cmd == "handle":
        handle(*args)
    else:
        raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
