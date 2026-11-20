"""LIND-ECO-01 integration v2 — evaluation renders of the packaged game-material assets.

  blender -b --factory-startup --python-exit-code 1 --python tools/map_blender/lind/ecology/eco_integration_v2_render.py -- \
      --pkg /tmp/lind_eco_v2 --shot all

Shots use the *game* materials (glTF-compatible Principled, no Cycles translucency) so what is judged is what
WebGL receives. Terrain, sea and figure are noncanonical staging proxies. Not a WORLD placement.
"""
import argparse
import hashlib
import json
import math
import pathlib
import random
import sys

import bpy
from mathutils import Vector

SHOTS = ("lineup", "closeup_small", "lod_ladder", "cliffmeadow", "gameview")
FIG_H = 1.75


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def setup(sc, w, h, samples):
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"


def clear_staging(sc):
    for o in list(sc.objects):
        if o.get("v2_stage"):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in sc.objects:
        o.hide_render = True


def stage(ob):
    ob["v2_stage"] = 1
    if ob.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(ob)
    ob.hide_render = False
    return ob


def inst(name, loc, rot_z=0.0, scale=1.0):
    src = bpy.data.objects[name]
    ob = bpy.data.objects.new(name + "_i", src.data)  # linked duplicate (shared mesh)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    ob.scale = (scale, scale, scale)
    return stage(ob)


def mat(name, col, rough=0.9):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (*col, 1)
    bs.inputs["Roughness"].default_value = rough
    return m


def ground_mat():
    m = bpy.data.materials.get("STAGE_ground")
    if m:
        return m
    m = bpy.data.materials.new("STAGE_ground")
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.9
    nz.inputs["Detail"].default_value = 6
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (0.045, 0.075, 0.018, 1)
    rp.color_ramp.elements[1].color = (0.13, 0.17, 0.045, 1)
    nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.95
    return m


def figure(loc):
    """1.75 m capsule figure, scale reference only."""
    me = bpy.data.meshes.new("fig")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.2, radius2=0.17, depth=1.45)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.725))
    sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.14)
    bmesh.ops.translate(bm, verts=sph["verts"], vec=(0, 0, FIG_H - 0.14))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat("STAGE_fig", (0.75, 0.75, 0.78), 0.6))
    ob = bpy.data.objects.new("figure_175", me)
    ob.location = loc
    return stage(ob)


def plane(name, size, loc, m, sub=0, zfn=None):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=max(1, sub), y_segments=max(1, sub), size=size / 2)
    if zfn:
        for v in bm.verts:
            v.co.z = zfn(v.co.x + loc[0], v.co.y + loc[1])
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.location = (loc[0], loc[1], 0)
    return stage(ob)


def light_day(sc):
    w = bpy.data.worlds.get("STAGE_day") or bpy.data.worlds.new("STAGE_day")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1)
    bg.inputs[1].default_value = 0.9
    sc.world = w
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 4.0
    sun.data.color = (1.0, 0.93, 0.82)
    sun.data.angle = math.radians(1.5)
    sun.rotation_euler = (math.radians(42), 0, math.radians(35))
    stage(sun)


def light_sunset(sc):
    w = bpy.data.worlds.get("STAGE_sunset") or bpy.data.worlds.new("STAGE_sunset")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    if not any(n.type == "TEX_GRADIENT" for n in nt.nodes):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        rp = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
        nt.links.new(sep.outputs["Z"], rp.inputs["Fac"])
        rp.color_ramp.elements[0].position = 0.5
        rp.color_ramp.elements[0].color = (1.0, 0.52, 0.22, 1)
        rp.color_ramp.elements[1].position = 0.72
        rp.color_ramp.elements[1].color = (0.30, 0.30, 0.62, 1)
        nt.links.new(rp.outputs["Color"], bg.inputs["Color"])
    bg.inputs[1].default_value = 0.85
    sc.world = w
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.6
    sun.data.color = (1.0, 0.70, 0.42)
    sun.data.angle = math.radians(2.0)
    # low sun over the sea (+X side, in front-right of camera like the cliff CG)
    sun.rotation_euler = (math.radians(74), 0, math.radians(105))
    stage(sun)


def cam(sc, loc, look, lens=35, ortho=None):
    c = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    c.location = loc
    d = Vector(look) - Vector(loc)
    c.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if ortho:
        c.data.type = "ORTHO"
        c.data.ortho_scale = ortho
    else:
        c.data.lens = lens
    c.data.clip_end = 500
    stage(c)
    sc.camera = c
    return c


def render(sc, path):
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return path


PACK = ["eco_tree_deciduous_a", "eco_tree_forest_tall_a", "eco_tree_apple_a", "eco_tree_conifer_a",
        "eco_shrub_round_a", "eco_hedgerow", "eco_grass_tuft_short", "eco_grass_meadow", "eco_grass_tall_lax",
        "eco_grass_coastal_dune", "eco_sedge_bank", "eco_reed_riverside", "eco_turf_meadow_a",
        "eco_flower_daisy_clump", "eco_flower_violet_cushion", "eco_flower_spike_clump",
        "eco_moss_cushion_a", "eco_moss_mat_b"]


def shot_lineup(sc, out, s):
    clear_staging(sc)
    light_day(sc)
    plane("ground", 80, (0, 0), ground_mat())
    xs = {"eco_tree_deciduous_a": (-14, 6), "eco_tree_forest_tall_a": (-5, 7), "eco_tree_apple_a": (4, 6),
          "eco_tree_conifer_a": (12, 8), "eco_shrub_round_a": (-9, 0.5), "eco_hedgerow": (-3, 0.5)}
    for n, (x, y) in xs.items():
        inst(n + "_LOD0", (x, y, 0))
    small = PACK[6:]
    for i, n in enumerate(small):
        inst(n + "_LOD0", (1.2 + (i % 6) * 1.25, -0.8 - (i // 6) * 1.4, 0))
    figure((-0.8, -1.0, 0))
    cam(sc, (1.0, -17.0, 4.2), (0.5, 2.0, 1.6), lens=30)
    setup(sc, 1280, 720, s)
    return [render(sc, out / "v2_lineup_lod0_day.png")]


def shot_closeup_small(sc, out, s):
    clear_staging(sc)
    light_day(sc)
    plane("ground", 40, (0, 0), ground_mat())
    items = ["eco_turf_meadow_a", "eco_flower_daisy_clump", "eco_flower_violet_cushion", "eco_flower_spike_clump",
             "eco_grass_meadow", "eco_grass_coastal_dune", "eco_moss_cushion_a", "eco_shrub_round_a"]
    xs = [-2.5, -1.05, -0.35, 0.35, 1.05, 1.8, 2.5, 3.7]
    for n, x in zip(items, xs):
        inst(n + "_LOD0", (x, 0.6 if n in ("eco_turf_meadow_a", "eco_shrub_round_a") else 0, 0))
    cam(sc, (0.5, -5.0, 1.35), (0.5, 0.5, 0.2), lens=26)
    setup(sc, 1280, 720, s)
    return [render(sc, out / "v2_closeup_small_lod0_day.png")]


def shot_lod_ladder(sc, out, s):
    clear_staging(sc)
    light_day(sc)
    plane("ground", 80, (0, 0), ground_mat())
    rows = [("eco_tree_deciduous_a", 9.0), ("eco_shrub_round_a", 3.2), ("eco_grass_meadow", 1.1),
            ("eco_flower_daisy_clump", 0.9), ("eco_flower_violet_cushion", 0.7), ("eco_turf_meadow_a", 2.6)]
    x = -14.0
    for n, wdt in rows:
        for k in range(3):
            if bpy.data.objects.get(f"{n}_LOD{k}"):
                inst(f"{n}_LOD{k}", (x + wdt * 0.5, 0, 0))["lod_row"] = k
        x += wdt + 1.0
    # one render per LOD level at the identical camera (matched comparison)
    paths = []
    for k in range(3):
        for o in sc.objects:
            if o.get("lod_row") is not None:
                o.hide_render = o["lod_row"] != k
        cam(sc, (-1.5, -26.0, 4.0), (-1.5, 0.0, 2.0), lens=40)
        setup(sc, 1280, 420, s)
        paths.append(render(sc, out / f"v2_lod_ladder_lod{k}.png"))
    return paths


def terrain_z(x, y):
    """Noncanonical clifftop proxy: gentle swells rising inland (-y), lip at y=+11 dropping to the sea."""
    z = 0.18 * math.sin(x * 0.35) * math.cos(y * 0.28) + 0.12 * math.sin(x * 0.9 + y * 0.6) - 0.035 * y
    if y > 11.0:
        z -= (y - 11.0) ** 2 * 1.8
    return z


def scatter_meadow(sc, area, rng, turf_lod, accents_lod):
    (x0, x1), (y0, y1) = area
    # jittered (not row-aligned) tile centres with ~30 % overlap so feathered edges interleave
    y = y0
    while y < y1:
        x = x0 + rng.uniform(0, 0.6)
        while x < x1:
            px, py = x + rng.uniform(-0.35, 0.35), y + rng.uniform(-0.35, 0.35)
            if py < 11.2:
                inst(f"eco_turf_meadow_a_{turf_lod}", (px, py, terrain_z(px, py) - 0.01), rng.uniform(0, math.tau), rng.uniform(0.95, 1.15))
            x += 1.3
        y += 1.3
    def acc(name, n, ylo, yhi, sc_rng=(0.85, 1.15)):
        for _ in range(n):
            px, py = rng.uniform(x0, x1), rng.uniform(ylo, yhi)
            inst(f"{name}_{accents_lod}", (px, py, terrain_z(px, py) - 0.01), rng.uniform(0, math.tau), rng.uniform(*sc_rng))
    span = (x1 - x0) * (y1 - y0) / 400.0
    acc("eco_flower_daisy_clump", int(26 * span), y0, 9.0)
    acc("eco_flower_violet_cushion", int(22 * span), y0 + 2, 10.8)
    acc("eco_grass_meadow", int(18 * span), y0, 9.5)
    acc("eco_grass_tuft_short", int(14 * span), y0, 10.0)
    acc("eco_grass_coastal_dune", int(16 * span), 8.8, 11.0, (0.9, 1.25))


def shot_cliffmeadow(sc, out, s):
    clear_staging(sc)
    light_sunset(sc)
    plane("terrain", 40, (0, 2), ground_mat(), sub=120, zfn=terrain_z)
    sea = plane("sea", 400, (0, 150), mat("STAGE_sea", (0.05, 0.10, 0.20), 0.15))
    sea.location.z = -24
    rng = random.Random(20261120)
    scatter_meadow(sc, ((-11, 13), (-14, 11.5)), rng, "LOD0", "LOD0")
    # oak framing the left like the cliff CG; shrubs mid-ground; moss on proxy rocks
    inst("eco_tree_deciduous_a_LOD0", (-7.5, -2.0, terrain_z(-7.5, -2.0) - 0.05), 0.6)
    inst("eco_shrub_round_a_LOD0", (5.5, 3.5, terrain_z(5.5, 3.5) - 0.05), 1.2)
    inst("eco_shrub_round_a_LOD0", (8.2, 5.0, terrain_z(8.2, 5.0) - 0.05), 2.4, 0.8)
    rk = bpy.data.objects.get("eco_rocks_river")
    for i, (x, y) in enumerate(((1.5, 1.0), (-2.5, 4.5), (3.8, 7.5))):
        if rk:
            r = inst("eco_rocks_river", (x, y, terrain_z(x, y) - 0.08), i * 1.7, 1.6)
        inst("eco_moss_mat_b_LOD0", (x, y, terrain_z(x, y) + 0.18), i * 0.9, 0.9)
        inst("eco_moss_cushion_a_LOD0", (x + 0.9, y - 0.5, terrain_z(x + 0.9, y - 0.5) - 0.01), i, 1.0)
    figure((0.2, -2.0, terrain_z(0.2, -2.0)))
    cam(sc, (-1.0, -12.5, 1.55), (3.0, 6.0, 0.4), lens=28)
    setup(sc, 1280, 720, s)
    return [render(sc, out / "v2_cliffmeadow_sunset_lod0.png")]


def shot_gameview(sc, out, s):
    return _gameview(sc, out, s, "LOD1") + _gameview(sc, out, s, "LOD2")


def _gameview(sc, out, s, turf_lod):
    """Fixed 28 deg quarter-view, ortho; 1.75 m figure = 48 px on a 720 px frame -> 27.43 px/m."""
    clear_staging(sc)
    light_day(sc)
    plane("terrain", 70, (0, 0), ground_mat(), sub=140, zfn=lambda x, y: terrain_z(x, y - 10.0))
    rng = random.Random(20261121)  # same seed for both turf LODs -> identical layout
    # game default LOD per placement rules: turf LOD1, accents LOD1, trees LOD1
    # (terrain_z shifted so the lip sits at y=+21: everything here is plateau)
    def tz(x, y):
        return terrain_z(x, y - 10.0)
    (x0, x1), (y0, y1) = (-25, 25), (-26, 18)
    y = y0
    while y < y1:
        x = x0 + rng.uniform(0, 0.6)
        while x < x1:
            px, py = x + rng.uniform(-0.35, 0.35), y + rng.uniform(-0.35, 0.35)
            if abs(px - 0.3 * py - 3.0) > 1.4:  # a worn path band stays bare (staging, not a route)
                inst(f"eco_turf_meadow_a_{turf_lod}", (px, py, tz(px, py) - 0.01), rng.uniform(0, math.tau), rng.uniform(0.95, 1.15))
            x += 1.3
        y += 1.3
    for name, n in (("eco_flower_daisy_clump", 70), ("eco_flower_violet_cushion", 60), ("eco_grass_meadow", 50),
                    ("eco_grass_tuft_short", 40), ("eco_flower_spike_clump", 18)):
        for _ in range(n):
            px, py = rng.uniform(x0, x1), rng.uniform(y0, y1)
            inst(f"{name}_LOD1", (px, py, tz(px, py) - 0.01), rng.uniform(0, math.tau), rng.uniform(0.9, 1.2))
    for (x, y, n) in ((-14, 8, "eco_tree_deciduous_a"), (12, 11, "eco_tree_forest_tall_a"), (17, -4, "eco_tree_deciduous_a"),
                      (-6, 12, "eco_shrub_round_a"), (4, 9, "eco_shrub_round_a"), (-18, -6, "eco_shrub_round_a")):
        inst(f"{n}_LOD1", (x, y, tz(x, y) - 0.05), rng.uniform(0, math.tau))
    figure((0, 0, tz(0, 0)))
    pitch = math.radians(28)
    d = Vector((0, math.cos(pitch), -math.sin(pitch)))
    target = Vector((0, 0, 0.8))
    c = cam(sc, tuple(target - d * 80), tuple(target), ortho=1280 / (48 / FIG_H))
    setup(sc, 1280, 720, s)
    p = render(sc, out / f"v2_gameview_28deg_ortho_fig48px_turf{turf_lod.lower()}.png")
    return [p]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", required=True)
    ap.add_argument("--shot", default="all")
    ap.add_argument("--samples", type=int, default=32)
    a = ap.parse_args(argv)
    pkg = pathlib.Path(a.pkg)
    out = pkg / "renders"
    out.mkdir(exist_ok=True)
    blend = pkg / "eco_integration_v2.blend"
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    sc = bpy.context.scene
    names = SHOTS if a.shot == "all" else a.shot.split(",")
    reg_p = out / "renders_v2.json"
    reg = json.loads(reg_p.read_text()) if reg_p.exists() else {"files": {}}
    build_p = pkg / "integration_build.json"
    for nm in names:
        for p in globals()["shot_" + nm](sc, out, a.samples):
            reg["files"][pathlib.Path(p).name] = {
                "sha256": sha(p), "shot": nm, "samples": a.samples, "engine": "CYCLES_CPU+OIDN",
                "blender": bpy.app.version_string, "input_blend_sha256": sha(blend),
                "integration_build_sha256": sha(build_p), "render_script_sha256": sha(__file__),
                "materials": "game (glTF-compatible) materials; staging terrain/sea/figure are proxies"}
    reg_p.write_text(json.dumps(reg, indent=1))
    print("V2_RENDER_DONE", names)


if __name__ == "__main__":
    main()
