"""LIND-WORLD-01 terrain field generator (pure numpy, no bpy).

Shared by build_terrain.py (Blender build) and qa_terrain.py (determinism re-check).
All geometry is driven by docs/production/lind/world/lind-world-terrain.v1.json.
Every output is a CANDIDATE: status PROPOSED_NOT_LOCKED.

Conventions: +X east, +Y north, +Z up, 1 unit = 1 m, Z=0 = sea level,
origin XY = plaza wind rune stone.
"""
import hashlib
import json
import math
import pathlib

import numpy as np

FIELDS_VERSION = "lind-world-fields-1.0"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DEFAULT_SPEC = REPO_ROOT / "docs/production/lind/world/lind-world-terrain.v1.json"
DEFAULT_SEED = 20261116


# ---------------------------------------------------------------- helpers
def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def _hash01(ix, iy, seed):
    """Deterministic integer hash -> [0,1). Works on int64 arrays (wraps)."""
    with np.errstate(over="ignore"):
        h = (ix.astype(np.uint64) * np.uint64(374761393)
             + iy.astype(np.uint64) * np.uint64(668265263)
             + np.uint64(seed) * np.uint64(1442695041))
        h = (h ^ (h >> np.uint64(13))) * np.uint64(1274126177)
        h = h ^ (h >> np.uint64(16))
    return (h & np.uint64(0xFFFFFF)).astype(np.float64) / float(0x1000000)


def value_noise(x, y, scale, seed):
    """Smooth value noise in [-1,1], feature size ~scale metres."""
    u = x / scale
    v = y / scale
    iu = np.floor(u).astype(np.int64)
    iv = np.floor(v).astype(np.int64)
    fu = u - iu
    fv = v - iv
    fu = fu * fu * (3 - 2 * fu)
    fv = fv * fv * (3 - 2 * fv)
    a = _hash01(iu, iv, seed)
    b = _hash01(iu + 1, iv, seed)
    c = _hash01(iu, iv + 1, seed)
    d = _hash01(iu + 1, iv + 1, seed)
    return (lerp(lerp(a, b, fu), lerp(c, d, fu), fv)) * 2.0 - 1.0


def fbm(x, y, scale, seed, octaves=4, gain=0.5):
    total = np.zeros_like(x, dtype=np.float64)
    amp = 1.0
    norm = 0.0
    s = scale
    for o in range(octaves):
        total += amp * value_noise(x, y, s, seed + 101 * o)
        norm += amp
        amp *= gain
        s *= 0.5
    return total / norm


def _az_dir(az):
    a = math.radians(az)
    return np.array([math.sin(a), math.cos(a)])


def extend_polyline(pts, dist, az0=None, az1=None):
    """Extrapolate both ends of a polyline by `dist` metres (for far-field queries).
    Optional az0/az1 give explicit extension azimuths (deg, clockwise from north)."""
    pts = np.asarray(pts, dtype=np.float64)
    d0 = _az_dir(az0) if az0 is not None else (pts[0] - pts[1]) / np.linalg.norm(pts[0] - pts[1])
    d1 = _az_dir(az1) if az1 is not None else (pts[-1] - pts[-2]) / np.linalg.norm(pts[-1] - pts[-2])
    return np.vstack([pts[0] + d0 * dist, pts, pts[-1] + d1 * dist])


def polyline_query(px, py, pts):
    """Nearest-point query against an open polyline.

    Returns dict with dist, seg index, t on segment, signed cross (sign: >0 left of
    travel direction), arclength s at nearest point, and cumulative lengths.
    """
    pts = np.asarray(pts, dtype=np.float64)
    seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seglen)])
    best = np.full(px.shape, np.inf)
    idx = np.zeros(px.shape, dtype=np.int64)
    tt = np.zeros(px.shape)
    cr = np.zeros(px.shape)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        abx, aby = bx - ax, by - ay
        L2 = abx * abx + aby * aby
        apx = px - ax
        apy = py - ay
        t = np.clip((apx * abx + apy * aby) / L2, 0.0, 1.0)
        dx = apx - t * abx
        dy = apy - t * aby
        d2 = dx * dx + dy * dy
        m = d2 < best
        best = np.where(m, d2, best)
        idx = np.where(m, i, idx)
        tt = np.where(m, t, tt)
        cr = np.where(m, abx * apy - aby * apx, cr)
    s = cum[idx] + tt * seglen[idx]
    return {"dist": np.sqrt(best), "idx": idx, "t": tt, "cross": cr, "s": s,
            "cum": cum}


def interp_along(q, values):
    v = np.asarray(values, dtype=np.float64)
    return v[q["idx"]] * (1 - q["t"]) + v[q["idx"] + 1] * q["t"]


def point_in_polygon(px, py, poly):
    poly = np.asarray(poly, dtype=np.float64)
    inside = np.zeros(px.shape, dtype=bool)
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = ((yi > py) != (yj > py))
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi
        inside ^= cond & (px < xint)
        j = i
    return inside


def polygon_soft_mask(px, py, poly, feather):
    """1 deep inside polygon, 0 outside, feathered inward over `feather` m."""
    ring = list(poly) + [poly[0]]
    q = polyline_query(px, py, ring)
    inside = point_in_polygon(px, py, poly)
    return np.where(inside, smoothstep(0.0, feather, q["dist"]), 0.0)


def load_spec(path=None):
    p = pathlib.Path(path) if path else DEFAULT_SPEC
    raw = p.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest(), p


# ---------------------------------------------------------------- spec-derived data
def coast_data(spec):
    c = spec["coastline"]
    pts = np.asarray(c["points"], dtype=np.float64)
    n = len(pts)
    ct = np.zeros(n)
    cliffness = np.zeros(n)
    cliff_of_type = {"rocky_cliff_low": 1.0, "windward_cliff_main": 1.0,
                     "rocky_shore_descending": 0.8, "rocky_point": 0.5,
                     "inlet_shore_beach": 0.0, "rocky_shore_low": 0.3}
    for seg in c["segments"]:
        for k in range(seg["from"], seg["to"] + 1):
            ct[k] = seg["cliff_top_m"]
            cliffness[k] = cliff_of_type[seg["type"]]
    return pts, ct, cliffness


def river_data(spec):
    cl = spec["river"]["centreline"]
    pts = np.asarray([p["xy"] for p in cl], dtype=np.float64)
    wz = np.asarray([p["water_z"] for p in cl], dtype=np.float64)
    bw = np.asarray([p["bed_width_m"] for p in cl], dtype=np.float64)
    bank = spec["river"]["bank_profile"]
    bkw = np.full(len(pts), float(bank["bank_width_m"]))
    bke = np.full(len(pts), float(bank["bank_width_m"]))
    gr = bank["west_bank_cliff_reach"]
    for k in range(gr["from_i"], gr["to_i"] + 1):
        bkw[k] = float(gr["bank_width_m"])
    return pts, wz, bw, bkw, bke


def _extend_values(vals, pts_ext, pts, slope_clip=None):
    """Linear extrapolation of per-vertex values for an extended polyline."""
    v = np.asarray(vals, dtype=np.float64)
    l0 = np.linalg.norm(pts[1] - pts[0])
    l1 = np.linalg.norm(pts[-1] - pts[-2])
    e0 = np.linalg.norm(pts_ext[0] - pts[0])
    e1 = np.linalg.norm(pts_ext[-1] - pts[-1])
    v0 = v[0] + (v[0] - v[1]) / l0 * e0
    v1 = v[-1] + (v[-1] - v[-2]) / l1 * e1
    if slope_clip is not None:
        v0 = np.clip(v0, *slope_clip)
        v1 = np.clip(v1, *slope_clip)
    return np.concatenate([[v0], v, [v1]])


def coast_ext_az(spec):
    e = spec["coastline"].get("far_extension_azimuth_deg", {})
    return e.get("north_end"), e.get("south_end")


def _smooth_coast_attrs(X, Y, cpts, ct, cliffness, spacing=15.0, sigma=110.0, ext=2500.0, az=(None, None)):
    pe = extend_polyline(cpts, ext, *az)
    ct_e = np.concatenate([[ct[0]], ct, [ct[-1]]])
    cl_e = np.concatenate([[cliffness[0]], cliffness, [cliffness[-1]]])
    seglen = np.linalg.norm(np.diff(pe, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seglen)])
    s = np.arange(0.0, cum[-1], spacing)
    sx = np.interp(s, cum, pe[:, 0])
    sy = np.interp(s, cum, pe[:, 1])
    sct = np.interp(s, cum, ct_e)
    scl = np.interp(s, cum, cl_e)
    num_c = np.zeros(X.shape)
    num_l = np.zeros(X.shape)
    den = np.full(X.shape, 1e-12)
    inv = -1.0 / (2 * sigma * sigma)
    for k in range(len(s)):
        wk = np.exp(((X - sx[k]) ** 2 + (Y - sy[k]) ** 2) * inv)
        num_c += wk * sct[k]
        num_l += wk * scl[k]
        den += wk
    # far from every sample (den tiny) fall back to 0 cliff / 0 cliffness
    ok = den > 1e-9
    return np.where(ok, num_c / den, 0.0), np.where(ok, num_l / den, 0.0)


# ---------------------------------------------------------------- main field
def compute_fields(spec, X, Y, seed=DEFAULT_SEED, with_roads=True, far=False):
    """Compute heightfield H and material masks on arbitrary grid arrays X, Y."""
    reg = spec["region"]
    out = {}
    EXT = 9000.0

    # --- coast signed distance (positive on land)
    cpts, ct, cliffness = coast_data(spec)
    caz = coast_ext_az(spec)
    cext = extend_polyline(cpts, EXT, *caz)
    ct_e = np.concatenate([[ct[0]], ct, [ct[-1]]])
    cl_e = np.concatenate([[cliffness[0]], cliffness, [cliffness[-1]]])
    sea_poly = np.vstack([cext, [[-30000.0, cext[-1][1]], [-30000.0, cext[0][1]]]])
    is_sea = point_in_polygon(X, Y, sea_poly)
    qc = polyline_query(X, Y, cext)
    dc = np.where(is_sea, -qc["dist"], qc["dist"])
    # organic shoreline: perturb the signed distance (sea/land re-derived from it)
    dc = dc + float(spec["coastline"].get("shoreline_noise_m", 0.0)) * fbm(X, Y, 70.0, seed + 9, 3)
    # cliff-top height / cliffness as a smooth Gaussian-weighted field of densely
    # resampled coast points (nearest-segment lookup creates medial-axis creases).
    ctop, cliffv = _smooth_coast_attrs(X, Y, cpts, ct, cliffness, az=caz)
    out["coast_dist"] = dc

    # --- inland base relief
    b = 20.0 + 0.05 * np.clip(Y - 150.0, 0, None)
    b += 0.045 * np.clip(X - 170.0, 0, None) * smoothstep(-450.0, -150.0, Y)
    b -= 0.018 * np.clip(-Y - 150.0, 0, None)
    b += 5.0 * fbm(X, Y, 450.0, seed + 1, 3) + 2.0 * fbm(X, Y, 150.0, seed + 2, 3)
    # far vista relief outside the region (never inside it)
    ox = np.maximum(np.maximum(reg["x_min"] - X, X - reg["x_max"]), 0.0)
    oy = np.maximum(np.maximum(reg["y_min"] - Y, Y - reg["y_max"]), 0.0)
    outside = np.sqrt(ox * ox + oy * oy)
    ridge = 1.0 - np.abs(fbm(X, Y, 1800.0, seed + 3, 4))
    mount = smoothstep(0.0, 2600.0, outside) * (180.0 + 520.0 * ridge ** 2)
    mount *= smoothstep(250.0, 1600.0, dc)
    b += mount
    b = np.maximum(b, 3.0)

    # --- coastal high ground + cliff edge
    hill = 4.0 * fbm(X, Y, 120.0, seed + 4, 3)
    w = smoothstep(0.0, 320.0, dc)
    h_land = (ctop + hill * (ctop > 1)) * (1 - w) + b * w
    vp = spec["event_anchors"]
    sv = [a for a in vp if a["id"] == "sunset_viewpoint_hill"][0]["xy"]
    r2 = (X - sv[0]) ** 2 + (Y - sv[1]) ** 2
    sva = [a for a in vp if a["id"] == "sunset_viewpoint_hill"][0]
    kh, ks = float(sva.get("knoll_height_m", 14.0)), float(sva.get("knoll_sigma_m", 110.0))
    h_land += kh * np.exp(-r2 / (2 * ks ** 2)) * (dc > 0)
    ew = lerp(45.0, 9.0, cliffv)
    edge = smoothstep(0.0, ew, dc)
    h_sea = np.clip(-1.5 - 0.035 * np.abs(dc), -22.0, None)
    H = np.where(dc > 0, h_sea * (1 - edge) + h_land * edge, h_sea)
    land = dc > 0

    # --- village platform
    pz = spec["village_building_zones"]["platform_z"]
    e = np.sqrt(((X + 50.0) / 200.0) ** 2 + ((Y - 15.0) / 210.0) ** 2)
    wv = 1.0 - smoothstep(0.85, 1.35, e)
    H = lerp(H, pz - 0.004 * X, wv)
    out["village_w"] = wv

    # --- harbour platform (inlet head)
    hz = [z for z in spec["village_building_zones"]["zones"] if z["id"] == "Z_HARBOR_PORT"][0]
    eh = np.sqrt(((X + 465.0) / 85.0) ** 2 + ((Y + 300.0) / 50.0) ** 2)
    wh = (1.0 - smoothstep(0.8, 1.4, eh)) * smoothstep(3.0, 9.0, dc)
    H = lerp(H, float(hz["platform_z"]), wh)

    # --- river: valley, bluff, levee, channel
    rpts, wz, bw, bkw, bke = river_data(spec)
    rext = extend_polyline(rpts, EXT)
    wz_e = _extend_values(wz, rext, rpts, (0.5, 400.0))
    bw_e = np.concatenate([[bw[0]], bw, [bw[-1]]])
    bkw_e = np.concatenate([[bkw[0]], bkw, [bkw[-1]]])
    bke_e = np.concatenate([[bke[0]], bke, [bke[-1]]])
    qr = polyline_query(X, Y, rext)
    dr = qr["dist"]
    west = qr["cross"] < 0  # travel N->S: west bank is on the right (cross<0)
    wzr = interp_along(qr, wz_e)
    half = interp_along(qr, bw_e) * 0.5
    bk = np.where(west, interp_along(qr, bkw_e), interp_along(qr, bke_e))
    depth = float(spec["river"]["water_depth_m"])

    valley = wzr + 1.0 + 0.18 * np.maximum(dr - half - bk, 0.0)
    H = np.where(land, np.minimum(H, valley), H)

    # raid bluff on the west bank of the gorge reach
    ra = [a for a in spec["cliff_anchors"]["anchors"] if a["id"] == "raid_riverside_cliff"][0]
    bc = (ra["edge_xy"][0] - 40.0, ra["edge_xy"][1] - 10.0)
    rb = np.sqrt((X - bc[0]) ** 2 + (Y - bc[1]) ** 2)
    bluff = ra["cliff_top_z"] - 11.0 * (rb / 95.0) ** 2 + 0.8 * fbm(X, Y, 30.0, seed + 5, 2)
    H = np.where(west & land, np.maximum(H, bluff), H)

    # farm terraces (north)
    fz = [z for z in spec["terrain_zones"]["zones"] if z["id"] == "farm_north"][0]
    fm = polygon_soft_mask(X, Y, fz["polygon"], 25.0)
    step = float(fz["terrace_step_m"])
    qv = H / step
    fl = np.floor(qv)
    ht = (fl + smoothstep(0.72, 1.0, qv - fl)) * step
    H = lerp(H, ht, fm)
    out["farm_w"] = fm

    # levee: keep ground near the channel above water
    wl = 1.0 - smoothstep(half + bk, half + bk + 50.0, dr)
    H1 = H + wl * np.maximum(0.0, wzr + 1.0 - H)
    bed = wzr - depth * (1.0 - (dr / np.maximum(half, 1e-6)) ** 2) - 0.3
    tb = smoothstep(0.0, 1.0, (dr - half) / bk)
    bank = lerp(wzr - 0.3, H1, tb)
    H = np.where(dr < half, bed, np.where(dr < half + bk, bank, H1))
    out["river_dist"] = dr
    out["river_half"] = half
    out["river_bank"] = bk
    out["river_wz"] = wzr

    # --- fine detail (not on platform / channel)
    det_mask = (1 - wv) * smoothstep(0.0, 6.0, dr - half - bk) * smoothstep(0.0, 6.0, dc)
    H = H + det_mask * (0.9 * fbm(X, Y, 40.0, seed + 6, 3))
    # land floor: dry land never dips below sea level (except the river channel)
    floor = np.minimum(0.25 + 0.03 * dc, 2.0)
    H = np.where((dc > 0) & (dr > half + bk), np.maximum(H, floor), H)

    # --- roads (local only)
    road_w = np.zeros_like(H)
    if with_roads and not far:
        H, road_w = apply_roads(spec, X, Y, H)
    out["road_w"] = road_w
    out["H"] = H

    # --- masks
    if not far:
        cell = float(X[0, 1] - X[0, 0])
        gy, gx = np.gradient(H, cell)
        slope = np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy)))
        out["slope"] = slope
        rock = smoothstep(30.0, 46.0, slope)
        rock = np.maximum(rock, smoothstep(0.35, 0.8, cliffv) * (1 - smoothstep(0.0, 14.0, dc)) * (dc > -10))
        sand = (1 - smoothstep(0.3, 0.6, cliffv)) * smoothstep(-8.0, -1.0, dc) * (1 - smoothstep(18.0, 40.0, dc))
        sand *= (1 - smoothstep(3.0, 6.0, H))
        gravel = 1 - smoothstep(half, half + 2.5, dr)
        sand = np.maximum(sand, gravel)
        # field parcels (~42 x 26 m, slightly rotated) with hedge/verge gaps
        ang = 0.12
        u = (X * math.cos(ang) + Y * math.sin(ang)) / 42.0
        v = (-X * math.sin(ang) + Y * math.cos(ang)) / 26.0
        iu, iv = np.floor(u), np.floor(v)
        fu, fv = u - iu, v - iv
        pv = _hash01(iu.astype(np.int64), iv.astype(np.int64), seed + 20)
        inner = (smoothstep(0.0, 0.08, fu) * smoothstep(0.0, 0.08, 1 - fu)
                 * smoothstep(0.0, 0.12, fv) * smoothstep(0.0, 0.12, 1 - fv))
        soil = fm * inner * np.where(pv > 0.35, 0.45 + 0.5 * pv, 0.08)
        soil = np.maximum(soil, 0.25 * wv * (0.5 + 0.5 * fbm(X, Y, 20.0, seed + 8, 2)))
        soil = np.maximum(soil, road_w * 0.9)
        wet = np.maximum(1 - smoothstep(half, half + bk + 8.0, dr), 1 - smoothstep(0.0, 12.0, dc))
        soil *= (1 - rock)
        sand *= (1 - rock)
        out["mask"] = np.stack([rock, sand, soil, wet], axis=-1).clip(0, 1)
    return out


def road_profile(spec, edge, Hsampler):
    """Longitudinal z profile for a road edge: smoothed terrain with grade clamp."""
    pts = np.asarray(edge["polyline"], dtype=np.float64)
    seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seglen)])
    L = cum[-1]
    n = max(int(L / 2.0), 2)
    s = np.linspace(0.0, L, n + 1)
    xs = np.interp(s, cum, pts[:, 0])
    ys = np.interp(s, cum, pts[:, 1])
    z = Hsampler(xs, ys)
    nodes = spec["route_graph"]["nodes"]
    za = nodes[edge["a"]]["z"]
    zb = nodes[edge["b"]]["z"]
    k = 15
    for _ in range(4):
        zp = np.pad(z, k, mode="edge")
        z = np.convolve(zp, np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
    # pin endpoints where the spec gives explicit node elevations
    if edge["id"] == "road_bridge_east":
        zb = spec["bridge"]["deck_z"]
    if edge["id"] == "path_training_east":
        za = spec["bridge"]["deck_z"]
    if za is not None:
        z = z + (za - z[0]) * (1 - smoothstep(0.0, 60.0, s))
    if zb is not None:
        z = z + (zb - z[-1]) * smoothstep(L - 60.0, L, s)
    g = 0.9 * float(edge["max_grade"])
    ds = s[1] - s[0]
    for _ in range(3):
        for i in range(1, len(z)):
            z[i] = np.clip(z[i], z[i - 1] - g * ds, z[i - 1] + g * ds)
        for i in range(len(z) - 2, -1, -1):
            z[i] = np.clip(z[i], z[i + 1] - g * ds, z[i + 1] + g * ds)
    return s, xs, ys, z


def make_sampler(X, Y, H):
    x0 = X[0, 0]
    y0 = Y[0, 0]
    c = X[0, 1] - X[0, 0]
    ny, nx = H.shape

    def sample(xs, ys):
        fx = np.clip((np.asarray(xs) - x0) / c, 0, nx - 1.0001)
        fy = np.clip((np.asarray(ys) - y0) / c, 0, ny - 1.0001)
        i = np.floor(fx).astype(int)
        j = np.floor(fy).astype(int)
        tx = fx - i
        ty = fy - j
        a = H[j, i] * (1 - tx) + H[j, i + 1] * tx
        b = H[j + 1, i] * (1 - tx) + H[j + 1, i + 1] * tx
        return a * (1 - ty) + b * ty
    return sample


def apply_roads(spec, X, Y, H):
    sampler = make_sampler(X, Y, H)
    total_w = np.zeros_like(H)
    Hn = H.copy()
    for edge in spec["route_graph"]["edges"]:
        s, xs, ys, z = road_profile(spec, edge, sampler)
        q = polyline_query(X, Y, np.stack([xs, ys], axis=1))
        zq = np.interp(q["s"], s, z)
        half = edge["width_m"] * 0.5
        wroad = 1.0 - smoothstep(half, half + 6.0, q["dist"])
        # do not flatten across the river channel
        Hn = lerp(Hn, zq, wroad * (wroad > 0.001))
        total_w = np.maximum(total_w, 1.0 - smoothstep(half - 0.5, half + 0.5, q["dist"]))
    return Hn, total_w


def region_grid(spec):
    reg = spec["region"]
    c = float(reg["heightfield_cell_m"])
    xs = np.arange(reg["x_min"], reg["x_max"] + 0.5 * c, c)
    ys = np.arange(reg["y_min"], reg["y_max"] + 0.5 * c, c)
    X, Y = np.meshgrid(xs, ys)
    return X, Y


def heightfield_hash(H):
    return hashlib.sha256(np.round(H, 4).astype(np.float32).tobytes()).hexdigest()
