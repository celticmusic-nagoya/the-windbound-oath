"""Read-only Blender forensic audit of a previously produced candidate .blend.

Run only in a trusted Blender 4.3.2 environment; no autoexec and no saves.
Outputs JSON to stdout; exits nonzero on a failed structural check.
This is NOT an art-quality or canon approval.
"""
import argparse
import json
import sys

import bpy


def inspect(expected_min_meshes, expected_min_triangles):
    scene = bpy.context.scene
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    triangles = sum(sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
                    for obj in meshes)
    missing_images = []
    for img in bpy.data.images:
        if img.source == "FILE" and img.filepath and not img.packed_file:
            try:
                if not img.has_data:
                    missing_images.append(img.name)
            except (RuntimeError, ValueError):
                missing_images.append(img.name)
    nonmanifold = []
    for obj in meshes:
        edges = obj.data.edges
        if not edges:
            nonmanifold.append(obj.name + ":no_edges")
    errors = []
    if len(meshes) < expected_min_meshes:
        errors.append("mesh_count_below_expected")
    if triangles < expected_min_triangles:
        errors.append("triangle_count_below_expected")
    if nonmanifold:
        errors.append("mesh_without_edges")
    return {
        "status": "FAIL" if errors else "PASS",
        "blender_version": bpy.app.version_string,
        "scene": scene.name,
        "mesh_count": len(meshes),
        "triangles": triangles,
        "missing_image_data_candidates": missing_images,
        "errors": errors,
        "scope": "read_only_reopen_and_basic_mesh_inventory_only",
        "art_qa": "NOT_RUN",
        "runtime_qa": "NOT_RUN",
    }


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-meshes", type=int, default=1)
    parser.add_argument("--min-triangles", type=int, default=1)
    parser.add_argument("--report", required=True)
    parsed = parser.parse_args(args)
    result = inspect(parsed.min_meshes, parsed.min_triangles)
    with open(parsed.report, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
