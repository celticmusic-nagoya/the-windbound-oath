"""ROUTE-MAT-01 bounded Blender integration candidate. Never edits approved assets.
Run: blender -b --factory-startup --python tools/map_blender/lind/route_mat_01/build_sample.py -- --root . --out /tmp/route-mat-01
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector

SEED = 35901


def load_material(root):
    source = root / "assets/candidates/route-mat-01/attempt-01/load_material.py"
    spec = importlib.util.spec_from_file_location("route_mat_loader", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_material(root)


def make_stone(name, center, dims, stone_mat, rng):
    """Solid watertight six-faced stone with nonrectangular corners and bevel."""
    x, y, z = center
    sx, sy, sz = dims
    verts = []
    for level in (-1, 1):
        for yi, xi in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            jx = rng.uniform(-0.09, 0.09) * sx
            jy = rng.uniform(-0.08, 0.08) * sy
            jz = rng.uniform(-0.06, 0.06) * sz
            verts.append((x + xi * sx / 2 + jx, y + yi * sy / 2 + jy,
                          z + level * sz / 2 + jz))
    faces = [(3, 2, 1, 0), (4, 5, 6, 7),
             (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(stone_mat)
    uv = mesh.uv_layers.new(name="StoneFace_UV")
    # Distinct in-bounds UV islands for each face; paired maps use same UV layer.
    u0 = rng.uniform(0.08, 0.48)
    v0 = rng.uniform(0.08, 0.48)
    span = rng.uniform(0.22, 0.38)
    for poly in mesh.polygons:
        coords = ((u0, v0), (u0 + span, v0), (u0 + span, v0 + span),
                  (u0, v0 + span))
        for li, xy in zip(poly.loop_indices, coords):
            uv.data[li].uv = xy
        poly.use_smooth = False
    bevel = obj.modifiers.new("RealEdgeRelief", "BEVEL")
    bevel.width = min(sx, sy, sz) * 0.065
    bevel.segments = 3
    if hasattr(bevel, "affect"):
        bevel.affect = "EDGES"
    weighted = obj.modifiers.new("WeightedNormals", "WEIGHTED_NORMAL")
    return obj


def aim(camera, point):
    direction = Vector(point) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
    root, out = a.root.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    mat, loaded = load_material(root)
    mortar = bpy.data.materials.new("Mortar_SeparateCandidate")
    mortar.diffuse_color = (0.21, 0.20, 0.17, 1)
    stones = []
    # Bounded abutment face. Course heights and bond vary; geometry is not a 2D facade.
    z = 0.0
    for row in range(5):
        height = rng.uniform(0.32, 0.49)
        cursor = -2.25 + rng.uniform(-0.18, 0.12)
        while cursor < 2.1:
            width = min(rng.uniform(0.47, 1.03), 2.28 - cursor)
            if width < 0.19:
                break
            depth = rng.uniform(0.56, 0.91)
            obj = make_stone("Stone_%02d" % len(stones),
                             (cursor + width / 2, rng.uniform(-0.06, 0.04),
                              z + height / 2), (width - 0.035, depth, height - 0.028),
                             mat, rng)
            stones.append(obj)
            cursor += width
        z += height
    # Real structural backfill/support, not a texture painted onto a plane.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.40, z / 2))
    support = bpy.context.object
    support.name = "Abutment_Backfill_Separate"
    support.dimensions = (4.45, 0.44, z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    support.data.materials.append(mortar)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.14))
    ground = bpy.context.object
    ground.name = "Ground_Reference"
    ground.dimensions = (7, 5, 0.25)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ground.data.materials.append(mortar)
    world = bpy.context.scene.world
    world.color = (0.24, 0.24, 0.24)
    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4, 7))
    light = bpy.context.object
    light.data.energy = 850
    light.data.shape = "DISK"
    light.data.size = 5
    bpy.ops.object.camera_add(location=(6, -8, 5))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_percentage = 100
    views = [
        ("overview", (6, -8, 5), (0, 0, 1), 960, 720),
        ("junction-detail", (1.6, -3.6, 2.3), (0, 0, 1.2), 960, 720),
        ("gameplay-distance", (9, -12, 9), (0, 0, 1), 640, 480),
    ]
    for name, position, target, w, h in views:
        cam.location = position
        aim(cam, target)
        scene.render.resolution_x, scene.render.resolution_y = w, h
        scene.render.filepath = str(out / (name + ".png"))
        bpy.ops.render.render(write_still=True)
    # Pack images to keep the saved blend inspectable outside the checkout.
    bpy.ops.file.pack_all()
    blend = out / "route-mat-01-candidate.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report = {
        "status": "TECHNICAL_CANDIDATE_NOT_ART_APPROVED",
        "source_commit": "62f5d8d6db43e9078a71688f9c6bdee8d1d94304",
        "seed": SEED, "blender": bpy.app.version_string,
        "stone_count": len(stones), "geometry": "individual closed six-sided solids",
        "material_maps": loaded, "real_support": support.name,
        "G1": "PARTIAL", "G2": "NOT_RUN_INDEPENDENT",
        "G3": "PARTIAL_AUTOMATED", "G4": "NOT_RUN",
        "files": {},
    }
    for path in [blend] + [out / (v[0] + ".png") for v in views]:
        report["files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (out / "qa.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
