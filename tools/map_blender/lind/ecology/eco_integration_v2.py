"""LIND-ECO-01 integration package v2 — vegetation selection, CG-fit additions, game materials,
LOD0/LOD1/LOD2, glTF export, PBR card maps, placement rules and SHA records for Codex field integration.

Run (Blender 5.3):
  blender -b --factory-startup --python-exit-code 1 --python tools/map_blender/lind/ecology/build_eco_assets.py -- --out /tmp/lind_eco
  blender -b --factory-startup --python-exit-code 1 --python tools/map_blender/lind/ecology/eco_integration_v2.py -- \
      --kit /tmp/lind_eco/eco_kit_v1.blend --kit-json /tmp/lind_eco/eco_kit_build.json --out /tmp/lind_eco_v2

Candidate tooling only. Nothing produced here is adopted art; G2 requires an independent reviewer and
G4 requires the runtime/Android owner. The existing eco_assets.py / eco_lib.py generators are imported, not edited.
"""
import argparse
import hashlib
import json
import math
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import eco_assets as A  # noqa: E402
import eco_lib as L  # noqa: E402

SEED = 20261120
REPO = HERE.parents[3]
KIT_PKG = REPO / "assets" / "candidates" / "LIND-ECO-01" / "eco_kit_v1"
UP = Vector((0, 0, 1))
PREVAILING_WIND = Vector((0.85, -0.25, 0.0)).normalized()  # sea -> land, same vector as coastal_dune lean

# --------------------------------------------------------------------------- selection (inventory verdicts)
# verdict: PACKAGE (candidate for integration test), PACKAGE_NEW (made in this pass), DEFER (kept in kit,
# not packaged: out of vegetation scope or owned by another lane), EXCLUDE (known G2 FAIL/blockout).
SELECTION = {
    "eco_tree_deciduous_a": ("PACKAGE", "oak cloud crown; matches rounded oaks of rilde_village.png and cliff CG foreground tree"),
    "eco_tree_forest_tall_a": ("PACKAGE", "beech ovoid; woodland edge / Moss Forest approach"),
    "eco_tree_apple_a": ("PACKAGE", "orchard only; not in cliff zone"),
    "eco_tree_conifer_a": ("PACKAGE", "conifers visible on rilde_village.png hills; background/forest only"),
    "eco_hedgerow": ("PACKAGE", "HEDGE-F2 cluster shell; field boundaries"),
    "eco_grass_tuft_short": ("PACKAGE", "ECO-G2 accent tuft over turf; paths/verges"),
    "eco_grass_meadow": ("PACKAGE", "ECO-G2 accent clump with seed stems"),
    "eco_grass_tall_lax": ("PACKAGE", "field margins, fence feet"),
    "eco_grass_coastal_dune": ("PACKAGE", "wind-combed accent for exposed cliff edge only; never as the carpet"),
    "eco_sedge_bank": ("PACKAGE", "river banks (rilde_village.png river)"),
    "eco_reed_riverside": ("PACKAGE", "river banks, sparse"),
    "eco_grass_card_lod1": ("SUPERSEDED", "stippled binary-alpha card (G2-01 defect); replaced by per-asset LOD2 impostors"),
    "eco_flower_patch": ("SUPERSEDED", "red poppies absent from both approved CGs; split into CG-matched clumps below"),
    "eco_wheat_patch": ("DEFER", "farmland crop, not in this vegetation pass"),
    "eco_vegetable_rows": ("DEFER", "farmland crop, not in this vegetation pass"),
    "eco_haystack": ("DEFER", "farm prop"),
    "eco_fence_post_rail": ("DEFER", "boundary prop, not vegetation"),
    "eco_rocks_river": ("DEFER", "rock lane (PR #421 owns cliff rock); used only as a moss-placement preview surface"),
    "eco_rocks_coastal": ("EXCLUDE", "independent G2 FAIL: inflated smooth proxy boulders"),
    "eco_river_water": ("DEFER", "water lane"),
    "eco_river_bank": ("DEFER", "preview terrain, replaced by WORLD terrain"),
    "eco_chicken_hen_blockout": ("EXCLUDE", "STRUCTURAL_BLOCKOUT_NOT_ART"),
    "eco_cow_blockout": ("EXCLUDE", "STRUCTURAL_BLOCKOUT_NOT_ART"),
}

# category, wind (amp m, freq Hz, flutter), placement-rule key
PACKAGED_META = {
    "eco_tree_deciduous_a": ("tree", (0.22, 0.32, 0.30), "tree_broadleaf"),
    "eco_tree_forest_tall_a": ("tree", (0.28, 0.28, 0.30), "tree_woodland"),
    "eco_tree_apple_a": ("tree", (0.16, 0.36, 0.30), "tree_orchard"),
    "eco_tree_conifer_a": ("tree", (0.20, 0.25, 0.25), "tree_conifer"),
    "eco_hedgerow": ("shrub", (0.06, 0.45, 0.35), "hedgerow"),
    "eco_shrub_round_a": ("shrub", (0.07, 0.45, 0.35), "shrub_low"),
    "eco_grass_tuft_short": ("grass", (0.05, 0.7, 0.35), "grass_accent"),
    "eco_grass_meadow": ("grass", (0.08, 0.6, 0.35), "grass_accent"),
    "eco_grass_tall_lax": ("grass", (0.12, 0.55, 0.3), "grass_margin"),
    "eco_grass_coastal_dune": ("grass", (0.09, 0.6, 0.3), "grass_cliff_edge"),
    "eco_sedge_bank": ("grass", (0.10, 0.5, 0.3), "riverbank"),
    "eco_reed_riverside": ("grass", (0.14, 0.5, 0.3), "riverbank"),
    "eco_turf_meadow_a": ("turf", (0.04, 0.7, 0.35), "turf_carpet"),
    "eco_flower_daisy_clump": ("flower", (0.06, 0.6, 0.35), "flower_meadow"),
    "eco_flower_violet_cushion": ("flower", (0.03, 0.6, 0.35), "flower_cliff_cushion"),
    "eco_flower_spike_clump": ("flower", (0.07, 0.55, 0.35), "flower_village"),
    "eco_moss_cushion_a": ("moss", None, "moss_cushion"),
    "eco_moss_mat_b": ("moss", None, "moss_mat"),
}


# --------------------------------------------------------------------------- new assets (CG-fit additions)
def _strip_blade(acc, rng, base, comb, L, w, col_b, col_t, ww_max, curl):
    """TURF-T1 blade: flat 3-ring strip + tip (5 tris), curved toward the comb vector.
    Soft painterly turf needs many cheap blades, not the 24-tri V-folded ECO-G2 blade."""
    yaw = math.atan2(comb.y, comb.x) + rng.uniform(-0.9, 0.9)
    hd = Vector((math.cos(yaw), math.sin(yaw), 0))
    side = hd.cross(UP).normalized()
    side = (Matrix.Rotation(rng.uniform(-0.5, 0.5), 3, UP) @ side)
    lean = rng.uniform(0.15, 0.45) + curl
    ids = []
    for i, t in enumerate((0.0, 0.38, 0.72)):
        p = base + UP * (L * t * (1 - 0.35 * lean * t)) + hd * (L * lean * t * t)
        ww = ww_max * t ** 1.5
        hw = w * (1.0 - 0.25 * t)
        c = A.lerp(col_b, col_t, t ** 0.7)
        ids.append((acc.vert(p - side * hw, c, ww), acc.vert(p + side * hw, c, ww)))
    tip = base + UP * (L * (1 - 0.35 * lean)) + hd * (L * lean)
    it = acc.vert(tip, col_t, ww_max)
    for a, b in zip(ids, ids[1:]):
        acc.face((a[0], a[1], b[1], b[0]), 0)
    acc.face((ids[-1][0], ids[-1][1], it), 0)


def build_turf_patch(seed, size=2.0, density=520.0):
    """TURF-T1: continuous meadow turf tile. Structural difference from ECO-G2 clumps and the
    coastal sward scatter (both FAIL: isolated tuft footprints): blades are placed by stratified
    jitter over the whole area with no clump centroid; height comes from a low-frequency swell
    field; colour comes from a patchiness field (lit yellow-green / mid green / sparse straw);
    the outline is a noisy superellipse with a density feather so tiles overlap without seams."""
    rng = A.new_rng(seed, "turf")
    acc = MeshAcc_()
    ph = [rng.uniform(0, math.tau) for _ in range(8)]
    half = size / 2

    def swell(x, y):
        v = 0.55 * math.sin(x * 1.9 + ph[0]) * math.cos(y * 1.5 + ph[1]) + 0.45 * math.sin(x * 3.7 + y * 2.9 + ph[2])
        return 0.5 + 0.5 * v

    def patch(x, y):
        v = 0.6 * math.sin(x * 2.6 + ph[3]) * math.sin(y * 2.2 + ph[4]) + 0.4 * math.cos(x * 5.1 - y * 4.3 + ph[5])
        return 0.5 + 0.5 * v

    def edge(x, y):
        a = math.atan2(y, x)
        R = half * (0.93 + 0.07 * math.sin(3 * a + ph[6]) + 0.05 * math.sin(7 * a + ph[7]))
        r = (abs(x) ** 4 + abs(y) ** 4) ** 0.25
        return r / R  # <1 inside

    cell = 1.0 / math.sqrt(density)
    n = int(size / cell)
    lit, mid, dark_tip, straw = (0.50, 0.60, 0.12), (0.27, 0.44, 0.08), (0.18, 0.33, 0.06), (0.58, 0.50, 0.24)
    base_c = (0.035, 0.065, 0.016)
    stats = {"blades": 0, "straw": 0, "tall": 0}
    for i in range(n):
        for j in range(n):
            x = -half + (i + rng.random()) * cell
            y = -half + (j + rng.random()) * cell
            e = edge(x, y)
            if e > 1.0:
                continue
            feather = max(0.0, (e - 0.72) / 0.28)
            if rng.random() < feather ** 1.4:
                continue
            h = swell(x, y)
            L = (0.07 + 0.13 * h ** 1.3) * (1 - 0.45 * feather) * rng.uniform(0.7, 1.15)
            if rng.random() < 0.05:
                L *= 1.65
                stats["tall"] += 1
            pv = patch(x, y)
            tip = A.lerp(mid, lit, min(1.0, max(0.0, pv * 1.3 - 0.15)))
            if rng.random() < 0.25:
                tip = A.lerp(tip, dark_tip, 0.6)
            if rng.random() < 0.06 + 0.06 * (1 - pv):
                tip = straw
                stats["straw"] += 1
            tip = A.jitter_col(rng, tip, 0.08)
            _strip_blade(acc, rng, Vector((x, y, 0.0)), PREVAILING_WIND, L, rng.uniform(0.0035, 0.0065),
                         base_c, tip, min(1.0, L / 0.2), 0.15 * h)
            stats["blades"] += 1
    stats.update(size_m=size, density_per_m2=density, method="TURF-T1 stratified continuous turf, swell+patch fields, feathered superellipse")
    return acc, stats


def MeshAcc_():
    return L.MeshAcc()


def _rosette(acc, rng, c, n, Lr, w, col_b, col_t):
    for k in range(n):
        a = math.tau * k / n + rng.uniform(-0.3, 0.3)
        A._blade(acc, rng, c + UP * 0.005, (UP * 0.45 + Vector((math.cos(a), math.sin(a), 0))).normalized(),
                 rng.uniform(*Lr), w, 0.5, col_b, col_t, 0.35, nseg=3)


def _turf_skirt(acc, rng, radius, n):
    for k in range(n):
        r = radius * math.sqrt(rng.random())
        a = rng.uniform(0, math.tau)
        _strip_blade(acc, rng, Vector((math.cos(a) * r, math.sin(a) * r, 0)), PREVAILING_WIND,
                     rng.uniform(0.06, 0.16), rng.uniform(0.0035, 0.006), (0.035, 0.065, 0.016),
                     A.jitter_col(rng, (0.40, 0.55, 0.11), 0.1), 0.6, 0.1)


def build_daisy_clump(seed):
    """Oxeye-daisy colony growing out of foliage (cliff CG foreground, rilde_village.png verges)."""
    rng = A.new_rng(seed, "daisy_clump")
    acc = L.MeshAcc()
    nf = rng.randint(9, 13)
    for k in range(nf):
        r = 0.16 * math.sqrt(rng.random())
        a = rng.uniform(0, math.tau)
        A._flower(acc, rng, Vector((math.cos(a) * r, math.sin(a) * r, 0)), "daisy")
    _rosette(acc, rng, Vector(), 9, (0.08, 0.14), 0.012, (0.03, 0.09, 0.02), (0.20, 0.40, 0.08))
    _turf_skirt(acc, rng, 0.26, 160)
    return acc, {"flowers": nf, "method": "FLOWER-F2 single-species colony + rosette + turf skirt"}


def build_violet_cushion(seed):
    """Low cushion with globular violet heads (cliff CG violet points; thrift-like clifftop habit)."""
    rng = A.new_rng(seed, "violet_cushion")
    acc = L.MeshAcc()
    # dense hemispherical cushion of narrow leaves
    for k in range(210):
        a = rng.uniform(0, math.tau)
        r = 0.11 * math.sqrt(rng.random())
        lean = (UP * (1.2 - r / 0.11) + Vector((math.cos(a), math.sin(a), 0))).normalized()
        A._blade(acc, rng, Vector((math.cos(a) * r, math.sin(a) * r, 0)), lean, rng.uniform(0.05, 0.10),
                 0.0028, 0.3, (0.04, 0.08, 0.025), A.jitter_col(rng, (0.24, 0.38, 0.10), 0.1), 0.3, nseg=3)
    nh = rng.randint(15, 21)
    for k in range(nh):
        a = rng.uniform(0, math.tau)
        r = 0.09 * math.sqrt(rng.random())
        b = Vector((math.cos(a) * r, math.sin(a) * r, 0.02))
        H = rng.uniform(0.10, 0.22)
        d = (UP + Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.1, 0.35)).normalized()
        pts = [b + d * H * i / 4 for i in range(5)]
        acc.tube(pts, [0.0016] * 5, 3, [(0.22, 0.30, 0.10)] * 5, [(i / 4) ** 1.5 for i in range(5)], cap_tip=False)
        col = A.jitter_col(rng, (0.50, 0.28, 0.66), 0.12)
        hr = rng.uniform(0.019, 0.026)
        c = pts[-1] + d * hr * 0.6
        rings, segs = 4, 7
        rows = []
        for ri in range(1, rings):
            th = math.pi * ri / rings
            row = []
            for sj in range(segs):
                phi = math.tau * sj / segs + ri * 0.4
                rr = hr * (1 + 0.18 * ((sj + ri) % 2))  # floret bumps
                p = c + Vector((math.sin(th) * math.cos(phi), math.sin(th) * math.sin(phi), math.cos(th))) * rr
                shade = 0.75 + 0.35 * max(0.0, math.cos(th))
                row.append(acc.vert(p, tuple(min(1.0, x * shade) for x in col), 1.0))
            rows.append(row)
        top = acc.vert(c + UP * hr, tuple(min(1.0, x * 1.15) for x in col), 1.0)
        bot = acc.vert(c - UP * hr, tuple(x * 0.7 for x in col), 1.0)
        for sj in range(segs):
            s2 = (sj + 1) % segs
            acc.face((top, rows[0][sj], rows[0][s2]), 0)
            acc.face((bot, rows[-1][s2], rows[-1][sj]), 0)
            for ri in range(rings - 2):
                acc.face((rows[ri][sj], rows[ri + 1][sj], rows[ri + 1][s2], rows[ri][s2]), 0)
    _turf_skirt(acc, rng, 0.17, 60)
    return acc, {"heads": nh, "method": "FLOWER-F2 leaf cushion + globular heads"}


def build_spike_clump(seed):
    """Lupin/foxglove-like violet spikes (rilde_village.png foreground)."""
    rng = A.new_rng(seed, "spike_clump")
    acc = L.MeshAcc()
    ns = rng.randint(4, 6)
    for k in range(ns):
        r = 0.09 * math.sqrt(rng.random())
        a = rng.uniform(0, math.tau)
        A._flower(acc, rng, Vector((math.cos(a) * r, math.sin(a) * r, 0)), "spike")
    _rosette(acc, rng, Vector(), 12, (0.12, 0.22), 0.016, (0.03, 0.09, 0.02), (0.18, 0.38, 0.07))
    _turf_skirt(acc, rng, 0.22, 110)
    return acc, {"spikes": ns, "method": "FLOWER-F2 spike colony + rosette + turf skirt"}


def build_moss(seed, kind="cushion"):
    """MOSS-M1: displaced low dome (cushion) or thin mat; UV planar (0.5 m tile) for the moss PBR set,
    vertex colour carries the dark-core / lit-top tint. Edge dips below z=0 so it seats into rock/soil."""
    rng = A.new_rng(seed, "moss:" + kind)
    acc = L.MeshAcc()
    R0, H, rings, segs = (0.32, 0.055, 9, 40) if kind == "cushion" else (0.55, 0.012, 7, 44)
    ph = [rng.uniform(0, math.tau) for _ in range(6)]

    def Rt(a):
        return R0 * (0.82 + 0.12 * math.sin(2 * a + ph[0]) + 0.08 * math.sin(5 * a + ph[1]) + 0.05 * math.sin(9 * a + ph[2]))

    centre_h = H
    centre = acc.vert((0, 0, centre_h), (0.30, 0.40, 0.07), 0.0)
    grid = []
    for ri in range(1, rings + 1):
        t = ri / rings
        row = []
        for sj in range(segs):
            a = math.tau * sj / segs
            r = Rt(a) * t
            x, y = math.cos(a) * r, math.sin(a) * r
            bump = 0.35 * math.sin(x * 23 + ph[3]) * math.sin(y * 19 + ph[4]) + 0.25 * math.sin(x * 41 - y * 37 + ph[5])
            z = H * (1 - t ** 2.2) ** 0.6 * (1 + bump * (1 - t)) - (0.012 if ri == rings else 0.0)
            lt = max(0.0, min(1.0, z / H))
            c = A.lerp((0.07, 0.13, 0.03), (0.42, 0.52, 0.10), lt ** 0.6)
            c = A.jitter_col(rng, c, 0.06)
            row.append(acc.vert((x, y, z), c, 0.0))
        grid.append(row)
    uvf = 1 / 0.5
    for sj in range(segs):
        s2 = (sj + 1) % segs
        tri = (centre, grid[0][sj], grid[0][s2])
        acc.face(tri, 0, uv=[tuple(Vector(acc.v[i][:2]) * uvf) for i in tri])
        for ri in range(rings - 1):
            q = (grid[ri][sj], grid[ri + 1][sj], grid[ri + 1][s2], grid[ri][s2])
            acc.face(q, 0, uv=[tuple(Vector(acc.v[i][:2]) * uvf) for i in q])
    return acc, {"radius_m": R0, "height_m": H, "method": "MOSS-M1 displaced dome/mat + tileable PBR"}


SHRUB_PRESET = dict(trunk_len=0.22, trunk_r=0.05, lean=0.06, scaffolds=5, scaffold_at=(0.3, 1.0),
                    scaffold_len=(0.55, 0.8), angle=(38, 62), depth=3, len_decay=(0.6, 0.75), gravi=0.15,
                    tex="beech", card_size=(0.30, 0.42), card_density=13.0, lobe_merge=0.45, lobe_pad=0.30,
                    lobe_depth=1, lobe_zscale=0.72, tint=(0.75, 1.25), bark=(0.22, 0.17, 0.12), apples=0,
                    side_shoots=0, droop=0.05, sides0=6, bare_below=0.10)


def build_shrub(seed):
    A.TREE_PRESETS["shrub_round"] = SHRUB_PRESET  # runtime-only preset; eco_assets.py is not edited
    return A.build_tree(seed, preset="shrub_round")


# --------------------------------------------------------------------------- PBR texture derivation
def _load_rgba(path):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    return np.asarray(im).astype(np.float32) / 255.0


def _save(path, arr, mode):
    from PIL import Image
    a = np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(a, mode).save(path, optimize=True)


def _blur(a, r=1):
    out = a.copy()
    for _ in range(r):
        out = (out + np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 5.0
    return out


def derive_card_pbr(src, out_dir, stem, normal_strength=3.0, rough_base=0.62):
    """Albedo+alpha card -> normal (tangent space, from luminance+alpha height) and ORM (R=AO, G=rough, B=metal=0)."""
    rgba = _load_rgba(src)
    rgb, a = rgba[..., :3], rgba[..., 3]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    h = _blur(0.65 * _blur(a, 3) + 0.35 * lum, 1)
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * normal_strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * normal_strength
    n = np.stack([-dx, dy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    nrm = n * 0.5 + 0.5
    ao = np.clip(0.55 + 0.45 * _blur(a, 4), 0, 1)
    rough = np.clip(rough_base + 0.25 * (0.5 - lum), 0.35, 0.95)
    orm = np.stack([ao, rough, np.zeros_like(a)], -1)
    paths = {"basecolor": out_dir / f"{stem}_basecolor.png", "normal": out_dir / f"{stem}_normal.png",
             "orm": out_dir / f"{stem}_orm.png"}
    shutil.copy2(src, paths["basecolor"])
    _save(paths["normal"], nrm, "RGB")
    _save(paths["orm"], orm, "RGB")
    return paths


def paint_moss_set(out_dir, seed, S=512):
    """Tileable moss albedo/normal/ORM (periodic sums of sines + hashed clumps -> wraps seamlessly)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S * math.tau
    h = np.zeros((S, S), np.float32)
    for k in range(18):
        fx, fy = rng.integers(2, 26, 2)
        h += np.sin(fx * xx + fy * yy + rng.uniform(0, math.tau)) / (1 + 0.15 * (fx + fy))
    # clumped fronds: periodic Gaussian bumps
    for k in range(900):
        cx, cy, r = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(2.5, 7.0)
        x0, x1 = int(cx - 3 * r), int(cx + 3 * r) + 1
        y0, y1 = int(cy - 3 * r), int(cy + 3 * r) + 1
        gy, gx = np.mgrid[y0:y1, x0:x1]
        g = np.exp(-(((gx - cx) ** 2 + (gy - cy) ** 2) / (2 * r * r))).astype(np.float32)
        h[np.ix_(np.arange(y0, y1) % S, np.arange(x0, x1) % S)] += g * rng.uniform(0.4, 1.0)
    h = (h - h.min()) / (h.max() - h.min())
    dark, lit, tip = np.array([0.10, 0.17, 0.04]), np.array([0.36, 0.48, 0.09]), np.array([0.60, 0.64, 0.18])
    t = h[..., None]
    alb = dark * (1 - t) + lit * t
    spark = (h > 0.82)[..., None] * rng.uniform(0.0, 1.0, (S, S, 1)) * 0.6
    alb = alb * (1 - spark) + tip * spark
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 6.0
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 6.0
    n = np.stack([-dx, dy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    orm = np.stack([0.5 + 0.5 * h, 0.85 - 0.15 * h, np.zeros_like(h)], -1)
    paths = {"basecolor": out_dir / "moss_tile_basecolor.png", "normal": out_dir / "moss_tile_normal.png",
             "orm": out_dir / "moss_tile_orm.png", "height": out_dir / "moss_tile_height.png"}
    _save(paths["basecolor"], alb.astype(np.float32), "RGB")
    _save(paths["normal"], (n * 0.5 + 0.5).astype(np.float32), "RGB")
    _save(paths["orm"], orm.astype(np.float32), "RGB")
    _save(paths["height"], h, "L")
    return paths


# --------------------------------------------------------------------------- game (glTF-friendly) materials
def _img(path):
    im = bpy.data.images.load(str(path), check_existing=True)
    return im


def gm_vcol(name, rough=0.6, gain=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    nt.links.new(vc.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = 0.0
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    m.use_backface_culling = False
    m["eco_vcol_gain"] = gain
    return m


def gm_textured(name, pbr, alpha_clip=True, rough=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tb = nt.nodes.new("ShaderNodeTexImage")
    tb.image = _img(pbr["basecolor"])
    nt.links.new(tb.outputs["Color"], bs.inputs["Base Color"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = _img(pbr["normal"])
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = _img(pbr["orm"])
    to.image.colorspace_settings.name = "Non-Color"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bs.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], bs.inputs["Metallic"])
    if alpha_clip:
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.5
        nt.links.new(tb.outputs["Alpha"], gt.inputs[0])
        nt.links.new(gt.outputs["Value"], bs.inputs["Alpha"])
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    m.use_backface_culling = False
    return m


def build_game_materials(tex):
    return {
        "foliage": gm_vcol("GM_eco_foliage_vcol", rough=0.62),
        "flower": gm_vcol("GM_eco_flower_vcol", rough=0.5),
        "bark": gm_vcol("GM_eco_bark_vcol", rough=0.9),
        "gloss": gm_vcol("GM_eco_fruit_vcol", rough=0.35),
        "oak": gm_textured("GM_eco_leafcard_oak", tex["leaf_cluster_oak"]),
        "beech": gm_textured("GM_eco_leafcard_beech", tex["leaf_cluster_beech"]),
        "apple": gm_textured("GM_eco_leafcard_apple", tex["leaf_cluster_apple"]),
        "needle": gm_textured("GM_eco_leafcard_needle", tex["leaf_spray_needle"]),
        "moss": gm_textured("GM_eco_moss", tex["moss_tile"], alpha_clip=False),
    }


ORIG_TO_GM = {
    "M_eco_grass": "foliage", "M_eco_leaf": "foliage", "M_eco_flower": "flower", "M_eco_bark": "bark",
    "M_eco_apple": "gloss", "M_eco_leafcard_oak": "oak", "M_eco_leafcard_beech": "beech",
    "M_eco_leafcard_apple": "apple", "M_eco_leafcard_needle": "needle", "M_eco_moss": "moss",
}
CARD_GM = {"oak", "beech", "apple", "needle"}


def assign_game_materials(ob, gms):
    me = ob.data
    for i, m in enumerate(me.materials):
        key = ORIG_TO_GM.get(m.name if m else "", "foliage")
        me.materials[i] = gms[key]


def calibrate_vcol(ob, gain_by_mat):
    """Per-material-slot vertex colour gain (albedo calibration toward the approved CG value structure)."""
    me = ob.data
    col = me.color_attributes.get("Col")
    if col is None:
        return
    vmat = {}
    for p in me.polygons:
        for vi in p.vertices:
            vmat.setdefault(vi, p.material_index)
    slot_gain = [gain_by_mat.get(m.name, 1.0) for m in me.materials]
    for vi, d in enumerate(col.data):
        g = slot_gain[vmat.get(vi, 0)]
        r, gg, b, a = d.color
        d.color = (min(1.0, r * g), min(1.0, gg * g), min(1.0, b * g), a)


# --------------------------------------------------------------------------- LODs
def lod_thin(src, name, keep, grow, thin_mats, seed, bark_ratio=1.0):
    """LOD1: deterministic removal of whole foliage islands (blades / cards / heads) of the listed material
    slots; kept islands are scaled about their root (lowest-wind vertex) to preserve coverage."""
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = name
    ob.data.name = name + "_mesh"
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    ww = bm.verts.layers.float.get("wind_weight")
    rng = A.new_rng(seed, "lod:" + name)
    seen = set()
    kill = []
    for f in bm.faces:
        if f.index in seen or f.material_index not in thin_mats:
            continue
        stack, island = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            island.append(g)
            for v in g.verts:
                for h in v.link_faces:
                    if h.index not in seen and h.material_index == g.material_index:
                        seen.add(h.index)
                        stack.append(h)
        if rng.random() > keep:
            kill.extend(island)
        elif grow != 1.0:
            verts = {v for g in island for v in g.verts}
            root = min(verts, key=lambda v: (v[ww] if ww else 0.0, v.co.z)).co.copy()
            for v in verts:
                v.co = root + (v.co - root) * grow
    bmesh.ops.delete(bm, geom=list(set(kill)), context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    if bark_ratio < 1.0:
        _decimate_slots(ob, bark_ratio, {i for i in range(len(ob.data.materials)) if i not in thin_mats})
    return ob


def _decimate_slots(ob, ratio, slots):
    """Collapse-decimate only the faces of the given material slots (bark tubes), cards untouched."""
    vg = ob.vertex_groups.new(name="lod_decimate")
    vids = {v for p in ob.data.polygons if p.material_index in slots for v in p.vertices}
    vg.add(sorted(vids), 1.0, "REPLACE")
    md = ob.modifiers.new("lod_dec", "DECIMATE")
    md.decimate_type = "COLLAPSE"
    md.ratio = ratio
    md.vertex_group = vg.name
    md.vertex_group_factor = 1000.0
    md.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = ob
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_apply(modifier=md.name)
    g = ob.vertex_groups.get("lod_decimate")
    if g:
        ob.vertex_groups.remove(g)


def lod_impostor(src, name, atlas_path, samples, res=512):
    """LOD2: 2 crossed quads (front / side) textured from orthographic renders of LOD0 under uniform white
    ambient light (albedo x ambient occlusion, straight alpha). Pivot at the base like LOD0."""
    sc = bpy.context.scene
    dims = src.dimensions.copy()
    bb = [src.matrix_world @ Vector(c) for c in src.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    cen = (mn + mx) / 2
    width = max(mx.x - mn.x, mx.y - mn.y)
    H = mx.z - max(0.0, mn.z)
    span = max(width, H) * 1.02
    # isolate
    hidden = []
    for o in sc.objects:
        if o is not src and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    cam_d = bpy.data.cameras.new("imp_cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = span
    cam = bpy.data.objects.new("imp_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    w = bpy.data.worlds.get("IMP_WORLD") or bpy.data.worlds.new("IMP_WORLD")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    old_world = sc.world
    sc.world = w
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    from PIL import Image
    tiles = []
    zc = max(0.0, mn.z) + span / 2
    for k, (dirv, rot) in enumerate(((Vector((0, -1, 0)), (math.pi / 2, 0, 0)), (Vector((1, 0, 0)), (math.pi / 2, 0, math.pi / 2)))):
        cam.rotation_euler = rot
        if k == 1:
            cam.location = Vector((cen.x, cen.y, zc)) + Vector((50, 0, 0))
        else:
            cam.location = Vector((cen.x, cen.y, zc)) + Vector((0, -50, 0))
        p = str(atlas_path) + f".v{k}.png"
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append(Image.open(p).convert("RGBA"))
    atlas = Image.new("RGBA", (res * 2, res))
    atlas.paste(tiles[0], (0, 0))
    atlas.paste(tiles[1], (res, 0))
    # dilate colour under alpha=0 (no halos under mip/alpha-clip)
    arr = np.asarray(atlas).astype(np.float32)
    rgb, a = arr[..., :3], arr[..., 3:] / 255.0
    acc_c, acc_w = rgb * a, a.copy()
    for _ in range(8):
        acc_c = _blur(acc_c, 1)
        acc_w = _blur(acc_w, 1)
    fill = acc_c / np.maximum(acc_w, 1e-4)
    rgb = np.where(a > 0.01, rgb, fill)
    out = np.concatenate([rgb, a * 255.0], -1)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(atlas_path, optimize=True)
    for k in range(2):
        pathlib.Path(str(atlas_path) + f".v{k}.png").unlink()
    for o in hidden:
        o.hide_render = False
    bpy.data.objects.remove(cam)
    sc.world = old_world
    # mesh: quad A in XZ (front, u 0..0.5), quad B in YZ (side, u 0.5..1)
    acc = L.MeshAcc()
    hs = span / 2
    z0 = zc - hs
    z1 = zc + hs
    for k in range(2):
        if k == 0:
            a0, a1 = Vector((cen.x - hs, cen.y, z0)), Vector((cen.x + hs, cen.y, z0))
            b1, b0 = Vector((cen.x + hs, cen.y, z1)), Vector((cen.x - hs, cen.y, z1))
        else:
            a0, a1 = Vector((cen.x, cen.y - hs, z0)), Vector((cen.x, cen.y + hs, z0))
            b1, b0 = Vector((cen.x, cen.y + hs, z1)), Vector((cen.x, cen.y - hs, z1))
        u0, u1 = 0.5 * k, 0.5 * k + 0.5
        ids = [acc.vert(a0, (1, 1, 1), 0.0), acc.vert(a1, (1, 1, 1), 0.0), acc.vert(b1, (1, 1, 1), 1.0), acc.vert(b0, (1, 1, 1), 1.0)]
        acc.face(ids, 0, uv=[(u0, 0), (u1, 0), (u1, 1), (u0, 1)])
    m = gm_textured("GM_" + name, {"basecolor": atlas_path, "normal": _flat_normal(atlas_path.parent), "orm": _flat_orm(atlas_path.parent)})
    ob = acc.build(name, [m], smooth=True)
    # impostor shading: normals pointing up-and-out so lighting matches the 3D crown, not a flat plane
    me = ob.data
    nrm = []
    for vx in me.vertices:
        d = Vector((vx.co.x - cen.x, vx.co.y - cen.y, 0))
        nv = (d.normalized() * 0.4 + UP).normalized() if d.length > 1e-4 else UP.copy()
        nrm.append(tuple(nv))
    me.normals_split_custom_set_from_vertices(nrm)
    return ob, {"atlas": atlas_path.name, "span_m": round(span, 3), "views": ["front_-Y", "side_+X"], "samples": samples}


def lod_decal_top(src, name, atlas_path, samples, res=1024):
    """Turf LOD2: one flat quad carrying a top-down orthographic bake of LOD0 (albedo x AO, feathered alpha).
    For the fixed 28 deg game camera blades are < 1 px wide; geometry beyond this is wasted on Android."""
    sc = bpy.context.scene
    bb = [src.matrix_world @ Vector(c) for c in src.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), 0))
    mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    cen = (mn + mx) / 2
    span = max(mx.x - mn.x, mx.y - mn.y) * 1.02
    hidden = [o for o in sc.objects if o is not src and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    cam_d = bpy.data.cameras.new("dec_cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = span
    cam = bpy.data.objects.new("dec_cam", cam_d)
    sc.collection.objects.link(cam)
    cam.location = (cen.x, cen.y, 20.0)
    cam.rotation_euler = (0, 0, 0)
    sc.camera = cam
    w = bpy.data.worlds.get("IMP_WORLD") or bpy.data.worlds.new("IMP_WORLD")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    old_world = sc.world
    sc.world = w
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = str(atlas_path)
    bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    bpy.data.objects.remove(cam)
    sc.world = old_world
    acc = L.MeshAcc()
    hs = span / 2
    ids = [acc.vert((cen.x - hs, cen.y - hs, 0.015), (1, 1, 1), 0.0), acc.vert((cen.x + hs, cen.y - hs, 0.015), (1, 1, 1), 0.0),
           acc.vert((cen.x + hs, cen.y + hs, 0.015), (1, 1, 1), 0.0), acc.vert((cen.x - hs, cen.y + hs, 0.015), (1, 1, 1), 0.0)]
    acc.face(ids, 0, uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    m = gm_textured("GM_" + name, {"basecolor": atlas_path, "normal": _flat_normal(atlas_path.parent), "orm": _flat_orm(atlas_path.parent)})
    ob = acc.build(name, [m], smooth=True)
    return ob, {"atlas": atlas_path.name, "span_m": round(span, 3), "views": ["top_-Z"], "samples": samples}


def _flat_normal(d):
    p = d / "flat_normal.png"
    if not p.exists():
        from PIL import Image
        Image.new("RGB", (4, 4), (128, 128, 255)).save(p)
    return p


def _flat_orm(d):
    p = d / "flat_orm_r075.png"
    if not p.exists():
        from PIL import Image
        Image.new("RGB", (4, 4), (255, 191, 0)).save(p)
    return p


# --------------------------------------------------------------------------- export
def export_glb(ob, path, wind):
    """glTF 2.0 binary: Y-up, COLOR_0 = vertex colour (albedo tint; spec multiplies baseColorTexture),
    _WIND_WEIGHT custom attribute (0 root .. 1 tip), wind params in node extras."""
    me = ob.data
    if "wind_weight" in me.attributes and "_WIND_WEIGHT" not in me.attributes:
        src = me.attributes["wind_weight"]
        dst = me.attributes.new("_WIND_WEIGHT", "FLOAT", "POINT")
        vals = [0.0] * len(src.data)
        src.data.foreach_get("value", vals)
        dst.data.foreach_set("value", vals)
    if "Col" in me.color_attributes:
        me.color_attributes.active_color = me.color_attributes["Col"]
    ob["eco_wind"] = {"amplitude_m": wind[0], "frequency_hz": wind[1], "flutter": wind[2],
                      "channel": L.WIND_PROP} if wind else {"channel": None}
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_apply=True,
                              export_vertex_color="ACTIVE", export_all_vertex_colors=False,
                              export_attributes=True, export_extras=True, export_yup=True,
                              export_image_format="AUTO", export_materials="EXPORT", export_tangents=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def glb_summary(path):
    """Parse the GLB JSON chunk to record what actually got exported (not what we intended)."""
    data = pathlib.Path(path).read_bytes()
    ln = int.from_bytes(data[12:16], "little")
    js = json.loads(data[20:20 + ln])
    prims = [p for m in js.get("meshes", []) for p in m["primitives"]]
    return {
        "attributes": sorted({k for p in prims for k in p["attributes"]}),
        "materials": [{"name": m.get("name"), "alphaMode": m.get("alphaMode", "OPAQUE"),
                       "alphaCutoff": m.get("alphaCutoff"), "doubleSided": m.get("doubleSided", False),
                       "baseColorTexture": "baseColorTexture" in m.get("pbrMetallicRoughness", {}),
                       "normalTexture": "normalTexture" in m,
                       "metallicRoughnessTexture": "metallicRoughnessTexture" in m.get("pbrMetallicRoughness", {})}
                      for m in js.get("materials", [])],
        "images": len(js.get("images", [])),
        "bytes": len(data),
    }


# --------------------------------------------------------------------------- main
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--kit-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--impostor-samples", type=int, default=24)
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out).resolve()
    for sub in ("glb", "textures", "impostors"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    kit_json = json.loads(pathlib.Path(a.kit_json).read_text())
    bpy.ops.wm.open_mainfile(filepath=a.kit)
    sc = bpy.context.scene
    L.ensure_cycles()

    # 1) verify the reused kit geometry against its build record (provenance, no silent drift)
    reuse = {}
    kit_assets = {x["id"]: x for x in kit_json.get("assets", [])} if isinstance(kit_json.get("assets"), list) else kit_json.get("assets", {})
    for oid, (verdict, why) in SELECTION.items():
        ob = bpy.data.objects.get(oid)
        rec = kit_assets.get(oid, {})
        gh = L.geometry_hash(ob) if ob else None
        reuse[oid] = {"verdict": verdict, "reason": why, "geometry_sha256": gh,
                      "matches_kit_build": (gh == rec.get("geometry_sha256")) if rec else None,
                      "tris_lod0": L.tri_count(ob) if ob else None}

    # 2) PBR maps for the existing leaf cards + new moss set
    tex = {}
    for stem in ("leaf_cluster_oak", "leaf_cluster_beech", "leaf_cluster_apple", "leaf_spray_needle"):
        tex[stem] = derive_card_pbr(KIT_PKG / "textures" / f"{stem}.png", out / "textures", stem)
    tex["moss_tile"] = paint_moss_set(out / "textures", SEED)
    gms = build_game_materials(tex)

    # 3) new CG-fit assets
    col_new = bpy.data.collections.new("ECO_V2_NEW")
    sc.collection.children.link(col_new)
    M_moss = bpy.data.materials.new("M_eco_moss")
    new_specs = [
        ("eco_turf_meadow_a", build_turf_patch, {}, ["M_eco_grass"]),
        ("eco_flower_daisy_clump", build_daisy_clump, {}, ["M_eco_flower"]),
        ("eco_flower_violet_cushion", build_violet_cushion, {}, ["M_eco_flower"]),
        ("eco_flower_spike_clump", build_spike_clump, {}, ["M_eco_flower"]),
        ("eco_moss_cushion_a", build_moss, {"kind": "cushion"}, ["M_eco_moss"]),
        ("eco_moss_mat_b", build_moss, {"kind": "mat"}, ["M_eco_moss"]),
        ("eco_shrub_round_a", build_shrub, {}, ["M_eco_bark", "M_eco_leafcard_beech"]),
    ]
    new_stats = {}
    for oid, fn, kw, mnames in new_specs:
        acc, st = fn(SEED, **kw)
        mats_ = [bpy.data.materials.get(n) or M_moss for n in mnames]
        ob = acc.build(oid, mats_, collection=col_new)
        new_stats[oid] = {"stats": st, "geometry_sha256": L.geometry_hash(ob), "tris_lod0": L.tri_count(ob),
                          "dims_m": [round(v, 3) for v in ob.dimensions]}

    # 4) per packaged asset: game copy (LOD0), LOD1 thin, LOD2 impostor, GLB export
    col_pkg = bpy.data.collections.new("ECO_V2_PACKAGE")
    sc.collection.children.link(col_pkg)
    # albedo calibration toward approved CG value structure (G2-01 §4: crowns 40 % too dark, no lit tops)
    GAIN = {"M_eco_leafcard_oak": 1.30, "M_eco_leafcard_beech": 1.25, "M_eco_leafcard_apple": 1.2,
            "M_eco_leafcard_needle": 1.1, "M_eco_grass": 1.12, "M_eco_flower": 1.0, "M_eco_bark": 0.95}
    LOD1 = {"tree": (0.5, 1.3), "shrub": (0.5, 1.3), "grass": (0.45, 1.12), "turf": (0.28, 1.18),
            "flower": (0.6, 1.08), "moss": None}
    records = {}
    for oid, (cat, wind, rule) in PACKAGED_META.items():
        src = bpy.data.objects[oid]
        g0 = src.copy()
        g0.data = src.data.copy()
        g0.name = oid + "_LOD0"
        g0.data.name = g0.name + "_mesh"
        col_pkg.objects.link(g0)
        calibrate_vcol(g0, GAIN)
        mslots = [m.name for m in g0.data.materials]
        assign_game_materials(g0, gms)
        g0.location = (0, 0, 0)
        lods = [g0]
        if LOD1[cat]:
            thin_slots = {i for i, n in enumerate(mslots) if n not in ("M_eco_bark", "M_eco_apple")}
            g1 = lod_thin(g0, oid + "_LOD1", LOD1[cat][0], LOD1[cat][1], thin_slots, SEED,
                          bark_ratio=0.3 if cat in ("tree", "shrub") else 1.0)
            for c in g1.users_collection:
                c.objects.unlink(g1)
            col_pkg.objects.link(g1)
            lods.append(g1)
        if cat in ("tree", "shrub", "grass", "flower"):
            g2, imp = lod_impostor(g0, oid + "_LOD2", out / "impostors" / f"{oid}_LOD2_atlas.png", a.impostor_samples)
            for c in g2.users_collection:
                c.objects.unlink(g2)
            col_pkg.objects.link(g2)
            lods.append(g2)
        elif cat == "turf":
            g2, imp = lod_decal_top(g0, oid + "_LOD2", out / "impostors" / f"{oid}_LOD2_top.png", a.impostor_samples)
            for c in g2.users_collection:
                c.objects.unlink(g2)
            col_pkg.objects.link(g2)
            lods.append(g2)
        else:
            imp = None
        rec = {"category": cat, "placement_rule": rule, "wind": wind, "source_material_slots": mslots, "lods": []}
        for k, ob in enumerate(lods):
            ob.location = (0, 0, 0)
            p = out / "glb" / f"{ob.name}.glb"
            export_glb(ob, p, wind)
            rec["lods"].append({"lod": k, "file": f"glb/{p.name}", "tris": L.tri_count(ob),
                                "dims_m": [round(v, 3) for v in ob.dimensions], "glb": glb_summary(p)})
        if imp:
            rec["impostor"] = imp
        records[oid] = rec
        # spread package objects for the editable .blend (x rows), not a world placement
    for i, oid in enumerate(PACKAGED_META):
        for k in range(3):
            ob = bpy.data.objects.get(f"{oid}_LOD{k}")
            if ob:
                ob.location = (k * 9.0, -i * 9.0, 0)
    # hide reused kit collection content from renders of the package blend (kept for provenance)
    for o in sc.objects:
        if o.users_collection and all(c.name not in ("ECO_V2_PACKAGE",) for c in o.users_collection):
            o.hide_render = True
            o.hide_set(True) if o.name in bpy.context.view_layer.objects else None
    # relative image paths valid once the package sits at assets/candidates/LIND-ECO-01/integration_v2/
    for img in bpy.data.images:
        fp = pathlib.Path(bpy.path.abspath(img.filepath)).resolve() if img.filepath else None
        if not fp:
            continue
        if out in fp.parents:
            img.filepath = "//" + fp.relative_to(out).as_posix()
        elif fp.parent == KIT_PKG / "textures":
            img.filepath = "//../eco_kit_v1/textures/" + fp.name
    blend = out / "eco_integration_v2.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True, relative_remap=False)

    build = {
        "schema": "two.lind.eco.integration.v2", "task_id": "LIND-ECO-01", "blender": bpy.app.version_string,
        "seed_new_assets": SEED, "kit_combined_geometry_sha256": kit_json.get("combined_geometry_sha256"),
        "selection": reuse, "new_assets": new_stats, "packaged": records,
        "albedo_gain_by_source_material": GAIN, "lod1_rules": {k: v for k, v in LOD1.items()},
        "prevailing_wind_xy": list(PREVAILING_WIND[:2]),
        "status": "CANDIDATE_FOR_INTEGRATION_TEST — not adopted; G2 independent NOT_RUN for v2 assets; G4 NOT_RUN",
    }
    (out / "integration_build.json").write_text(json.dumps(build, indent=1, ensure_ascii=False))
    print("INTEGRATION_V2_DONE", len(records), "assets")


if __name__ == "__main__":
    main()
