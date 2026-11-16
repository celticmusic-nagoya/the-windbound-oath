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


def lights(sc, sun_elev=38, sun_az=-35, energy=3.6, sky=(0.42, 0.55, 0.78), sky_strength=0.9):
    w = bpy.data.worlds.new("W_eco_preview")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*sky, 1)
    bg.inputs["Strength"].default_value = sky_strength
    sc.world = w
    ld = bpy.data.lights.new("SUN_eco", "SUN")
    ld.energy = energy
    ld.angle = math.radians(2.5)
    ld.color = (1.0, 0.93, 0.82)
    so = bpy.data.objects.new("SUN_eco", ld)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(90 - sun_elev), 0, math.radians(sun_az))


def ground(stage, size=240.0, mat=None):
    me = bpy.data.meshes.new("PREVIEW_GROUND")
    s = size / 2
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(mat or L.mat_ground())
    ob = bpy.data.objects.new("PREVIEW_GROUND", me)
    stage.objects.link(ob)
    return ob


def water_strip(stage, x0, x1, y0, y1, z=0.012):
    nx, ny = 24, 120
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            verts.append((x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new("PREVIEW_WATER")
    me.from_pydata(verts, [], faces)
    me.materials.append(L.mat_water())
    ob = bpy.data.objects.new("PREVIEW_WATER", me)
    stage.objects.link(ob)
    L.add_water(ob)
    # muddy bank strips either side
    for xb in (x0 - 0.35, x1):
        bm = bpy.data.meshes.new("PREVIEW_BANK")
        bm.from_pydata([(xb, y0, 0.004), (xb + 0.35, y0, 0.004), (xb + 0.35, y1, 0.004), (xb, y1, 0.004)], [], [(0, 1, 2, 3)])
        bm.materials.append(L.mat_ground("M_eco_preview_bank", (0.10, 0.08, 0.05), (0.16, 0.13, 0.08)))
        bo = bpy.data.objects.new("PREVIEW_BANK", bm)
        stage.objects.link(bo)
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
def build_vignette(stage, seed=20261116):
    rng = L.new_rng(seed, "vignette")
    ground(stage)
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
    place(stage, "eco_tree_deciduous_a", (-10.5, 7.5, 0), rot_z=0.8)
    place(stage, "eco_tree_forest_tall_a", (-15.5, 13.0, 0), rot_z=2.2)
    place(stage, "eco_tree_deciduous_a", (4.5, 14.0, 0), rot_z=3.3, scale=1.1)
    place(stage, "eco_haystack", (5.6, 2.2, 0))
    # livestock
    for (x, y, r) in ((1.2, -3.0, 0.6), (2.3, -3.6, -1.9), (-0.4, -3.9, 2.8), (3.6, -2.7, 1.2)):
        place(stage, "eco_chicken_hen_a", (x, y, 0), rot_z=r)
    # stream (preview only) with riverside reeds — demonstrates the separate water channel
    water_strip(stage, -10.2, -9.0, -9.0, 16.0)
    for k in range(26):
        side = rng.choice((-10.45, -8.75))
        place(stage, "eco_reed_riverside", (side + rng.uniform(-0.15, 0.15), rng.uniform(-8, 12), 0),
              rot_z=rng.uniform(0, math.tau), scale=rng.uniform(0.8, 1.2))
    # grass clumps on verges / margins (instances share mesh data)
    variants = ["eco_grass_tuft_short", "eco_grass_meadow", "eco_grass_tall_lax"]
    for k in range(260):
        zone = rng.random()
        if zone < 0.45:   # foreground verge in front of fence
            x, y = rng.uniform(-8.5, 11), rng.uniform(-7, -2.1)
        elif zone < 0.7:  # field margin between beds and wheat
            x, y = rng.uniform(-8.5, 10.5), rng.uniform(1.8, 2.05) if rng.random() < 0.5 else rng.uniform(6.05, 6.6)
        else:             # orchard floor
            x, y = rng.uniform(7.5, 15), rng.uniform(-1, 10)
        place(stage, rng.choice(variants), (x, y, 0), rot_z=rng.uniform(0, math.tau), scale=rng.uniform(0.8, 1.35))
    # sparse grass cards (LOD1 alpha path) in the far orchard
    for k in range(60):
        place(stage, "eco_grass_card_lod1", (rng.uniform(8, 16), rng.uniform(10, 16), 0), rot_z=rng.uniform(0, math.tau))


VIGNETTE_CAM = ((-1.0, -15.5, 7.6), (1.2, 3.0, 0.6), 30.0)


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
    camera(sc, (-6.0, -6.5, 3.2), (-3.0, 3.0, 0.4), 28.0)  # stream + wheat + verge in frame
    outs = []
    for wind in (1.0, 0.0):
        L.set_channel(sc, wind=wind, water=1.0)
        for f in (12, 30):
            outs.append(render(sc, "eco_windpair_wind%d_f%02d" % (int(wind), f), frame=f))
    return outs


def shot_lineup_large(samples):
    sc, lib, stage = open_kit()
    ground(stage, mat=L.mat_ground("M_eco_preview_neutral", (0.20, 0.20, 0.18), (0.26, 0.25, 0.22)))
    items = [("eco_tree_deciduous_a", -9.0, 4), ("eco_tree_apple_a", -2.2, 3), ("eco_tree_forest_tall_a", 4.6, 5),
             ("eco_hedgerow", 10.8, 3), ("eco_haystack", 14.8, 3), ("eco_cow_blockout", 18.0, 2)]
    for aid, x, y in items:
        place(stage, aid, (x, y, 0))
    lower = [("eco_wheat_patch", -6.6, -3.2), ("eco_vegetable_rows", -3.6, -3.2), ("eco_flower_patch", 0.6, -3.2),
             ("eco_fence_post_rail", 6.4, -2.6), ("eco_chicken_hen_a", 11.0, -3.0), ("eco_grass_meadow", 12.2, -3.0),
             ("eco_grass_tall_lax", 13.2, -3.0), ("eco_reed_riverside", 14.4, -3.0)]
    for aid, x, y in lower:
        place(stage, aid, (x, y, 0))
    lights(sc, sun_elev=42, sun_az=-30)
    setup_render(sc, 1280, 720, samples)
    camera(sc, (4.5, -24.0, 7.5), (4.5, 1.0, 2.2), 30.0)
    L.set_channel(sc, wind=0.0)
    return [render(sc, "eco_lineup_large_wind0")]


def shot_lineup_small(samples):
    sc, lib, stage = open_kit()
    ground(stage, mat=L.mat_ground("M_eco_preview_neutral", (0.20, 0.20, 0.18), (0.26, 0.25, 0.22)))
    items = ["eco_grass_tuft_short", "eco_grass_meadow", "eco_grass_tall_lax", "eco_grass_coastal_dune",
             "eco_reed_riverside", "eco_grass_card_lod1", "eco_chicken_hen_a"]
    xs = [-2.4, -1.5, -0.45, 0.65, 1.6, 2.55, 3.4]
    for aid, x in zip(items, xs):
        place(stage, aid, (x, 0, 0), rot_z=(math.radians(200) if aid == "eco_chicken_hen_a" else 0))
    lights(sc, sun_elev=40, sun_az=-40)
    setup_render(sc, 1280, 560, samples)
    camera(sc, (0.5, -6.8, 1.6), (0.5, 0, 0.42), 38.0)
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
    place(stage, "eco_chicken_hen_a", (0.55, -0.55, 0), rot_z=math.radians(215))
    lights(sc, sun_elev=26, sun_az=-60, energy=4.0)
    setup_render(sc, 1280, 720, samples)
    camera(sc, (0.2, -3.3, 0.75), (0.4, 0.8, 0.45), 40.0)
    L.set_channel(sc, wind=1.0)
    return [render(sc, "eco_closeup_grass_wheat_wind1_f12")]


ICON_ITEMS = ["eco_tree_deciduous_a", "eco_tree_apple_a", "eco_tree_forest_tall_a", "eco_hedgerow", "eco_haystack",
              "eco_wheat_patch", "eco_vegetable_rows", "eco_flower_patch", "eco_fence_post_rail",
              "eco_grass_tuft_short", "eco_grass_meadow", "eco_grass_tall_lax", "eco_grass_coastal_dune",
              "eco_reed_riverside", "eco_chicken_hen_a", "eco_cow_blockout"]


def shot_icons(samples):
    """Game-camera (ortho, 30 deg elevation, 45 deg yaw) transparent renders, fitted per asset."""
    sc, lib, stage = open_kit()
    lights(sc, sun_elev=45, sun_az=-35)
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
         "closeup": shot_closeup, "windpair": shot_windpair, "icons": shot_icons}
DEFAULT_SAMPLES = {"lineup_large": 40, "lineup_small": 48, "vignette": 48, "closeup": 48, "windpair": 24, "icons": 24}


def record(paths, shot, samples):
    reg = OUT / "renders.json"
    data = json.loads(reg.read_text()) if reg.exists() else {"blender_version": bpy.app.version_string, "files": {}}
    for p in paths:
        data["files"][p.name] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "shot": shot,
                                 "samples": samples, "engine": "CYCLES_CPU+OIDN"}
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
