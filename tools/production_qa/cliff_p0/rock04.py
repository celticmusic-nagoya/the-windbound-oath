"""Measured, bounded winding and rear-cap correction on an isolated Blender copy."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils.bvhtree import BVHTree


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def protected(obj):
    digest = hashlib.sha256()
    for item in sorted(bpy.context.scene.objects, key=lambda value: value.name):
        digest.update(repr((item.name, tuple(tuple(row) for row in item.matrix_world),
                            item.hide_render, item.type)).encode())
        if item == obj or item.type != "MESH":
            continue
        mesh = item.data
        records = (tuple(tuple(v.co) for v in mesh.vertices),
                   tuple(tuple(p.vertices) for p in mesh.polygons),
                   tuple(p.material_index for p in mesh.polygons),
                   tuple(tuple(n.vector) for n in mesh.corner_normals),
                   tuple(tuple(tuple(uv.uv) for uv in layer.data) for layer in mesh.uv_layers))
        digest.update(repr(records).encode())
    return digest.hexdigest()


def coordinates(mesh):
    return [tuple(vertex.co) for vertex in mesh.vertices]


def measure(obj):
    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        result = dict(vertices=len(bm.verts), faces=len(bm.faces),
                      winding=sum(not edge.is_contiguous for edge in bm.edges),
                      boundary=sum(edge.is_boundary for edge in bm.edges),
                      nonmanifold=sum(not edge.is_manifold for edge in bm.edges),
                      signed_volume_bu3=bm.calc_volume(signed=True))
    finally:
        bm.free()
    points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    tris = [tuple(tri.vertices) for tri in mesh.loop_triangles]
    tree = BVHTree.FromPolygons(points, tris, all_triangles=True)
    result["self_pairs"] = sum(i < j and set(tris[i]).isdisjoint(tris[j])
                               for i, j in tree.overlap(tree))
    result["min_triangle_area_bu2"] = min(
        ((points[j] - points[i]).cross(points[k] - points[i])).length / 2
        for i, j, k in tris)
    for name in ("C10 large rock 03", "Cliff C8 B | joinable coastal segment"):
        other = bpy.data.objects[name]
        other.data.calc_loop_triangles()
        other_tree = BVHTree.FromPolygons(
            [other.matrix_world @ v.co for v in other.data.vertices],
            [tuple(t.vertices) for t in other.data.loop_triangles], all_triangles=True)
        result[name + " overlap pairs"] = len(tree.overlap(other_tree))
    return result


def correct(obj, design, stage):
    mesh = obj.data
    assert not mesh.uv_layers and not mesh.has_custom_normals
    old_faces = Counter((frozenset(poly.vertices), poly.material_index) for poly in mesh.polygons)
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        if stage == "winding":
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        else:
            bm.faces.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            cap = bm.faces[1]
            assert [v.index for v in cap.verts] == design["cap_vertex_ids"]
            material, smooth = cap.material_index, cap.smooth
            bmesh.ops.delete(bm, geom=[cap], context="FACES_ONLY")
            for triangle in design["cap_triangles"]:
                face = bm.faces.new(tuple(bm.verts[i] for i in triangle))
                face.material_index = material
                face.smooth = smooth
                old_faces[frozenset(triangle), material] += 1
            old_faces[frozenset(design["cap_vertex_ids"]), material] -= 1
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    assert Counter((frozenset(poly.vertices), poly.material_index)
                   for poly in mesh.polygons) == +old_faces


def main():
    mode, stage, source, expected, design_path, output = sys.argv[sys.argv.index("--") + 1:]
    source, design_path, output = map(Path, (source, design_path, output))
    design = json.loads(design_path.read_text())
    assert bpy.app.version == (5, 3, 0)
    assert sha(source) == expected
    bpy.ops.wm.open_mainfile(filepath=str(source))
    obj = bpy.data.objects[design["object"]]
    if mode == "inspect":
        result = dict(metrics=measure(obj), native_sha256=expected,
                      protected_sha256=protected(obj))
    else:
        before = measure(obj)
        locked = protected(obj)
        verts = coordinates(obj.data)
        if stage == "winding":
            assert expected == design["source_sha256"]
            assert all(before[key] == val for key, val in design["baseline"].items())
        correct(obj, design, stage)
        after = measure(obj)
        assert coordinates(obj.data) == verts
        assert protected(obj) == locked
        assert after["winding"] == after["boundary"] == after["nonmanifold"] == 0
        assert after["signed_volume_bu3"] > 0
        assert after["vertices"] == design["target"]["vertices"]
        assert after["min_triangle_area_bu2"] >= design["target"]["min_triangle_area_bu2"]
        assert after["self_pairs"] == (before["self_pairs"] if stage == "winding" else 0)
        assert after["faces"] == (before["faces"] if stage == "winding" else design["target"]["faces"])
        native = output.with_suffix(".blend")
        assert not native.exists()
        bpy.ops.wm.save_as_mainfile(filepath=str(native))
        result = dict(stage=stage, source_sha256=expected, native_sha256=sha(native),
                      design_sha256=sha(design_path), protected_sha256=locked,
                      vertex_delta_max_bu=0.0, before=before, metrics=after)
    output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
