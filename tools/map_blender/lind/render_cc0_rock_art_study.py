"""Render a non-canonical CC0 rock assembly art study from verified packed .blend sources.
No new sculpt, no final cliff claim, no official map dimensions or placements.
"""
import argparse
import bpy
import hashlib
import json
import math
import sys
from mathutils import Vector
from pathlib import Path

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bounds(objects):
    pts = [o.matrix_world @ Vector(v) for o in objects for v in o.bound_box]
    if not pts:
        raise RuntimeError("Source has no mesh bounds")
    lo = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return lo, hi

def append_source(path, collection_name):
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = [name for name in src.objects if name]
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    result = []
    for obj in dst.objects:
        if obj and obj.type == "MESH":
            collection.objects.link(obj)
            result.append(obj)
    if not result:
        raise RuntimeError("No mesh objects from " + str(path))
    return collection, result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    a = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    src = Path(a.source)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((src / "editable_source_manifest.json").read_text())
    candidates = manifest["candidates"]
    assert len(candidates) == 2
    for item in candidates:
        assert sha(src / item["blend"]) == item["blend_sha256"]
        assert item["G1"] == "BLOCKED"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.16, 0.16, 0.16)
    scene["official_world_metric"] = "UNAPPROVED"
    scene["official_placement"] = "NOT_RUN"
    scene["art_status"] = "EXPLORATORY_CC0_ROCK_ASSEMBLY_NOT_ADOPTED"
    scene["no_generated_terrain"] = True
    placements = []
    # Studio composition in dimensionless display units; never write back to official layout.
    targets = [(-0.68, 0.0, 0.0), (0.72, 0.10, -0.12)]
    scales = [1.35, 1.05]
    for i, item in enumerate(candidates):
        coll, meshes = append_source(src / item["blend"], "CC0_SOURCE_" + item["id"])
        root = bpy.data.objects.new("DISPLAY_ONLY_" + item["id"], None)
        coll.objects.link(root)
        lo, hi = bounds(meshes)
        center = (lo + hi) / 2
        extent = max((hi - lo).length, 0.00001)
        for obj in meshes:
            # Parent inverse keeps imported geometry and PBR nodes unchanged.
            world = obj.matrix_world.copy()
            obj.parent = root
            obj.matrix_parent_inverse.identity()
            obj.matrix_world = world
        root.scale = (scales[i] / extent,) * 3
        root.location = Vector(targets[i]) - (center * (scales[i] / extent))
        root.rotation_euler[2] = (0.12 if i == 0 else -0.36)
        placements.append({"id": item["id"], "source_blend_sha256": item["blend_sha256"],
                           "display_scale_only": scales[i] / extent,
                           "display_target_only": list(targets[i]),
                           "source_meshes": len(meshes)})
    # A neutral studio ground is a render aid, not terrain geometry.
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.72))
    ground = bpy.context.object
    ground.name = "STUDIO_GROUND_NOT_TERRAIN"
    mat = bpy.data.materials.new("Neutral studio ground")
    mat.diffuse_color = (0.18, 0.18, 0.18, 1)
    ground.data.materials.append(mat)
    for name, loc, energy, size in [
        ("Key", (-3, -4, 7), 950, 5),
        ("Fill", (4, -1, 4), 500, 4),
        ("Rim", (0, 4, 6), 1100, 3),
    ]:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        ob = bpy.data.objects.new(name, data)
        scene.collection.objects.link(ob)
        ob.location = loc
        ob.rotation_euler = (Vector((0, 0, 0)) - ob.location).to_track_quat("-Z", "Y").to_euler()
    camdata = bpy.data.cameras.new("Studio camera")
    cam = bpy.data.objects.new("Studio camera", camdata)
    scene.collection.objects.link(cam)
    scene.camera = cam
    camdata.type = "ORTHO"
    camdata.ortho_scale = 3.6
    views = {"front": (3, -5, 2.2), "side": (5, 0, 2.5), "elevated": (4, -4, 5)}
    for label, location in views.items():
        cam.location = location
        cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(out / (label + ".png"))
        bpy.ops.render.render(write_still=True)
    blend = out / "cc0_rock_art_study.blend"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    files = [blend] + [out / (label + ".png") for label in views]
    report = {"status": "EXPLORATORY_ONLY", "G1": "BLOCKED", "G2": "NOT_RUN",
              "G3": "PENDING_INDEPENDENT_REOPEN", "G4": "NOT_RUN",
              "no_cliff_geometry_created": True, "source_candidates": placements,
              "files": {p.name: sha(p) for p in files}}
    (out / "art_study_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print("LIND_ROCK_ART_STUDY_RENDERED", json.dumps(report), flush=True)

if __name__ == "__main__":
    main()
