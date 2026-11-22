"""Shared matched-view render module: identical camera rig and lighting for preview and high quality.

preview: Workbench clay + wire overlay (fast, structure) and Cycles 16 spp material views.
hq:      Cycles 128 spp, denoised when OIDN is available, 1024 px, all views.
The rig is created for the render and removed afterwards, so native sources are not altered.
"""
import math
import struct
import zlib
from pathlib import Path

import bpy
from mathutils import Vector

VIEWS = {  # character faces -Y; "right" = the character's own right side (camera on -X)
    "front": (0.0, -1.0, 0.0), "right": (-1.0, 0.0, 0.0), "back": (0.0, 1.0, 0.0),
    "left": (1.0, 0.0, 0.0), "three_quarter": (-0.7071, -0.7071, 0.0)}
MODES = {
    "preview": {"res": 512, "clay": True, "cycles_spp": 16, "cycles_views": ("front", "three_quarter"), "cycles_res": 384},
    "hq": {"res": 1024, "clay": False, "cycles_spp": 128, "cycles_views": tuple(VIEWS), "cycles_res": 1024},
}


def read_png_rgb(path):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w = 8, b"", 0
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            assert depth == 8 and ctype in (2, 6) and interlace == 0
            bpp = 3 if ctype == 2 else 4
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + n
    raw, stride, rows, prev = zlib.decompress(idat), w * bpp, [], bytearray(w * bpp)
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], (prev[i - bpp] if i >= bpp else 0)
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return w, h, bpp, rows


def _bounds(names):
    pts = []
    for n in names:
        ob = bpy.data.objects[n]
        pts += [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return (lo + hi) / 2, max(hi - lo) * 1.25


def _rig(scene, center, size):
    made = []
    cam = bpy.data.objects.new("TWO_RIG_cam", bpy.data.cameras.new("TWO_RIG_cam"))
    cam.data.type, cam.data.ortho_scale = "ORTHO", size
    scene.collection.objects.link(cam)
    made.append(cam)
    for name, loc, power, sz in (("key", (-3, -4, 4), 900, 3), ("fill", (4, -3, 1), 250, 4), ("rim", (1, 5, 4), 500, 2)):
        light = bpy.data.objects.new("TWO_RIG_" + name, bpy.data.lights.new("TWO_RIG_" + name, "AREA"))
        light.data.energy, light.data.size = power, sz
        light.location = center + Vector(loc)
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(light)
        made.append(light)
    return cam, made


def _aim(cam, center, direction, size):
    d = Vector(direction).normalized()
    cam.location = center + d * size * 3
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def _world(scene, strength, color=(1, 1, 1)):
    w = scene.world or bpy.data.worlds.new("TWO_World")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background") or w.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = list(color) + [1]
    bg.inputs["Strength"].default_value = strength


def _cycles(scene, spp, res):
    scene.render.engine = "CYCLES"
    scene.cycles.device, scene.cycles.samples = "CPU", spp
    scene.cycles.use_denoising = spp >= 64 and bool(getattr(bpy.app.build_options, "openimagedenoise", True))
    scene.render.resolution_x = scene.render.resolution_y = res
    scene.render.resolution_percentage = 100


def render(scene, mode, outdir, names):
    cfg = MODES[mode]
    outdir.mkdir(parents=True, exist_ok=True)
    center, size = _bounds(names)
    cam, made = _rig(scene, center, size)
    scene.camera = cam
    _world(scene, 0.15)
    scene.view_settings.view_transform = "AgX"
    shown = {o.name: o.hide_render for o in scene.objects if not o.name.startswith("TWO_RIG_")}
    for o in scene.objects:
        if o.type == "MESH" and o.name not in names and o.name != "CAL-hair_scatter":
            o.hide_render = True
    out = []
    try:
        if cfg["clay"]:
            scene.render.engine = "BLENDER_WORKBENCH"
            scene.render.resolution_x = scene.render.resolution_y = cfg["res"]
            sh = scene.display.shading
            sh.light, sh.color_type, sh.show_cavity = "STUDIO", "SINGLE", True
            wires = []
            for n in names:
                m = bpy.data.objects[n].modifiers.new("TWO_RIG_wire", "WIREFRAME")
                m.thickness, m.use_replace = 0.004, False
                wires.append((n, m))
            for v, d in VIEWS.items():
                _aim(cam, center, d, size)
                scene.render.filepath = str(outdir / f"{mode}_clay_wire_{v}.png")
                bpy.ops.render.render(write_still=True)
                out.append(scene.render.filepath)
            for n, m in wires:
                bpy.data.objects[n].modifiers.remove(m)
        _cycles(scene, cfg["cycles_spp"], cfg["cycles_res"])
        for v in cfg["cycles_views"]:
            _aim(cam, center, VIEWS[v], size)
            scene.render.filepath = str(outdir / f"{mode}_cycles_{v}.png")
            bpy.ops.render.render(write_still=True)
            out.append(scene.render.filepath)
    finally:
        for o in made:
            bpy.data.objects.remove(o, do_unlink=True)
        for n, h in shown.items():
            scene.objects[n].hide_render = h
    stats = []
    for p in out:
        w, h, bpp, rows = read_png_rgb(p)
        lum = [sum(r[i:i + 3]) / 3 for r in rows[::8] for i in range(0, w * bpp, bpp * 8)]
        mean = sum(lum) / len(lum)
        sd = (sum((x - mean) ** 2 for x in lum) / len(lum)) ** 0.5
        stats.append({"path": Path(p).name, "size": [w, h], "luma_mean": round(mean, 2), "luma_sd": round(sd, 2),
                      "nonblank": sd > 4.0})
    if not all(s["nonblank"] for s in stats):
        raise RuntimeError("BLANK_RENDER")
    return stats


def measure_patch(scene, patch):
    """Render the material on a flat patch under uniform white light (Standard view) and return mean sRGB8."""
    saved = (scene.render.engine, scene.camera, scene.view_settings.view_transform, scene.render.filepath,
             scene.render.resolution_x, scene.render.resolution_y)
    hidden = {o.name: o.hide_render for o in scene.objects}
    for o in scene.objects:
        o.hide_render = o.name != patch.name
    cam = bpy.data.objects.new("TWO_RIG_patchcam", bpy.data.cameras.new("TWO_RIG_patchcam"))
    cam.data.type, cam.data.ortho_scale = "ORTHO", 0.3
    scene.collection.objects.link(cam)
    cam.location = patch.location + Vector((0, -2, 0))
    cam.rotation_euler = (math.pi / 2, 0, 0)
    scene.camera = cam
    _world(scene, 1.0)
    scene.view_settings.view_transform = "Standard"
    _cycles(scene, 64, 48)
    path = bpy.app.tempdir + "two_patch.png"
    scene.render.filepath = path
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        bpy.data.objects.remove(cam, do_unlink=True)
        for n, h in hidden.items():
            scene.objects[n].hide_render = h
        (scene.render.engine, scene.camera, scene.view_settings.view_transform, scene.render.filepath,
         scene.render.resolution_x, scene.render.resolution_y) = saved
    w, h, bpp, rows = read_png_rgb(path)
    acc, n = [0, 0, 0], 0
    for r in rows[8:-8]:
        for x in range(8, w - 8):
            for c in range(3):
                acc[c] += r[x * bpp + c]
            n += 1
    return [round(a / n) for a in acc]
