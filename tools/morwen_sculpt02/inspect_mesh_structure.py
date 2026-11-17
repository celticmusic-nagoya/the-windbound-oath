"""Read-only Blender structure audit for Morwen candidate files.

Usage:
 blender -b morwen_sculpt02_v02_UNAPPROVED.blend --python inspect_mesh_structure.py -- /tmp/morwen_mesh_audit.json
No file saving, scene edits, or mesh regeneration.
"""
import bpy
import hashlib
import json
import math
import os
import sys
from pathlib import Path

def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def mesh_record(obj):
    mesh = obj.data
    keys = mesh.shape_keys
    vertices = mesh.vertices
    polygons = mesh.polygons
    return {
        "name": obj.name,
        "mesh_name": mesh.name,
        "vertex_count": len(vertices),
        "edge_count": len(mesh.edges),
        "face_count": len(polygons),
        "triangle_count": sum(len(face.vertices) - 2 for face in polygons),
        "all_quad_faces": sum(len(face.vertices) == 4 for face in polygons),
        "ngon_faces": sum(len(face.vertices) > 4 for face in polygons),
        "uv_layers": [layer.name for layer in mesh.uv_layers],
        "shape_keys": [key.name for key in keys.key_blocks] if keys else [],
        "vertex_groups": [group.name for group in obj.vertex_groups],
        "modifiers": [{"name": mod.name, "type": mod.type} for mod in obj.modifiers],
        "visible_render": not obj.hide_render,
        "collection_names": sorted(c.name for c in obj.users_collection),
        "bounds_local": [
            [min(v.co[axis] for v in vertices), max(v.co[axis] for v in vertices)]
            if vertices else None for axis in range(3)
        ],
        "finite_coordinates": all(math.isfinite(value) for v in vertices for value in v.co),
        "mesh_fingerprint_sha256": hashlib.sha256(
            ("|".join(
                f"{v.co.x:.9g},{v.co.y:.9g},{v.co.z:.9g}" for v in vertices
            ) + "#" + "|".join(
                ",".join(str(i) for i in p.vertices) for p in polygons
            )).encode("utf-8")
        ).hexdigest(),
    }

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1:
        raise SystemExit("Expected exactly one output JSON path after --")
    source = Path(bpy.data.filepath)
    if not source.is_file():
        raise RuntimeError("Open an existing .blend first")
    meshes = sorted((mesh_record(obj) for obj in bpy.data.objects if obj.type == "MESH"), key=lambda x: x["name"])
    data = {
        "audit": "read_only_mesh_structure_v1",
        "source_path": str(source),
        "source_sha256": file_hash(source),
        "blender_version": bpy.app.version_string,
        "mesh_count": len(meshes),
        "armatures": [
            {"name": obj.name, "bones": [b.name for b in obj.data.bones]}
            for obj in bpy.data.objects if obj.type == "ARMATURE"
        ],
        "meshes": meshes,
    }
    target = Path(argv[0])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MORWEN_MESH_AUDIT_WRITTEN", target)
    print("SOURCE_SHA256", data["source_sha256"])
    print("MESHES", len(meshes))

if __name__ == "__main__":
    main()
