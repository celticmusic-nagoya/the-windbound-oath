"""Read-only, face-ID-level junction self-contact audit for Blender 5.3.

Usage:
 blender -b --disable-autoexec --python-exit-code 1 --python \
   tools/production_qa/junction_contact_faces.py -- candidate.blend audit.json

This diagnostic does not modify or save the source .blend. It uses the same
BVHTree.overlap detector and x guard as sculpt_junction.py. An overlap is a
broad-phase triangle contact, NOT necessarily a confirmed geometric penetration.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

TARGET = "Cliff C8 B | joinable coastal segment"
GUARD = (-9.0, -4.9)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    world = [tuple(obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
    triangles = []
    records = []
    for tri in mesh.loop_triangles:
        ids = tuple(int(i) for i in tri.vertices)
        if min(world[i][0] for i in ids) >= GUARD[1] or max(world[i][0] for i in ids) <= GUARD[0]:
            continue
        records.append({"face_id": int(tri.polygon_index), "vertex_ids": ids})
        triangles.append(ids)
    if not triangles:
        raise ValueError("No triangles in guarded junction region")
    tree = BVHTree.FromPolygons(world, triangles, all_triangles=True)
    pairs = []
    adjacent_skipped = 0
    for i, j in sorted(set((min(a, b), max(a, b)) for a, b in tree.overlap(tree) if a != b)):
        left, right = records[i], records[j]
        if set(left["vertex_ids"]).intersection(right["vertex_ids"]):
            adjacent_skipped += 1
            continue
        vertices = sorted(set(left["vertex_ids"] + right["vertex_ids"]))
        xyz = [world[k] for k in vertices]
        pairs.append({
            "triangle_indices": [i, j],
            "face_ids": [left["face_id"], right["face_id"]],
            "vertex_ids": [list(left["vertex_ids"]), list(right["vertex_ids"])],
            "world_aabb": {
                "min": [min(v[axis] for v in xyz) for axis in range(3)],
                "max": [max(v[axis] for v in xyz) for axis in range(3)],
            },
            "contact_class": "BVH_OVERLAP_UNCONFIRMED",
        })
    return {
        "object": obj.name, "guard_x": list(GUARD),
        "mesh_vertices": len(mesh.vertices), "mesh_faces": len(mesh.polygons),
        "guarded_triangles": len(triangles),
        "adjacent_pairs_excluded": adjacent_skipped,
        "nonadjacent_bvh_pairs": len(pairs),
        "pairs": pairs,
        "limitations": [
            "BVH overlap is not an exact triangle-triangle penetration test",
            "Pairs sharing a vertex are excluded to match the original stop gate",
            "Containment and other scene objects are outside this local audit",
            "Triangle and face IDs refer to this saved candidate, not the C10 source",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-sha256", default=None)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source, output = args.source.resolve(), args.output.resolve()
    if bpy.app.version != (5, 3, 0):
        raise RuntimeError("Requires Blender 5.3.0 for comparable IDs and BVH behavior")
    if not source.is_file() or source == output:
        raise ValueError("Source must exist; output must be separate")
    original_hash = digest(source)
    if args.expected_sha256 and original_hash != args.expected_sha256.lower():
        raise ValueError("Candidate SHA-256 mismatch; refusing to inspect")
    bpy.ops.wm.open_mainfile(filepath=str(source))
    obj = bpy.data.objects.get(TARGET)
    if obj is None or obj.type != "MESH":
        raise ValueError("Expected carrier mesh not found")
    result = audit(obj)
    result.update({
        "source_sha256": original_hash,
        "runtime_blender": bpy.app.version_string,
        "G2": "NOT_RUN",
        "G3": "FAIL" if result["nonadjacent_bvh_pairs"] else "PARTIAL",
    })
    if digest(source) != original_hash:
        raise RuntimeError("Source changed during read-only audit")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("JUNCTION_FACE_AUDIT", result["nonadjacent_bvh_pairs"], str(output), flush=True)


if __name__ == "__main__":
    main()
