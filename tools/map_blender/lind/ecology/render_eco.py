"""LIND-ECO-01 — evidence renders for the ecology candidate kit (Cycles CPU, <=1280px).

  flock /tmp/blender.lock timeout 900 python3 tools/map_blender/lind/ecology/render_eco.py --shot <name> [--samples N]
  shots: lineup_large lineup_small vignette closeup windpair icons all
Opens /tmp/lind_eco/eco_kit_v1.blend (run build_eco_assets.py first) and writes PNGs to
assets/candidates/LIND-ECO-01/eco_kit_v1/renders/ plus renders.json (SHA-256 per file).
Preview ground / water / sky are staging only (WORLD lane owns terrain and water).
"""
import argparse
import hashlib
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import eco_assets as A  # noqa: E402
import eco_lib as L  # noqa: E402

REPO = HERE.parents[3]
PKG = REPO / "assets" / "candidates" / "LIND-ECO-01" / "eco_kit_v1"
OUT = PKG / "renders"
BLEND = pathlib.Path("/tmp/lind_eco/eco_kit_v1.blend")


def open_kit():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    L.ensure_cycles()
    sc = bpy.context.scene
    lib = bpy.data.collections["ECO_LIBRARY"]
    lib.hide_render = True
    lib.hide_viewport = True
    stage = bpy.data.collections.new("STAGE")
    sc.collection.children.link(stage)
    return sc, lib, stage


def place(stage, aid, loc, rot_z=0.0, scale=1.0):
    src = bpy.data.objects[aid]
    ob = src.copy()  # shares mesh data (instance-like), keeps LIND_Wind modifier
    stage.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    ob.scale = (scale, scale, scale)
    return ob


def setup_render(sc, w, h, samples, transparent=False):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.seed = 7
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast" if "AgX - Base Contrast" in [
        i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items] else "None"


def lights(sc, sun_elev=34, sun_az=-35, energy=4.2, sky=(0.52, 0.62, 0.80), sky_strength=1.0):
    """Warm late-morning key (matched loosely to the approved painterly CG: warm light tops,
    cool sky fill). Preview staging only."""
    w = bpy.data.worlds.new("W_eco_preview")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*sky, 1)
    bg.inputs["Strength"].default_value = sky_strength
    sc.world = w
    ld = bpy.data.lights.new("SUN_eco", "SUN")
    ld.energy = energy
    ld.angle = math.radians(2.5)
    ld.color = (1.0, 0.86, 0.66)
    so = bpy.data.objects.new("SUN_eco", ld)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(90 - sun_elev), 0, math.radians(sun_az))


def _plane(stage, name, x0, x1, y0, y1, mat, z=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    stage.objects.link(ob)
    return ob


def ground(stage, size=240.0, mat=None, hole=None):
    """Preview ground. hole=(x0, x1, y0, y1) leaves a corridor open for a river module."""
    mat = mat or L.mat_ground()
    s = size / 2
    if not hole:
        return _plane(stage, "PREVIEW_GROUND", -s, s, -s, s, mat)
    x0, x1, y0, y1 = hole
    _plane(stage, "PREVIEW_GROUND_W", -s, x0, -s, s, mat, -0.01)
    _plane(stage, "PREVIEW_GROUND_E", x1, s, -s, s, mat, -0.01)
    _plane(stage, "PREVIEW_GROUND_S", x0, x1, -s, y0, mat, -0.01)
    _plane(stage, "PREVIEW_GROUND_N", x0, x1, y1, s, mat, -0.01)


def river(stage, x0, y_scale, rng, reeds=24, sedge=30, rocks=6, y_range=None):
    """River module (water + banks) placed at x0, scaled along y, dressed with bank plants/rocks."""
    for aid in ("eco_river_bank", "eco_river_water"):
        place(stage, aid, (x0, 0, 0)).scale = (1, y_scale, 1)
    half = A.RIVER_LEN * y_scale / 2
    lo, hi = y_range or (-half + 0.5, half - 0.5)
    for k in range(reeds + sedge):
        y = rng.uniform(lo, hi)
        cx = A.river_centre_world(y, x0, y_scale)
        sd = rng.choice((-1, 1))
        aid = "eco_reed_riverside" if k < reeds else "eco_sedge_bank"
        off = rng.uniform(1.25, 1.6) if aid == "eco_reed_riverside" else rng.uniform(1.6, 2.6)
        place(stage, aid, (cx + sd * off, y, -0.1 if aid == "eco_reed_riverside" else 0),
              rot_z=rng.uniform(0, math.tau), scale=rng.uniform(0.85, 1.2))
    for k in range(rocks):
        y = rng.uniform(lo, hi)
        cx = A.river_centre_world(y, x0, y_scale)
        place(stage, "eco_rocks_river", (cx + rng.choice((-1, 1)) * rng.uniform(0.6, 1.3), y, -0.42),
              rot_z=rng.uniform(0, math.tau), scale=rng.uniform(0.7, 1.1))
    return half


def scale_proxy(stage, loc, rot_z=0.0):
    """1.75 m human scale reference (neutral grey mannequin, not a character asset)."""
    from mathutils import Matrix
    acc = L.MeshAcc()
    g = (0.55, 0.55, 0.55)
    for sx in (-1, 1):
        acc.tube([Vector((sx * 0.1, 0, 0)), Vector((sx * 0.1, 0, 0.45)), Vector((sx * 0.1, 0, 0.88))],
                 [0.065, 0.06, 0.075], 8, [g] * 3, [0] * 3, cap_tip=False, cap_base=True)
        acc.tube([Vector((sx * 0.24, 0, 1.42)), Vector((sx * 0.27, 0, 1.12)), Vector((sx * 0.28, 0.02, 0.82))],
                 [0.045, 0.04, 0.035], 8, [g] * 3, [0] * 3)
    acc.tube([Vector((0, 0, 0.85)), Vector((0, 0, 1.15)), Vector((0, 0, 1.45))], [0.17, 0.15, 0.19], 10, [g] * 3, [0] * 3)
    acc.tube([Vector((0, 0, 1.45)), Vector((0, 0, 1.53))], [0.05, 0.05], 8, [g] * 2, [0] * 2, cap_tip=False)
    acc.tube([Vector((0, 0, 1.52)), Vector((0, 0, 1.64)), Vector((0, 0, 1.75))], [0.085, 0.1, 0.02], 10, [g] * 3, [0] * 3)
    ob = acc.build("SCALE_PROXY_1.75m", [L.mat_vcol("M_scale_proxy", rough=0.6)], collection=stage)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    return ob


def camera(sc, loc, target, lens=35.0, ortho=None):
    cd = bpy.data.cameras.new("CAM")
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.clip_end = 400
    co = bpy.data.objects.new("CAM", cd)
    sc.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def render(sc, name, frame=12):
    OUT.mkdir(parents=True, exist_ok=True)
    sc.frame_set(frame)
    path = OUT / (name + ".png")
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return path


# ------------------------------------------------------------------------------ scenes
RIVER_X, RIVER_YS = -12.0, 3.0


def build_vignette(stage, seed=20261116):
    rng = L.new_rng(seed, "vignette")
    ground(stage, hole=(RIVER_X - 3.6, RIVER_X + 3.6, -A.RIVER_LEN * RIVER_YS / 2, A.RIVER_LEN * RIVER_YS / 2))
    # north farmland block: wheat strip, vegetable beds, flower margin
    for i in range(4):
        place(stage, "eco_wheat_patch", (-3.2 + i * 3.15, 3.0, 0))
        place(stage, "eco_wheat_patch", (-3.2 + i * 3.15, 5.0, 0))
    place(stage, "eco_vegetable_rows", (-6.6, 0.6, 0))
    place(stage, "eco_vegetable_rows", (-6.6, 3.0, 0))
    place(stage, "eco_flower_patch", (0.6, -0.4, 0))
    place(stage, "eco_flower_patch", (3.4, -0.6, 0), rot_z=math.pi)
    # boundaries
    place(stage, "eco_fence_post_rail", (0.8, -1.9, 0))
    place(stage, "eco_fence_post_rail", (7.4, -1.9, 0))
    place(stage, "eco_hedgerow", (-1.6, 7.2, 0))
    place(stage, "eco_hedgerow", (2.4, 7.25, 0), rot_z=math.pi)
    place(stage, "eco_hedgerow", (6.4, 7.2, 0))
    # orchard + trees
    for (x, y, r) in ((9.0, 3.2, 0.3), (12.2, 5.6, 2.1), (9.6, 8.4, 4.0), (13.4, 1.4, 1.2)):
        place(stage, "eco_tree_apple_a", (x, y, 0), rot_z=r, scale=rng.uniform(0.92, 1.08))
    place(stage, "eco_tree_deciduous_a", (-6.8, 8.6, 0), rot_z=0.8)
    place(stage, "eco_tree_forest_tall_a", (-17.5, 12.0, 0), rot_z=2.2)
    place(stage, "eco_tree_conifer_a", (-19.0, 6.0, 0), rot_z=1.0)
    place(stage, "eco_tree_conifer_a", (-16.5, 17.0, 0), rot_z=2.6, scale=1.15)
    place(stage, "eco_tree_conifer_a", (1.0, 17.5, 0), rot_z=0.3, scale=0.9)
    place(stage, "eco_tree_deciduous_a", (-17.0, -2.0, 0), rot_z=4.4, scale=0.9)
    place(stage, "eco_tree_deciduous_a", (4.5, 14.0, 0), rot_z=3.3, scale=1.1)
    place(stage, "eco_haystack", (5.6, 2.2, 0))
    # livestock are STRUCTURAL_BLOCKOUT_NOT_ART -> not placed in art vignettes; scale proxy instead
    scale_proxy(stage, (1.6, -3.2, 0), rot_z=0.3)
    # east-river style module (preview placement; the WORLD/Codex lane owns real river terrain)
    river(stage, RIVER_X, RIVER_YS, rng, reeds=40, sedge=46, rocks=10, y_range=(-12, 18))
    # grass clumps on verges / margins (instances share mesh data)
    variants = ["eco_grass_tuft_short", "eco_grass_meadow", "eco_grass_tall_lax"]
    for k in range(260):
        zone = rng.random()
        if zone < 0.45:   # foreground verge in front of fence
            x, y = rng.uniform(-7.8, 11), rng.uniform(-7, -2.1)
        elif zone < 0.7:  # field margin between beds and wheat
            x, y = rng.uniform(-8.5, 10.5), rng.uniform(1.8, 2.05) if rng.random() < 0.5 else rng.uniform(6.05, 6.6)
        else:             # orchard floor
            x, y = rng.uniform(7.5, 15), rng.uniform(-1, 10)
        place(stage, rng.choice(variants), (x, y, 0), rot_z=rng.uniform(0, math.tau), scale=rng.uniform(0.8, 1.35))
    # sparse grass cards (LOD1 alpha path) in the far orchard
    for k in range(60):
        place(stage, "eco_grass_card_lod1", (rng.uniform(8, 16), rng.uniform(10, 16), 0), rot_z=rng.uniform(0, math.tau))


VIGNETTE_CAM = ((-3.0, -17.0, 8.2), (-1.0, 3.0, 0.6), 28.0)


def shot_vignette(samples):
    sc, lib, stage = open_kit()
    build_vignette(stage)
    lights(sc)
    setup_render(sc, 1280, 720, samples)
    camera(sc, *VIGNETTE_CAM)
    L.set_channel(sc, wind=1.0, water=1.0)
    return [render(sc, "eco_farmland_vignette_wind1_f12")]


def shot_windpair(samples):
    sc, lib, stage = open_kit()
    build_vignette(stage)
    lights(sc)
    setup_render(sc, 960, 540, samples)
    camera(sc, (-6.2, -9.5, 3.6), (-8.0, 3.0, 0.2), 30.0)  # river + reeds + beds + wheat in frame
    outs = []
    for wind in (1.0, 0.0):
        L.set_channel(sc, wind=wind, water=1.0)
        for f in (12, 30):
            outs.append(render(sc, "eco_windpair_wind%d_f%02d" % (int(wind), f), frame=f))
    return outs


def shot_gameview(samples):
    """Game camera: orthographic quarter view, 28 deg elevation from the south (field rule 25-30 deg),
    vignette content, warm light, wind=1. Downsampled to 48/96 px figure scale in postprocess."""
    sc, lib, stage = open_kit()
    build_vignette(stage)
    lights(sc)
    setup_render(sc, 1280, 720, samples)
    el = math.radians(28)
    tgt = Vector((-2.0, 3.0, 0.5))
    d = Vector((0, -math.cos(el), math.sin(el)))
    camera(sc, tgt + d * 60, tgt, ortho=30.0)
    L.set_channel(sc, wind=1.0, water=1.0)
    return [render(sc, "eco_gameview_28deg_ortho_wind1_f12")]


def shot_lineup_large(samples):
    sc, lib, stage = open_kit()
    ground(stage, mat=L.mat_ground("M_eco_preview_neutral", (0.20, 0.20, 0.18), (0.26, 0.25, 0.22)))
    items = [("eco_tree_deciduous_a", -10.0, 4), ("eco_tree_apple_a", -4.2, 3), ("eco_tree_forest_tall_a", 1.6, 5),
             ("eco_tree_conifer_a", 7.6, 5), ("eco_hedgerow", 12.6, 3), ("eco_haystack", 17.0, 3),
             ("eco_rocks_coastal", -15.6, 3), ("eco_cow_blockout", 20.6, 2)]
    for aid, x, y in items:
        place(stage, aid, (x, y, 0))
    lower = [("eco_rocks_river", -12.0, -3.0), ("eco_wheat_patch", -6.6, -3.2), ("eco_vegetable_rows", -3.6, -3.2), ("eco_flower_patch", 0.6, -3.2),
             ("eco_fence_post_rail", 6.4, -2.6), ("eco_chicken_hen_blockout", 11.0, -3.0), ("eco_grass_meadow", 12.2, -3.0),
             ("eco_grass_tall_lax", 13.2, -3.0), ("eco_reed_riverside", 14.4, -3.0)]
    for aid, x, y in lower:
        place(stage, aid, (x, y, 0))
    scale_proxy(stage, (-1.4, -3.0, 0))
    lights(sc)
    setup_render(sc, 1280, 720, samples)
    camera(sc, (2.6, -30.0, 8.5), (2.6, 1.0, 2.4), 26.0)
    L.set_channel(sc, wind=0.0)
    return [render(sc, "eco_lineup_large_wind0")]


def shot_lineup_small(samples):
    sc, lib, stage = open_kit()
    ground(stage, mat=L.mat_ground("M_eco_preview_neutral", (0.20, 0.20, 0.18), (0.26, 0.25, 0.22)))
    items = ["eco_grass_tuft_short", "eco_grass_meadow", "eco_grass_tall_lax", "eco_grass_coastal_dune",
             "eco_sedge_bank", "eco_reed_riverside", "eco_grass_card_lod1", "eco_chicken_hen_blockout"]
    xs = [-2.9, -2.0, -0.95, 0.15, 1.2, 2.25, 3.15, 3.95]
    for aid, x in zip(items, xs):
        place(stage, aid, (x, 0, 0), rot_z=(math.radians(200) if aid == "eco_chicken_hen_blockout" else 0))
    scale_proxy(stage, (4.9, 0.3, 0))
    lights(sc)
    setup_render(sc, 1280, 560, samples)
    camera(sc, (1.0, -8.6, 2.1), (1.0, 0, 0.6), 38.0)
    L.set_channel(sc, wind=0.0)
    return [render(sc, "eco_lineup_small_wind0")]


def shot_closeup(samples):
    sc, lib, stage = open_kit()
    ground(stage)
    place(stage, "eco_wheat_patch", (0.0, 1.4, 0))
    place(stage, "eco_wheat_patch", (3.15, 1.4, 0))
    place(stage, "eco_flower_patch", (-1.9, -0.6, 0))
    rng = L.new_rng(20261116, "closeup")
    for k in range(70):
        place(stage, rng.choice(["eco_grass_tuft_short", "eco_grass_meadow", "eco_grass_tall_lax"]),
              (rng.uniform(-2.6, 2.6), rng.uniform(-1.6, 0.35), 0), rot_z=rng.uniform(0, math.tau), scale=rng.uniform(0.85, 1.3))
    lights(sc, sun_elev=28, sun_az=-60)
    setup_render(sc, 1280, 720, samples)
    camera(sc, (0.2, -3.3, 0.75), (0.4, 0.8, 0.45), 40.0)
    L.set_channel(sc, wind=1.0)
    return [render(sc, "eco_closeup_grass_wheat_wind1_f12")]


def shot_water(samples):
    """River module close view at wind=0 (wind-stop): two frames, plants frozen, water flowing."""
    sc, lib, stage = open_kit()
    rng = L.new_rng(20261116, "watershot")
    ys = 2.2
    ground(stage, hole=(-3.6, 3.6, -A.RIVER_LEN * ys / 2, A.RIVER_LEN * ys / 2))
    river(stage, 0.0, ys, rng, reeds=16, sedge=22, rocks=6, y_range=(-6, 7))
    for k in range(40):
        y = rng.uniform(-6, 7)
        cx = A.river_centre_world(y, 0.0, ys)
        place(stage, rng.choice(["eco_grass_meadow", "eco_grass_tall_lax"]),
              (cx + rng.choice((-1, 1)) * rng.uniform(2.8, 5.0), y, 0), rot_z=rng.uniform(0, math.tau))
    place(stage, "eco_tree_deciduous_a", (-6.0, 4.0, 0), rot_z=1.0)
    place(stage, "eco_tree_conifer_a", (5.5, 6.0, 0), rot_z=0.4)
    lights(sc, sun_elev=34, sun_az=-50)
    scale_proxy(stage, (3.6, -1.0, 0), rot_z=0.8)
    setup_render(sc, 1280, 720, samples)
    camera(sc, (7.5, -5.0, 3.8), (-0.6, 1.2, -0.3), 30.0)
    outs = []
    L.set_channel(sc, wind=0.0, water=1.0)
    for f in (12, 30):
        outs.append(render(sc, "eco_water_module_wind0_f%02d" % f, frame=f))
    return outs



def shot_coastal_sward(samples):
    """Noncanonical Atlantic cliff grass placement study; not a cliff geometry edit.

    Seeded spatially heterogeneous clumps, a bare wind-scoured strip, and rock pockets.
    Preview plane is staging only. Uses ECO-G2 coastal grass, no old VEG-F1 method.
    """
    sc, lib, stage = open_kit()
    rng = L.new_rng(20261120, "coastal_sward_01")
    ground(stage, size=18, mat=L.mat_ground("M_coastal_preview", (0.16, 0.17, 0.13), (0.27, 0.29, 0.20)))
    # Noncanonical rock props only; no changes to PR #421 cliff or approved CG.
    for x, y, scale in ((-2.4, 0.5, 0.9), (2.0, 1.6, 1.1), (0.4, 2.6, 0.7)):
        place(stage, "eco_rocks_coastal", (x, y, -0.11),
              rot_z=rng.uniform(0, math.tau), scale=scale)
    placed = 0
    # Stratified jitter instead of repeated aligned clumps; irregular sward density.
    for ix in range(32):
        for iy in range(18):
            x = -3.8 + (ix + rng.random()) * 0.24
            y = -1.7 + (iy + rng.random()) * 0.25
            # Coastal exposure: scoured edge at y < -0.8; inland sward behind.
            edge = 0.45 + 0.35 * math.sin(x * 1.4) + 0.12 * math.sin(x * 3.2)
            density = 0.78 if y > edge else (0.35 if y > -0.8 else 0.06)
            # Explicit exclusion around visible rocks, preserving exposed stone.
            if any((x-rx)**2 + (y-ry)**2 < rr**2
                   for rx, ry, rr in ((-2.4, 0.5, 0.8), (2.0, 1.6, 0.95), (0.4, 2.6, 0.6))):
                continue
            if rng.random() >= density:
                continue
            aid = "eco_grass_coastal_dune" if rng.random() < 0.82 else "eco_grass_tuft_short"
            place(stage, aid, (x, y, -0.025),
                  rot_z=rng.uniform(-0.18, 0.18), scale=rng.uniform(0.65, 1.06))
            placed += 1
    print("COASTAL_SWARD_CANDIDATE clumps=", placed, "seed=20261120")
    lights(sc, sun_elev=30, sun_az=-42)
    setup_render(sc, 1280, 720, samples)
    camera(sc, (5.3, -7.0, 4.0), (0, 0.55, 0.12), 37.0)
    L.set_channel(sc, wind=0.65)
    return [render(sc, "eco_coastal_sward_candidate_wind065")]


ICON_ITEMS = ["eco_tree_deciduous_a", "eco_tree_apple_a", "eco_tree_forest_tall_a", "eco_tree_conifer_a",
              "eco_hedgerow", "eco_haystack", "eco_rocks_river", "eco_rocks_coastal", "eco_sedge_bank",
              "eco_wheat_patch", "eco_vegetable_rows", "eco_flower_patch", "eco_fence_post_rail",
              "eco_grass_tuft_short", "eco_grass_meadow", "eco_grass_tall_lax", "eco_grass_coastal_dune",
              "eco_reed_riverside", "eco_chicken_hen_blockout", "eco_cow_blockout"]


def shot_icons(samples):
    """Game-camera (ortho, 30 deg elevation, 45 deg yaw) transparent renders, fitted per asset."""
    sc, lib, stage = open_kit()
    lights(sc, sun_elev=40, sun_az=-35)
    setup_render(sc, 256, 256, samples, transparent=True)
    L.set_channel(sc, wind=0.0)
    outs = []
    for aid in ICON_ITEMS:
        for o in list(stage.objects):
            stage.objects.unlink(o)
        ob = place(stage, aid, (0, 0, 0))
        bpy.context.view_layer.update()
        dims = bpy.data.objects[aid].dimensions
        size = max(dims.x, dims.y, dims.z) * 1.15
        c = Vector((0, 0, dims.z * 0.45))
        el, yaw = math.radians(30), math.radians(-45)
        d = Vector((math.cos(el) * math.sin(-yaw), -math.cos(el) * math.cos(yaw), math.sin(el)))
        for o in [o for o in sc.collection.objects if o.name.startswith("CAM")]:
            bpy.data.objects.remove(o)
        camera(sc, c + d * 40, c, ortho=size)
        outs.append(render(sc, "icon256_" + aid))
    return outs


SHOTS = {"lineup_large": shot_lineup_large, "lineup_small": shot_lineup_small, "vignette": shot_vignette,
         "closeup": shot_closeup, "windpair": shot_windpair, "icons": shot_icons, "water": shot_water,
         "gameview": shot_gameview, "coastal_sward": shot_coastal_sward}
DEFAULT_SAMPLES = {"lineup_large": 40, "lineup_small": 48, "vignette": 48, "closeup": 48, "windpair": 24, "icons": 24, "water": 32, "gameview": 40, "coastal_sward": 24}


def provenance():
    """Tie every render to the exact build: script hashes, combined geometry hash, textures, .blend."""
    build = json.loads((BLEND.parent / "eco_kit_build.json").read_text())
    return {
        "build_combined_geometry_sha256": build["combined_geometry_sha256"],
        "build_script_sha256": build["script_sha256"],
        "render_script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "textures_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted((PKG / "textures").glob("*.png"))},
        "blend_sha256": hashlib.sha256(BLEND.read_bytes()).hexdigest(),
    }


def record(paths, shot, samples):
    reg = OUT / "renders.json"
    data = json.loads(reg.read_text()) if reg.exists() else {"blender_version": bpy.app.version_string, "files": {}}
    prov = provenance()
    data["provenance"] = prov
    for p in paths:
        data["files"][p.name] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "shot": shot,
                                 "samples": samples, "engine": "CYCLES_CPU+OIDN",
                                 "build_combined_geometry_sha256": prov["build_combined_geometry_sha256"],
                                 "render_script_sha256": prov["render_script_sha256"],
                                 "blend_sha256": prov["blend_sha256"]}
    data["blender_version"] = bpy.app.version_string
    reg.write_text(json.dumps(data, indent=1, sort_keys=True))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shot", required=True)
    p.add_argument("--samples", type=int, default=0)
    a = p.parse_args(argv)
    names = list(SHOTS) if a.shot == "all" else [a.shot]
    for nm in names:
        s = a.samples or DEFAULT_SAMPLES[nm]
        paths = SHOTS[nm](s)
        record(paths, nm, s)
        for pth in paths:
            print("RENDERED", pth)


if __name__ == "__main__":
    main()
