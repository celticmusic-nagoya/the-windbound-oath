"""LIND-WORLD-01 deterministic Rilde region terrain build (candidate, PROPOSED_NOT_LOCKED).

Builds a real heightfield terrain (coastal Windward Cliffs, SW inlet + port basin,
village platform, north farm terraces, east N->S river with carved channel/banks,
raid riverside bluff, SE downstream lowland), draped road surfaces, sea plane,
river water surface, bridge abutment BLOCKOUTS, far-vista hills proxy, interface
anchors/zones, procedural PBR-ish materials blended by a per-vertex mask.

All coordinates come from docs/production/lind/world/lind-world-terrain.v1.json.

Run (bpy module):
  flock /tmp/blender.lock timeout 900 python3 tools/map_blender/lind/world/build_terrain.py --render all
Run (Blender CLI / CI):
  blender -b --python tools/map_blender/lind/world/build_terrain.py -- --render all
Options: --seed N  --candidate-id ID  --spec PATH  --render none|all|<comma list>
         --samples N  --no-blend
"""
import argparse
import hashlib
import json
import math
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import terrain_fields as tf  # noqa: E402

TASK_ID = "LIND-WORLD-01"
CANDIDATE_DEFAULT = "lind-world-terrain-c01"
BUILD_VERSION = "lind-world-build-1.0"
RENDER_NAMES = ["map_topdown", "map_topdown_annotated", "overview_3q",
                "cam_sunset_cliff_cg", "cam_village_plaza_cg", "cam_raid_riverside_cliff"]


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--spec", default=str(tf.DEFAULT_SPEC))
    p.add_argument("--seed", type=int, default=tf.DEFAULT_SEED)
    p.add_argument("--candidate-id", default=CANDIDATE_DEFAULT)
    p.add_argument("--out-root", default=str(tf.REPO_ROOT / "assets/candidates/LIND-WORLD-01"))
    p.add_argument("--render", default="none")
    p.add_argument("--samples", type=int, default=32)
    p.add_argument("--no-blend", action="store_true")
    return p.parse_args(argv)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ mesh helpers
def grid_mesh(name, X, Y, Z, face_mask=None, collection=None):
    ny, nx = Z.shape
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1).astype(np.float32)
    jj, ii = np.meshgrid(np.arange(ny - 1), np.arange(nx - 1), indexing="ij")
    v0 = (jj * nx + ii).ravel()
    quads = np.stack([v0, v0 + 1, v0 + nx + 1, v0 + nx], axis=1)  # CCW from above
    if face_mask is not None:
        quads = quads[face_mask.ravel()]
    used = np.unique(quads)
    remap = -np.ones(len(verts), dtype=np.int64)
    remap[used] = np.arange(len(used))
    quads = remap[quads]
    verts = verts[used]
    obj = mesh_from_arrays(name, verts, quads, collection)
    return obj, used


def mesh_from_arrays(name, verts, quads, collection=None):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", np.asarray(verts, dtype=np.float32).ravel())
    nq = len(quads)
    me.loops.add(nq * 4)
    me.loops.foreach_set("vertex_index", np.asarray(quads, dtype=np.int32).ravel())
    me.polygons.add(nq)
    me.polygons.foreach_set("loop_start", np.arange(0, nq * 4, 4, dtype=np.int32))
    me.update(calc_edges=True)
    try:
        me.shade_smooth()
    except AttributeError:
        me.polygons.foreach_set("use_smooth", np.ones(nq, dtype=bool))
    obj = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def add_color_attr(obj, name, rgba):
    attr = obj.data.color_attributes.new(name, "FLOAT_COLOR", "POINT")
    attr.data.foreach_set("color", np.asarray(rgba, dtype=np.float32).ravel())


def ribbon(name, xs, ys, zs, half_widths, ncross, collection, z_fn=None):
    """Quad ribbon along a polyline; normals face +Z."""
    pts = np.stack([xs, ys], axis=1)
    tang = np.gradient(pts, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    left = np.stack([-tang[:, 1], tang[:, 0]], axis=1)
    offs = np.linspace(-1.0, 1.0, ncross)
    verts = []
    for i in range(len(xs)):
        for o in offs:
            px, py = pts[i] + left[i] * o * half_widths[i]
            pz = z_fn(px, py) if z_fn else zs[i]
            verts.append((px, py, pz))
    quads = []
    for i in range(len(xs) - 1):
        for k in range(ncross - 1):
            a = i * ncross + k
            quads.append((a, a + ncross, a + ncross + 1, a + 1))
    return mesh_from_arrays(name, np.array(verts), np.array(quads), collection)


def resample_polyline(pts, step):
    pts = np.asarray(pts, dtype=np.float64)
    seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seglen)])
    n = max(int(cum[-1] / step), 1)
    s = np.linspace(0, cum[-1], n + 1)
    return s, np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1]), cum


# ------------------------------------------------------------------ materials
def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return nt


def _noise(nt, coord, scale, seed_w, detail=6.0):
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    if "W" in noise.inputs:
        noise.noise_dimensions = "4D"
        noise.inputs["W"].default_value = seed_w
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    return noise


def _layer_bsdf(nt, coord, c1, c2, scale, rough, bump_strength=0.0, seed_w=0.0, macro_scale=0.0):
    noise = _noise(nt, coord, scale, seed_w)
    fac = noise.outputs["Fac"]
    if macro_scale > 0:
        macro = _noise(nt, coord, macro_scale, seed_w + 0.5, 3.0)
        a = nt.nodes.new("ShaderNodeMath")
        a.operation = "MULTIPLY_ADD"
        nt.links.new(noise.outputs["Fac"], a.inputs[0])
        a.inputs[1].default_value = 0.4
        b = nt.nodes.new("ShaderNodeMath")
        b.operation = "MULTIPLY"
        nt.links.new(macro.outputs["Fac"], b.inputs[0])
        b.inputs[1].default_value = 0.6
        nt.links.new(b.outputs[0], a.inputs[2])
        fac = a.outputs[0]
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (*c1, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (*c2, 1.0)
    nt.links.new(fac, ramp.inputs["Fac"])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    if bump_strength > 0:
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = bump_strength
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return bsdf


def _mix(nt, fac_socket, a, b):
    m = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fac_socket, m.inputs[0])
    nt.links.new(a.outputs[0], m.inputs[1])
    nt.links.new(b.outputs[0], m.inputs[2])
    return m


def mat_terrain():
    mat = bpy.data.materials.new("M_terrain_blend_candidate")
    nt = _nodes(mat)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "terrain_mask"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(attr.outputs["Color"], sep.inputs["Color"])
    grass = _layer_bsdf(nt, coord, (0.07, 0.14, 0.03), (0.30, 0.38, 0.09), 0.06, 0.92, 0.15, 1.0, macro_scale=0.004)
    soil = _layer_bsdf(nt, coord, (0.20, 0.13, 0.07), (0.36, 0.25, 0.13), 0.25, 0.95, 0.2, 2.0)
    sand = _layer_bsdf(nt, coord, (0.55, 0.48, 0.34), (0.72, 0.65, 0.48), 0.4, 0.85, 0.1, 3.0)
    rock = _layer_bsdf(nt, coord, (0.22, 0.21, 0.20), (0.50, 0.48, 0.44), 0.18, 0.8, 0.6, 4.0)
    wetb = _layer_bsdf(nt, coord, (0.06, 0.08, 0.04), (0.14, 0.15, 0.08), 0.1, 0.45, 0.1, 5.0)
    m1 = _mix(nt, sep.outputs["Blue"], grass, soil)
    m2 = _mix(nt, sep.outputs["Green"], m1, sand)
    wet_fac = nt.nodes.new("ShaderNodeMath")
    wet_fac.operation = "MULTIPLY"
    wet_fac.inputs[1].default_value = 0.45
    nt.links.new(attr.outputs["Alpha"], wet_fac.inputs[0])
    m3 = _mix(nt, wet_fac.outputs[0], m2, wetb)
    m4 = _mix(nt, sep.outputs["Red"], m3, rock)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(m4.outputs[0], out.inputs["Surface"])
    return mat


def mat_water(name, shallow, deep, use_attr):
    mat = bpy.data.materials.new(name)
    nt = _nodes(mat)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.06
    if use_attr:
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "depth_tint"
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*shallow, 1)
        ramp.color_ramp.elements[1].color = (*deep, 1)
        nt.links.new(attr.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (*deep, 1)
    wave = nt.nodes.new("ShaderNodeTexNoise")
    wave.inputs["Scale"].default_value = 0.35
    wave.inputs["Detail"].default_value = 4.0
    nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return mat


def mat_simple(name, c1, c2, scale, rough):
    mat = bpy.data.materials.new(name)
    nt = _nodes(mat)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    b = _layer_bsdf(nt, coord, c1, c2, scale, rough, 0.3, 7.0)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return mat


# ------------------------------------------------------------------ world / light / camera
def az_el_vec(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))


PRESETS = {
    "map":    dict(az=315, el=33, sun=(1.0, 0.97, 0.92), strength=4.0, zen=(0.35, 0.5, 0.8), hor=(0.75, 0.82, 0.9), sky=0.7, glow=0.0),
    "day":    dict(az=235, el=32, sun=(1.0, 0.95, 0.88), strength=4.0, zen=(0.22, 0.4, 0.8), hor=(0.75, 0.82, 0.92), sky=0.8, glow=0.0),
    "village": dict(az=150, el=48, sun=(1.0, 0.96, 0.9), strength=4.0, zen=(0.22, 0.42, 0.85), hor=(0.8, 0.86, 0.95), sky=0.8, glow=0.0),
    "sunset": dict(az=252, el=2.5, sun=(1.0, 0.5, 0.25), strength=4.5, zen=(0.10, 0.10, 0.32), hor=(1.0, 0.48, 0.25), sky=0.9, glow=6.0),
    "dusk":   dict(az=262, el=5.0, sun=(1.0, 0.45, 0.22), strength=3.0, zen=(0.08, 0.08, 0.22), hor=(0.75, 0.35, 0.22), sky=0.7, glow=2.0),
}


def setup_world():
    world = bpy.data.worlds.new("W_lind_sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 0.55
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.name = "sky_ramp"
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.name = "sky_bg"
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.name = "sun_dot"
    nt.links.new(tc.outputs["Generated"], dot.inputs[0])
    gmr = nt.nodes.new("ShaderNodeMapRange")
    gmr.inputs["From Min"].default_value = 0.93
    gmr.inputs["From Max"].default_value = 1.0
    nt.links.new(dot.outputs["Value"], gmr.inputs["Value"])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    nt.links.new(gmr.outputs["Result"], pw.inputs[0])
    gm = nt.nodes.new("ShaderNodeMath")
    gm.operation = "MULTIPLY"
    gm.name = "glow_mul"
    nt.links.new(pw.outputs[0], gm.inputs[0])
    gbg = nt.nodes.new("ShaderNodeBackground")
    gbg.name = "glow_bg"
    nt.links.new(gm.outputs[0], gbg.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(bg.outputs[0], add.inputs[0])
    nt.links.new(gbg.outputs[0], add.inputs[1])
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    sun_data = bpy.data.lights.new("L_sun", "SUN")
    sun = bpy.data.objects.new("L_sun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    return world, sun


def apply_preset(world, sun, name):
    p = PRESETS[name]
    v = az_el_vec(p["az"], p["el"])
    sun.rotation_mode = "QUATERNION"
    sun.rotation_quaternion = v.to_track_quat("Z", "Y")
    sun.data.energy = p["strength"]
    sun.data.color = p["sun"]
    sun.data.angle = math.radians(1.5)
    nt = world.node_tree
    r = nt.nodes["sky_ramp"].color_ramp
    r.elements[0].color = (*p["hor"], 1)
    r.elements[1].color = (*p["zen"], 1)
    nt.nodes["sky_bg"].inputs["Strength"].default_value = p["sky"]
    nt.nodes["sun_dot"].inputs[1].default_value = tuple(v)
    nt.nodes["glow_mul"].inputs[1].default_value = p["glow"]
    nt.nodes["glow_bg"].inputs["Color"].default_value = (*p["sun"], 1)


def make_camera(name):
    cd = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)
    cd.clip_start = 0.5
    cd.clip_end = 40000.0
    return cam


def aim_heading(cam, loc, heading, pitch, hfov):
    cam.location = loc
    cam.rotation_mode = "XYZ"
    cam.rotation_euler = (math.radians(90 + pitch), 0.0, math.radians(-heading))
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.lens_unit = "FOV"
    cam.data.angle = math.radians(hfov)


def aim_at(cam, loc, target, lens):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = d.to_track_quat("-Z", "Y")
    cam.data.lens = lens


# ------------------------------------------------------------------ build
def build(opt):
    t0 = time.time()
    spec, spec_sha, spec_path = tf.load_spec(opt.spec)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    col_terrain = bpy.data.collections.new("LIND_WORLD_TERRAIN")
    col_water = bpy.data.collections.new("LIND_WORLD_WATER")
    col_roads = bpy.data.collections.new("LIND_WORLD_ROADS")
    col_block = bpy.data.collections.new("LIND_WORLD_BLOCKOUT")
    col_iface = bpy.data.collections.new("LIND_WORLD_INTERFACE")
    for c in (col_terrain, col_water, col_roads, col_block, col_iface):
        scene.collection.children.link(c)
    col_iface.hide_render = True

    # --- terrain heightfield
    X, Y = tf.region_grid(spec)
    F = tf.compute_fields(spec, X, Y, seed=opt.seed)
    H = F["H"]
    hhash = tf.heightfield_hash(H)
    # sculpt: break grid regularity on steep cliff faces (XY jitter < 0.36 cell)
    cell = float(spec["region"]["heightfield_cell_m"])
    steep = tf.smoothstep(40.0, 65.0, F["slope"])
    jx = tf.fbm(X, Y, 18.0, opt.seed + 11, 3) * 1.8 * steep
    jy = tf.fbm(X, Y, 18.0, opt.seed + 12, 3) * 1.8 * steep
    terrain, _ = grid_mesh("terrain_heightfield", X + jx, Y + jy, H, collection=col_terrain)
    add_color_attr(terrain, "terrain_mask", F["mask"].reshape(-1, 4))
    terrain.data.materials.append(mat_terrain())
    terrain["status"] = "CANDIDATE_PROPOSED_NOT_LOCKED"
    terrain["task_id"] = TASK_ID
    terrain["interface_json_sha256"] = spec_sha
    terrain["heightfield_sha256"] = hhash
    terrain["grid_shape"] = list(H.shape)
    terrain["cell_m"] = cell
    terrain["origin_xy"] = [float(X[0, 0]), float(Y[0, 0])]
    terrain["seed"] = opt.seed

    # --- skirt to hide seams with the far proxy
    ny, nx = H.shape
    ring = ([(0, i) for i in range(nx)] + [(j, nx - 1) for j in range(1, ny)]
            + [(ny - 1, i) for i in range(nx - 2, -1, -1)] + [(j, 0) for j in range(ny - 2, 0, -1)])
    ring.append(ring[0])
    sv, sq = [], []
    for k, (j, i) in enumerate(ring):
        sv.append((X[j, i], Y[j, i], H[j, i]))
        sv.append((X[j, i], Y[j, i], min(H[j, i], 0.0) - 30.0))
        if k:
            a = 2 * (k - 1)
            sq.append((a, a + 1, a + 3, a + 2))
    skirt = mesh_from_arrays("terrain_edge_skirt", np.array(sv), np.array(sq), col_terrain)
    skirt.data.materials.append(terrain.data.materials[0])
    add_color_attr(skirt, "terrain_mask", np.tile([0, 0, 0.3, 0], (len(sv), 1)))

    # --- far vista proxy
    reg = spec["region"]
    fx = np.arange(-7000.0, 7000.1, 100.0)
    FX, FY = np.meshgrid(fx, fx)
    FF = tf.compute_fields(spec, FX, FY, seed=opt.seed, with_roads=False, far=True)
    FH = FF["H"] - 0.6
    cx = (FX[:-1, :-1] + FX[1:, 1:]) * 0.5
    cy = (FY[:-1, :-1] + FY[1:, 1:]) * 0.5
    inside = (cx > reg["x_min"]) & (cx < reg["x_max"]) & (cy > reg["y_min"]) & (cy < reg["y_max"])
    far, used = grid_mesh("far_vista_hills_proxy_blockout", FX, FY, FH, face_mask=~inside, collection=col_block)
    gy, gx = np.gradient(FH, 100.0)
    fslope = np.degrees(np.arctan(np.hypot(gx, gy)))
    frock = np.maximum(tf.smoothstep(22, 38, fslope), tf.smoothstep(380, 520, FH))
    fmask = np.stack([frock, np.zeros_like(FH), np.zeros_like(FH), np.zeros_like(FH)], -1).reshape(-1, 4)[used]
    add_color_attr(far, "terrain_mask", fmask)
    far.data.materials.append(terrain.data.materials[0])
    far["status"] = "STRUCTURAL_BLOCKOUT_NOT_ART"

    # --- sea: region tint grid + infinite-ish plane
    dc = F["coast_dist"]
    fm = (np.minimum.reduce([dc[:-1, :-1], dc[1:, :-1], dc[:-1, 1:], dc[1:, 1:]]) < 3.0)
    sea_r, used = grid_mesh("sea_surface_region", X, Y, np.zeros_like(H), face_mask=fm, collection=col_water)
    depth = np.clip(-H / 14.0, 0.0, 1.0).ravel()[used]
    sea_r.data.attributes.new("depth_tint", "FLOAT", "POINT").data.foreach_set("value", depth.astype(np.float32))
    sea_r.data.materials.append(mat_water("M_sea_candidate", (0.06, 0.30, 0.30), (0.012, 0.06, 0.12), True))
    sv = np.array([[-40000, -40000, -0.03], [40000, -40000, -0.03], [40000, 40000, -0.03], [-40000, 40000, -0.03]])
    sea = mesh_from_arrays("sea_plane", sv, np.array([[0, 1, 2, 3]]), col_water)
    sea.data.materials.append(mat_water("M_sea_deep_candidate", (0, 0, 0), (0.012, 0.06, 0.12), False))

    # --- river water surface ribbon (N -> S order preserved)
    rpts, wz, bw, _, _ = tf.river_data(spec)
    s, rx, ry, cum = resample_polyline(rpts, 4.0)
    rwz = np.interp(s, cum, wz)
    rhw = np.interp(s, cum, bw) * 0.5 + 2.5
    river = ribbon("river_water_surface", rx, ry, rwz, rhw, 5, col_water)
    river.data.materials.append(mat_water("M_river_candidate", (0, 0, 0), (0.05, 0.17, 0.17), False))
    river["flow"] = "N_to_S (vertex rows ordered upstream->downstream)"
    river["cross_section_verts"] = 5

    # --- roads draped on final terrain
    sampler = tf.make_sampler(X, Y, H)
    road_mat = mat_simple("M_road_dirt_candidate", (0.30, 0.22, 0.14), (0.48, 0.38, 0.26), 0.5, 0.95)
    road_meta = {}
    for edge in spec["route_graph"]["edges"]:
        s, ex, ey, _ = resample_polyline(edge["polyline"], 2.0)
        hw = np.full(len(s), edge["width_m"] * 0.5)
        obj = ribbon("road_" + edge["id"], ex, ey, None, hw, 4, col_roads,
                     z_fn=lambda px, py: float(sampler([px], [py])[0]) + 0.07)
        obj.data.materials.append(road_mat)
        obj["class"] = edge["class"]
        obj["max_grade"] = edge["max_grade"]
        obj["cross_section_verts"] = 4
        obj["status"] = "CANDIDATE_PROPOSED_NOT_LOCKED"
        road_meta[edge["id"]] = len(s)

    # --- bridge blockouts
    blk = mat_simple("M_blockout_grey", (0.45, 0.45, 0.5), (0.55, 0.55, 0.6), 1.0, 0.8)
    br = spec["bridge"]
    wz_b = float(next(p["water_z"] for p in spec["river"]["centreline"] if p.get("tag") == "bridge_site"))
    for ab in br["abutments"]:
        x, y = ab["xy"]
        top = br["deck_z"]
        bot = wz_b - 2.5
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, (top + bot) / 2))
        o = bpy.context.active_object
        o.name = ab["id"]
        o.data.name = ab["id"]
        o.scale = (6.0, br["deck_width_m"] + 2.0, top - bot)
        for c in o.users_collection:
            c.objects.unlink(o)
        col_block.objects.link(o)
        o.data.materials.append(blk)
        o["status"] = "STRUCTURAL_BLOCKOUT_NOT_ART"
    bx, by = br["centre_xy"]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, br["deck_z"] - 0.2))
    o = bpy.context.active_object
    o.name = "bridge_deck_footprint_blockout"
    o.data.name = o.name
    o.scale = (br["span_m"], br["deck_width_m"], 0.4)
    for c in o.users_collection:
        c.objects.unlink(o)
    col_block.objects.link(o)
    o.data.materials.append(blk)
    o["status"] = "STRUCTURAL_BLOCKOUT_NOT_ART"

    # --- interface anchors + zones
    def empty(name, loc, props):
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 8
        e.location = loc
        for k, v in props.items():
            e[k] = v
        col_iface.objects.link(e)
    for nid, n in spec["route_graph"]["nodes"].items():
        if n["xy"]:
            z = float(sampler([n["xy"][0]], [n["xy"][1]])[0])
            empty("ANCHOR_" + nid, (n["xy"][0], n["xy"][1], z), {"kind": "route_node", "status": "PROPOSED_NOT_LOCKED"})
    for a in spec["cliff_anchors"]["anchors"]:
        z = float(sampler([a["edge_xy"][0]], [a["edge_xy"][1]])[0])
        empty("ANCHOR_CLIFF_" + a["id"], (a["edge_xy"][0], a["edge_xy"][1], z), {"kind": a["kind"], "status": a["status"]})
    for a in spec["event_anchors"]:
        if a.get("xy"):
            z = float(sampler([a["xy"][0]], [a["xy"][1]])[0])
            empty("ANCHOR_EVENT_" + a["id"], (a["xy"][0], a["xy"][1], z), {"kind": "event", "status": "PROPOSED_NOT_LOCKED"})
    for zgrp in (spec["village_building_zones"]["zones"], spec["terrain_zones"]["zones"]):
        for zn in zgrp:
            if "polygon" not in zn:
                continue
            poly = np.asarray(zn["polygon"], dtype=float)
            vz = sampler(poly[:, 0], poly[:, 1]) + 1.0
            me = bpy.data.meshes.new("ZONE_" + zn["id"])
            me.from_pydata([(p[0], p[1], z) for p, z in zip(poly, vz)],
                           [(i, (i + 1) % len(poly)) for i in range(len(poly))], [])
            ob = bpy.data.objects.new("ZONE_" + zn["id"], me)
            ob["status"] = zn.get("status", "PROPOSED_NOT_LOCKED")
            col_iface.objects.link(ob)

    timings = {"build_s": round(time.time() - t0, 2)}
    return dict(spec=spec, spec_sha=spec_sha, spec_path=spec_path, X=X, Y=Y, F=F, H=H,
                hhash=hhash, sampler=sampler, timings=timings, road_meta=road_meta)


# ------------------------------------------------------------------ render
def setup_cycles(samples, res):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transparent_max_bounces = 2
    sc.cycles.seed = 0
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"


def ground(sampler, x, y):
    return float(sampler([x], [y])[0])


def do_renders(ctx, opt, outdir, which):
    spec = ctx["spec"]
    sampler = ctx["sampler"]
    world, sun = setup_world()
    cams = spec["cameras"]
    rd = outdir / "renders"
    rd.mkdir(parents=True, exist_ok=True)
    results = []
    jobs = []
    m = cams["map_topdown"]
    jobs.append(("map_topdown", "map", m["res"], "ortho"))
    jobs.append(("overview_3q", "day", cams["overview_3q"]["res"], "overview"))
    for c in cams["cg_sightlines"]:
        preset = {"cam_sunset_cliff_cg": "sunset", "cam_village_plaza_cg": "village",
                  "cam_raid_riverside_cliff": "dusk"}[c["id"]]
        jobs.append((c["id"], preset, [1280, 720], c))
    for name, preset, res, camdef in jobs:
        if which != "all" and name not in which:
            continue
        cam = make_camera("CAM_" + name)
        if camdef == "ortho":
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = m["ortho_scale_m"]
            cam.location = (m["centre_xy"][0], m["centre_xy"][1], 1500.0)
            cam.rotation_euler = (0, 0, 0)
            camrec = {"type": "ORTHO", "centre_xy": m["centre_xy"], "ortho_scale_m": m["ortho_scale_m"]}
        elif camdef == "overview":
            o = cams["overview_3q"]
            aim_at(cam, o["location"], o["look_at"], o["lens_mm"])
            camrec = o
        else:
            x, y = camdef["location"][:2]
            z = ground(sampler, x, y) + camdef["eye_height_m"]
            aim_heading(cam, (x, y, z), camdef["heading_deg"], camdef["pitch_deg"], camdef["hfov_deg"])
            camrec = dict(camdef, resolved_z=round(z, 3))
        bpy.context.scene.camera = cam
        apply_preset(world, sun, preset)
        setup_cycles(opt.samples if camdef != "ortho" else max(16, opt.samples // 2), res)
        path = rd / f"{name}.png"
        bpy.context.scene.render.filepath = str(path)
        t = time.time()
        bpy.ops.render.render(write_still=True)
        results.append({"name": name, "path": str(path.relative_to(tf.REPO_ROOT)), "preset": preset,
                        "camera": camrec, "res": res, "render_s": round(time.time() - t, 1),
                        "sha256": sha256_file(path)})
        print("[render]", name, results[-1]["render_s"], "s", flush=True)
    if which == "all" or "map_topdown_annotated" in which:
        p = annotate_map(spec, rd / "map_topdown.png", rd / "map_topdown_annotated.png")
        if p:
            results.append({"name": "map_topdown_annotated", "path": str(p.relative_to(tf.REPO_ROOT)),
                            "derived_from": "map_topdown.png (PIL overlay of interface JSON)",
                            "sha256": sha256_file(p)})
    return results


def annotate_map(spec, src, dst):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    if not src.exists():
        return None
    im = Image.open(src).convert("RGB")
    W, Hh = im.size
    m = spec["cameras"]["map_topdown"]
    cx, cy = m["centre_xy"]
    sc = m["ortho_scale_m"]

    def P(x, y):
        return ((x - cx) / sc * W + W / 2, Hh / 2 - (y - cy) / sc * Hh)
    d = ImageDraw.Draw(im, "RGBA")
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    for z in spec["terrain_zones"]["zones"]:
        if "polygon" in z:
            d.polygon([P(*p) for p in z["polygon"]], outline=(255, 255, 255, 150))
            px, py = P(*np.mean(np.asarray(z["polygon"]), axis=0))
            d.text((px - 30, py), z["id"], fill=(255, 255, 255, 200), font=font)
    for z in spec["village_building_zones"]["zones"]:
        if "polygon" in z:
            d.polygon([P(*p) for p in z["polygon"]], outline=(255, 210, 0, 255), fill=(255, 210, 0, 40))
    rp = [P(*p["xy"]) for p in spec["river"]["centreline"]]
    d.line(rp, fill=(0, 220, 255, 255), width=2)
    for k in range(1, len(rp) - 1, 3):
        (x0, y0), (x1, y1) = rp[k], rp[k + 1]
        a = math.atan2(y1 - y0, x1 - x0)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        d.polygon([(mx + 9 * math.cos(a), my + 9 * math.sin(a)),
                   (mx + 6 * math.cos(a + 2.5), my + 6 * math.sin(a + 2.5)),
                   (mx + 6 * math.cos(a - 2.5), my + 6 * math.sin(a - 2.5))], fill=(0, 220, 255, 255))
    for e in spec["route_graph"]["edges"]:
        d.line([P(*p) for p in e["polyline"]], fill=(255, 80, 40, 255), width=2)
    for nid, n in spec["route_graph"]["nodes"].items():
        if n["xy"]:
            x, y = P(*n["xy"])
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 255, 255, 255))
            d.text((x + 6, y - 7), nid, fill=(255, 255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    for a in spec["cliff_anchors"]["anchors"]:
        x, y = P(*a["edge_xy"])
        d.ellipse([x - 10, y - 10, x + 10, y + 10], outline=(255, 0, 255, 255), width=3)
        d.text((x + 12, y + 6), "CLIFF:" + a["id"], fill=(255, 120, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    for c in spec["cameras"]["cg_sightlines"]:
        x, y = P(*c["location"][:2])
        h = math.radians(c["heading_deg"])
        for off in (-c["hfov_deg"] / 2, c["hfov_deg"] / 2):
            hh = h + math.radians(off)
            d.line([(x, y), (x + 70 * math.sin(hh), y - 70 * math.cos(hh))], fill=(255, 255, 0, 220), width=1)
        d.text((x - 40, y + 8), c["id"], fill=(255, 255, 0, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    # scale bar 500 m + north arrow
    x0, y0 = 30, Hh - 40
    d.line([(x0, y0), (x0 + 500 / sc * W, y0)], fill=(255, 255, 255, 255), width=4)
    d.text((x0, y0 - 18), "500 m  (+X east, +Y north, PROPOSED_NOT_LOCKED)", fill=(255, 255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    d.polygon([(W - 40, 30), (W - 50, 60), (W - 30, 60)], fill=(255, 255, 255, 255))
    d.text((W - 45, 62), "N", fill=(255, 255, 255, 255), font=font)
    im.save(dst)
    return dst


# ------------------------------------------------------------------ main
def main():
    opt = parse_args()
    which = "all" if opt.render == "all" else ([] if opt.render == "none" else opt.render.split(","))
    outdir = pathlib.Path(opt.out_root) / opt.candidate_id
    outdir.mkdir(parents=True, exist_ok=True)
    ctx = build(opt)
    blend = outdir / f"{opt.candidate_id}.blend"
    if not opt.no_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    objects = []
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        rec = {"name": o.name, "type": o.type, "collection": o.users_collection[0].name if o.users_collection else None}
        if o.type == "MESH":
            rec["verts"] = len(o.data.vertices)
            rec["faces"] = len(o.data.polygons)
        if "status" in o.keys():
            rec["status"] = o["status"]
        objects.append(rec)
    renders = do_renders(ctx, opt, outdir, which) if which else []
    manifest = {
        "schema": "lind-world-build-manifest-v1",
        "task_id": TASK_ID,
        "candidate_id": opt.candidate_id,
        "status": "CANDIDATE_PROPOSED_NOT_LOCKED",
        "g2": "NOT_RUN (independent review pending)",
        "build_version": BUILD_VERSION,
        "fields_version": tf.FIELDS_VERSION,
        "blender_version": bpy.app.version_string,
        "numpy_version": np.__version__,
        "seed": opt.seed,
        "interface_json": str(ctx["spec_path"].relative_to(tf.REPO_ROOT)),
        "interface_json_sha256": ctx["spec_sha"],
        "script_sha256": {
            "build_terrain.py": sha256_file(HERE / "build_terrain.py"),
            "terrain_fields.py": sha256_file(HERE / "terrain_fields.py"),
        },
        "heightfield": {"sha256": ctx["hhash"], "shape": list(ctx["H"].shape),
                        "cell_m": ctx["spec"]["region"]["heightfield_cell_m"],
                        "z_min": round(float(ctx["H"].min()), 3), "z_max": round(float(ctx["H"].max()), 3)},
        "blend": {"path": str(blend.relative_to(tf.REPO_ROOT)) if blend.exists() else None,
                  "bytes": blend.stat().st_size if blend.exists() else None,
                  "sha256": sha256_file(blend) if blend.exists() else None,
                  "commit_policy": "commit only if <= 40 MB"},
        "objects": objects,
        "renders": renders,
        "timings": ctx["timings"],
        "materials": "procedural only (Noise/ColorRamp/Principled); no external textures; no third-party assets",
    }
    (outdir / "build_manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print("[done]", outdir, ctx["timings"], flush=True)


if __name__ == "__main__":
    main()
