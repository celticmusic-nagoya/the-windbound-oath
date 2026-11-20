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


def triangle_crossing(first, second, epsilon=1e-7):
    """Intersect the two triangle/plane sections in world units."""
    def sub(a, b):
        return tuple(x-y for x,y in zip(a,b))

    def dot(a, b):
        return sum(x*y for x,y in zip(a,b))

    def cross(a, b):
        x,y,z = a
        i,j,k = b
        return y*k-z*j, z*i-x*k, x*j-y*i

    def norm(vec):
        size = dot(vec,vec)**0.5
        return tuple(x/size for x in vec) if size else vec

    a = norm(cross(sub(first[1],first[0]), sub(first[2],first[0])))
    b = norm(cross(sub(second[1],second[0]), sub(second[2],second[0])))
    direction = cross(a,b)
    if dot(direction,direction) <= 1e-16:
        distance = abs(dot(sub(second[0],first[0]),a))
        if distance > epsilon:
            return {"kind":"DISJOINT_PARALLEL","plane_separation": distance}
        # Clip the projected triangle against the other triangle's edge half-planes.
        axes = [i for i in range(3) if i != max(range(3), key=lambda i: abs(a[i]))]
        project = lambda p: tuple(p[i] for i in axes)
        polygon, clip = list(map(project, first)), list(map(project, second))
        def side(p,q,r):
            return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
        winding = 1 if side(*clip) >= 0 else -1
        for u,v in zip(clip,clip[1:]+clip[:1]):
            edges = list(zip(polygon,polygon[1:]+polygon[:1]))
            polygon = []
            for p,q in edges:
                dp,dq = winding*side(u,v,p),winding*side(u,v,q)
                if dp >= 0:
                    polygon.append(p)
                if (dp < 0) != (dq < 0):
                    f = dp/(dp-dq)
                    polygon.append(tuple(x+f*(y-x) for x,y in zip(p,q)))
        area = abs(sum(p[0]*q[1]-q[0]*p[1]
                       for p,q in zip(polygon,polygon[1:]+polygon[:1])))*0.5
        return {"kind":"COPLANAR_OVERLAP" if area > epsilon**2 else "COPLANAR_TOUCH_OR_SEPARATION",
                "projected_area":area,"plane_separation":distance}
    direction = norm(direction)
    def section(triangle, origin, normal):
        heights = [dot(sub(p,origin),normal) for p in triangle]
        points = [dot(p,direction) for p,h in zip(triangle,heights) if abs(h) <= epsilon]
        for i,j in ((0,1),(1,2),(2,0)):
            if heights[i]*heights[j] < 0:
                t = heights[i]/(heights[i]-heights[j])
                points.append(dot(tuple(x+t*(y-x) for x,y in zip(triangle[i],triangle[j])),direction))
        return (min(points),max(points)) if points else None, heights
    u, du = section(first,second[0],b)
    v, dv = section(second,first[0],a)
    length = min(u[1],v[1])-max(u[0],v[0]) if u and v else None
    strict = all(min(values) < -epsilon and max(values) > epsilon for values in (du,dv))
    kind = "CROSSING" if length is not None and length > epsilon and strict else (
        "TOUCH" if length is not None and length >= -epsilon else "DISJOINT")
    return {"kind":kind,"signed_interval_overlap":length,"signed_plane_distances":[du,dv],"epsilon":epsilon}


def audit(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    world = [tuple(obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
    triangles = []
    records = []
    for triangle_id, tri in enumerate(mesh.loop_triangles):
        ids = tuple(int(i) for i in tri.vertices)
        if min(world[i][0] for i in ids) >= GUARD[1] or max(world[i][0] for i in ids) <= GUARD[0]:
            continue
        records.append({"face_id": int(tri.polygon_index), "triangle_id": triangle_id, "vertex_ids": ids})
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
            "triangles": [dict(row, local_xyz=[list(mesh.vertices[k].co) for k in row["vertex_ids"]], world_xyz=[world[k] for k in row["vertex_ids"]], normal=list(mesh.polygons[row["face_id"]].normal), material_slot=mesh.polygons[row["face_id"]].material_index, loops=[{"id": k, "vertex": mesh.loops[k].vertex_index, "uv": {layer.name: list(layer.uv[k].vector) for layer in mesh.uv_layers}} for k in mesh.polygons[row["face_id"]].loop_indices]) for row in (left, right)],
            "vertex_ids": [list(left["vertex_ids"]), list(right["vertex_ids"])],
            "world_aabb": {
                "min": [min(v[axis] for v in xyz) for axis in range(3)],
                "max": [max(v[axis] for v in xyz) for axis in range(3)],
            },
            "intersection": triangle_crossing([world[k] for k in left["vertex_ids"]],
                                             [world[k] for k in right["vertex_ids"]]),
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
