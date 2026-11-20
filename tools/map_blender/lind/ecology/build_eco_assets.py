"""LIND-ECO-01 — deterministic build of the Rilde ecology candidate kit.

Run (pip bpy):   flock /tmp/blender.lock timeout 900 python3 tools/map_blender/lind/ecology/build_eco_assets.py --out /tmp/lind_eco
Run (Blender):   blender -b --python tools/map_blender/lind/ecology/build_eco_assets.py -- --out /tmp/lind_eco

Outputs (in --out):  eco_kit_v1.blend, eco_kit_build.json (geometry hashes, tri counts, seeds)
Also writes the LOD1 grass card texture into the candidate package (textures/grass_card_lod1.png).
Candidate only: nothing here is adopted art. Status per asset is in the manifest.
"""
import argparse
import hashlib
import json
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpy  # noqa: E402

import eco_assets as A  # noqa: E402
import eco_lib as L  # noqa: E402

MASTER_SEED = 20261116
REPO = HERE.parents[3]
PKG = REPO / "assets" / "candidates" / "LIND-ECO-01" / "eco_kit_v1"


def mats():
    return {
        "bark": L.mat_vcol("M_eco_bark", rough=0.9, noise_mod=0.8, noise_scale=9.0, spec=0.2, stretch=(4.0, 4.0, 0.35)),
        "leaf": L.mat_vcol("M_eco_leaf", rough=0.55, translucent=0.3, spec=0.4),
        "leafcard": L.mat_leafcard("M_eco_leafcard_oak", str(PKG / "textures" / "leaf_cluster_oak.png")),
        "leafcard_apple": L.mat_leafcard("M_eco_leafcard_apple", str(PKG / "textures" / "leaf_cluster_apple.png")),
        "leafcard_beech": L.mat_leafcard("M_eco_leafcard_beech", str(PKG / "textures" / "leaf_cluster_beech.png")),
        "apple": L.mat_vcol("M_eco_apple", rough=0.32, spec=0.55),
        "grass": L.mat_vcol("M_eco_grass", rough=0.6, translucent=0.3, spec=0.35),
        "wheat": L.mat_vcol("M_eco_wheat", rough=0.55, translucent=0.2, spec=0.4),
        "crop": L.mat_vcol("M_eco_crop", rough=0.5, translucent=0.2, spec=0.45),
        "soil": L.mat_vcol("M_eco_soil", rough=0.96, noise_mod=0.6, noise_scale=18.0, spec=0.15),
        "flower": L.mat_vcol("M_eco_flower", rough=0.5, translucent=0.25, spec=0.35),
        "wood": L.mat_vcol("M_eco_wood", rough=0.85, noise_mod=0.7, noise_scale=55.0, spec=0.2),
        "wood_post": L.mat_vcol("M_eco_wood_post", rough=0.9, noise_mod=0.85, noise_scale=14.0, spec=0.15, stretch=(3.0, 3.0, 0.25)),
        "wood_rail": L.mat_vcol("M_eco_wood_rail", rough=0.9, noise_mod=0.85, noise_scale=14.0, spec=0.15, stretch=(0.2, 3.0, 3.0)),
        "hay": L.mat_vcol("M_eco_hay", rough=0.9, noise_mod=0.45, noise_scale=90.0, spec=0.25),
        "plumage": L.mat_vcol("M_eco_plumage", rough=0.75, sheen=0.15, spec=0.3),
        "blockout": L.mat_vcol("M_eco_blockout", rough=0.8, spec=0.3),
        "needlecard": L.mat_leafcard("M_eco_leafcard_needle", str(PKG / "textures" / "leaf_spray_needle.png")),
        "rock": L.mat_vcol("M_eco_rock", rough=0.85, noise_mod=0.5, noise_scale=12.0, spec=0.3),
        "bank": L.mat_vcol("M_eco_bank", rough=0.95, noise_mod=0.5, noise_scale=8.0, spec=0.2),
        "water": L.mat_water(),
        "preview_ground": L.mat_ground(),
    }


# id, builder, kwargs, material keys (slot order), wind (amp, freq, flutter) or None, category, status
ASSETS = [
    ("eco_tree_deciduous_a", A.build_tree, {"preset": "deciduous"}, ["bark", "leafcard"], (0.22, 0.32, 0.30), "tree", "PROCEDURAL_CANDIDATE"),
    ("eco_tree_apple_a", A.build_tree, {"preset": "apple"}, ["bark", "leafcard_apple", "apple"], (0.16, 0.36, 0.30), "tree", "PROCEDURAL_CANDIDATE"),
    ("eco_tree_forest_tall_a", A.build_tree, {"preset": "forest_tall"}, ["bark", "leafcard_beech"], (0.28, 0.28, 0.30), "tree", "PROCEDURAL_CANDIDATE_UNREVIEWED_VARIANT"),
    ("eco_tree_conifer_a", A.build_conifer, {}, ["bark", "needlecard"], (0.20, 0.25, 0.25), "tree", "PROCEDURAL_CANDIDATE"),
    ("eco_grass_tuft_short", A.build_grass, {"preset": "tuft_short"}, ["grass"], (0.05, 0.7, 0.35), "grass", "PROCEDURAL_CANDIDATE"),
    ("eco_grass_meadow", A.build_grass, {"preset": "meadow"}, ["grass"], (0.08, 0.6, 0.35), "grass", "PROCEDURAL_CANDIDATE"),
    ("eco_grass_tall_lax", A.build_grass, {"preset": "tall_lax"}, ["grass"], (0.12, 0.55, 0.3), "grass", "PROCEDURAL_CANDIDATE"),
    ("eco_grass_coastal_dune", A.build_grass, {"preset": "coastal_dune"}, ["grass"], (0.09, 0.6, 0.3), "grass", "PROCEDURAL_CANDIDATE_UNREVIEWED_VARIANT"),
    ("eco_reed_riverside", A.build_grass, {"preset": "reed"}, ["grass"], (0.14, 0.5, 0.3), "riverside", "PROCEDURAL_CANDIDATE"),
    ("eco_sedge_bank", A.build_grass, {"preset": "sedge"}, ["grass"], (0.10, 0.5, 0.3), "riverside", "PROCEDURAL_CANDIDATE"),
    ("eco_rocks_river", A.build_rock_set, {"kind": "river"}, ["rock"], None, "riverside", "PROCEDURAL_CANDIDATE"),
    ("eco_rocks_coastal", A.build_rock_set, {"kind": "coastal"}, ["rock"], None, "coastal", "PROCEDURAL_CANDIDATE"),
    ("eco_river_water", A.build_river_water, {}, ["water"], "WATER", "water", "PROCEDURAL_CANDIDATE"),
    ("eco_river_bank", A.build_river_bank, {}, ["bank", "preview_ground"], None, "water", "MODULE_PREVIEW_TERRAIN_NOT_WORLD"),
    ("eco_wheat_patch", A.build_wheat_patch, {}, ["wheat"], (0.10, 0.5, 0.25), "field", "PROCEDURAL_CANDIDATE"),
    ("eco_vegetable_rows", A.build_vegetable_rows, {}, ["crop", "soil"], (0.03, 0.6, 0.4), "field", "PROCEDURAL_CANDIDATE"),
    ("eco_flower_patch", A.build_flower_patch, {}, ["flower"], (0.06, 0.6, 0.35), "field", "PROCEDURAL_CANDIDATE"),
    ("eco_hedgerow", A.build_hedgerow, {}, ["bark", "leafcard"], (0.06, 0.45, 0.35), "boundary", "PROCEDURAL_CANDIDATE"),
    ("eco_fence_post_rail", A.build_fence, {}, ["wood_post", "wood_rail"], None, "boundary", "PROCEDURAL_CANDIDATE"),
    ("eco_haystack", A.build_haystack, {}, ["hay", "wood"], (0.05, 0.5, 0.2), "farm_prop", "PROCEDURAL_CANDIDATE"),
    ("eco_chicken_hen_blockout", A.build_chicken, {}, ["plumage"], None, "livestock", "STRUCTURAL_BLOCKOUT_NOT_ART"),
    ("eco_cow_blockout", A.build_cow_blockout, {}, ["blockout"], None, "livestock", "STRUCTURAL_BLOCKOUT_NOT_ART"),
]


def make_grass_card_texture(path, seed):
    """LOD1 alpha card: continuous blade strokes painted on a 2x canvas and downsampled with
    premultiplied LANCZOS (soft AA alpha; G2-01: stippled binary blades). Bleed colour under alpha=0."""
    import numpy as np
    rng = L.new_rng(seed, "grasscard")
    W, H = 512, 1024
    rgb = np.zeros((H, W, 3), np.float32)
    a = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for k in range(54):
        x0 = W * (0.5 + rng.gauss(0, 0.14))
        lean = rng.uniform(-0.45, 0.45)
        Lb = H * (0.3 + 0.62 * rng.random() ** 1.5)
        w0 = rng.uniform(7.0, 12.0)
        cb = np.array([0.03, 0.07, 0.015]) * rng.uniform(0.8, 1.2)
        ct = np.array([0.40, 0.52, 0.11]) * rng.uniform(0.8, 1.1)
        if rng.random() < 0.12:
            ct = np.array([0.52, 0.44, 0.20])
        nst = int(Lb / 1.5)
        for s_ in range(nst):
            t = s_ / (nst - 1)
            cx = x0 + lean * Lb * t + lean * 80 * t * t
            cy = H - 1 - Lb * t + (abs(lean) * 0.4 * Lb * t * t)
            r = max(1.2, w0 * (1 - t) ** 0.9)
            x_lo, x_hi = int(max(0, cx - r - 1)), int(min(W, cx + r + 2))
            y_lo, y_hi = int(max(0, cy - r - 1)), int(min(H, cy + r + 2))
            if x_lo >= x_hi or y_lo >= y_hi:
                continue
            m = (xx[y_lo:y_hi, x_lo:x_hi] - cx) ** 2 + (yy[y_lo:y_hi, x_lo:x_hi] - cy) ** 2 <= r * r
            c = cb + (ct - cb) * t ** 0.8
            rgb[y_lo:y_hi, x_lo:x_hi][m] = c
            a[y_lo:y_hi, x_lo:x_hi][m] = 1.0
    A._soft_save(path, rgb, a, 2)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_grass_card_mesh(name, tex_path):
    import bmesh  # noqa: F401
    verts, faces, uvs, ww = [], [], [], []
    for k in range(3):
        ang = math.pi * k / 3
        dx, dy = math.cos(ang) * 0.25, math.sin(ang) * 0.25
        b = len(verts)
        verts += [(-dx, -dy, 0), (dx, dy, 0), (dx, dy, 0.5), (-dx, -dy, 0.5)]
        faces.append((b, b + 1, b + 2, b + 3))
        uvs += [(0, 0), (1, 0), (1, 1), (0, 1)]
        ww += [0, 0, 1, 1]
    me = bpy.data.meshes.new(name + "_mesh")
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for li, loop in enumerate(me.loops):
        uv.data[li].uv = uvs[loop.vertex_index]
    at = me.attributes.new("wind_weight", "FLOAT", "POINT")
    at.data.foreach_set("value", ww)
    me.materials.append(L.mat_image_alpha("M_eco_grass_card_lod1", str(tex_path)))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build(out_dir, seed=MASTER_SEED, save=True):
    sc = L.reset_scene()
    sc.render.fps = 24
    L.ensure_channels(sc, wind=1.0, water=1.0)
    textures = {}
    for kind in ("oak", "apple", "beech"):
        pth = A.paint_leaf_cluster(PKG / "textures" / ("leaf_cluster_%s.png" % kind), seed, kind)
        textures[pth.name] = hashlib.sha256(pth.read_bytes()).hexdigest()
    pth = A.paint_leaf_spray(PKG / "textures" / "leaf_spray_needle.png", seed, "needle")
    textures[pth.name] = hashlib.sha256(pth.read_bytes()).hexdigest()
    M = mats()
    lib = bpy.data.collections.new("ECO_LIBRARY")
    sc.collection.children.link(lib)
    records = []
    x = 0.0
    for aid, fn, kw, mkeys, wind, cat, status in ASSETS:
        acc, info = fn(seed, **kw)
        ob = acc.build(aid, [M[k] for k in mkeys], collection=lib)
        ob["lind_asset_id"] = aid
        ob["lind_status"] = status
        ob["lind_seed"] = seed
        if wind == "WATER":
            L.add_water(ob)
        elif wind:
            L.add_wind(ob, *wind)
        dims = ob.dimensions
        ob.location.x = x + dims.x / 2
        x += dims.x + 0.6
        records.append({
            "id": aid, "category": cat, "status": status, "generator": fn.__name__, "params": kw,
            "seed": seed, "materials": [M[k].name for k in mkeys],
            "triangles": L.tri_count(ob), "vertices": len(ob.data.vertices),
            "dimensions_m": [round(d, 3) for d in dims],
            "wind": ({"amplitude_m": wind[0], "frequency_hz": wind[1], "flutter": wind[2],
                      "modifier": "LIND_Wind", "node_group": L.WIND_GROUP} if wind and wind != "WATER" else None),
            "water": ({"modifier": "LIND_Water", "node_group": L.WATER_GROUP, "channel": L.WATER_PROP}
                      if wind == "WATER" else None),
            "geometry_sha256": L.geometry_hash(ob), "info": info,
        })
    tex = PKG / "textures" / "grass_card_lod1.png"
    tex_sha = make_grass_card_texture(tex, seed)
    card = make_grass_card_mesh("eco_grass_card_lod1", tex)
    card.users_collection[0].objects.unlink(card)
    lib.objects.link(card)
    L.add_wind(card, 0.08, 0.6, 0.3)
    card.location.x = x + 0.3
    card["lind_status"] = "LOD1_CARD_CANDIDATE"
    records.append({"id": "eco_grass_card_lod1", "category": "grass_lod1", "status": "LOD1_CARD_CANDIDATE",
                    "generator": "make_grass_card_mesh", "seed": seed, "triangles": L.tri_count(card),
                    "vertices": len(card.data.vertices), "materials": ["M_eco_grass_card_lod1"],
                    "texture": str(tex.relative_to(REPO)), "texture_sha256": tex_sha,
                    "wind": {"amplitude_m": 0.08, "frequency_hz": 0.6, "flutter": 0.3, "modifier": "LIND_Wind",
                             "node_group": L.WIND_GROUP},
                    "geometry_sha256": L.geometry_hash(card)})
    combined = hashlib.sha256("".join(r["geometry_sha256"] for r in records).encode()).hexdigest()
    result = {
        "task_id": "LIND-ECO-01", "candidate_id": "eco_kit_v1", "seed": seed,
        "blender_version": bpy.app.version_string,
        "script_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(HERE.glob("*.py"))},
        "channels": {"wind_property": "scene['%s']" % L.WIND_PROP, "water_property": "scene['%s']" % L.WATER_PROP,
                     "wind_ctrl": L.WIND_CTRL, "water_ctrl": L.WATER_CTRL,
                     "wind_group": L.WIND_GROUP, "water_group": L.WATER_GROUP},
        "assets": records, "combined_geometry_sha256": combined,
        "textures_sha256": {**textures, "grass_card_lod1.png": tex_sha},
    }
    if save:
        out_dir.mkdir(parents=True, exist_ok=True)
        blend = out_dir / "eco_kit_v1.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
        result["blend"] = {"path": str(blend), "sha256": hashlib.sha256(blend.read_bytes()).hexdigest(),
                           "bytes": blend.stat().st_size, "note": "binary not byte-deterministic (timestamps); geometry hashes are"}
        (out_dir / "eco_kit_build.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="/tmp/lind_eco")
    p.add_argument("--seed", type=int, default=MASTER_SEED)
    a = p.parse_args(argv)
    r = build(pathlib.Path(a.out), a.seed)
    for rec in r["assets"]:
        print("%-28s tris=%7d  %s" % (rec["id"], rec["triangles"], rec["geometry_sha256"][:12]))
    print("COMBINED", r["combined_geometry_sha256"])


if __name__ == "__main__":
    main()
