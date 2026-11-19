"""Reopen swept cliff C and verify the body, outputs and reference provenance."""
import argparse
import hashlib
import json
from pathlib import Path

import bpy
import bmesh
from mathutils.bvhtree import BVHTree

from build_windwaiting_cliff_C_swept import BODY, CG_SHA, make_section, SECTIONS


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connected_components(surface):
    remaining = set(surface.verts)
    components = 0
    while remaining:
        components += 1
        queue = [remaining.pop()]
        while queue:
            vertex = queue.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
    return components


def inspect_mesh(mesh):
    surface = bmesh.new()
    try:
        surface.from_mesh(mesh)
        counts = {
            "vertices": len(surface.verts),
            "edges": len(surface.edges),
            "faces": len(surface.faces),
            "connected_components": connected_components(surface),
            "boundary_edges": sum(edge.is_boundary for edge in surface.edges),
            "nonmanifold_edges": sum(not edge.is_manifold for edge in surface.edges),
            "inconsistent_edges": sum(not edge.is_contiguous for edge in surface.edges),
            "zero_area_faces": sum(face.calc_area() < 1e-12 for face in surface.faces),
            "signed_volume": surface.calc_volume(signed=True),
        }
    finally:
        surface.free()

    mesh.calc_loop_triangles()
    triangles = [tuple(tri.vertices) for tri in mesh.loop_triangles]
    triangle_vertices = [set(tri) for tri in triangles]
    vertices = [vert.co for vert in mesh.vertices]
    bvh = BVHTree.FromPolygons(vertices, triangles, all_triangles=True)
    counts["triangles"] = len(triangles)
    counts["intersecting_nonadjacent_triangle_pairs"] = sum(
        a < b and triangle_vertices[a].isdisjoint(triangle_vertices[b])
        for a, b in bvh.overlap(bvh)
    )
    counts["bounds"] = {
        "min": [min(v[axis] for v in vertices) for axis in range(3)],
        "max": [max(v[axis] for v in vertices) for axis in range(3)],
    }
    return counts


def check_outputs(root):
    files = {}
    for name in ("windwaiting_cliff_C_swept_UNAPPROVED.blend", "front.png", "left.png", "right.png",
                 "elevated.png", "comparison.png"):
        path = root / name
        assert path.stat().st_size > 0, path
        entry = {"bytes": path.stat().st_size, "sha256": digest(path)}
        if path.suffix == ".png":
            image = bpy.data.images.load(str(path.resolve()), check_existing=False)
            try:
                width, height = image.size
                assert len(image.pixels) == width * height * 4
                if name != "comparison.png":
                    assert (width, height) == (1200, 760), (name, width, height)
                    center = ((height // 2) * width + width // 2) * 4
                    assert image.pixels[0:4] != image.pixels[center:center + 4]
                entry["size"] = [width, height]
            finally:
                bpy.data.images.remove(image)
        files[name] = entry
    return files


def main():
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--out", type=Path, required=True)
    arguments.add_argument("--reference", type=Path, required=True)
    args = arguments.parse_args()
    assert tuple(bpy.app.version) == (5, 2, 4)
    assert digest(args.reference) == CG_SHA
    root = args.out.resolve()
    blend = root / "windwaiting_cliff_C_swept_UNAPPROVED.blend"
    assert bpy.ops.wm.open_mainfile(filepath=str(blend), use_scripts=False) == {"FINISHED"}
    scene = bpy.context.scene
    assert scene["coordinate_space"] == "asset-local-provisional"
    assert scene["unit_scale_status"] == "UNAPPROVED"
    source = Path(__file__).with_name("build_windwaiting_cliff_C_swept.py")
    assert scene["producer_script_sha256"] == digest(source)
    obj = bpy.data.objects[BODY]
    assert len(obj.modifiers) == 0 and obj.type == "MESH"
    mesh = inspect_mesh(obj.data)
    separate = {
        name: len(bpy.data.collections[name].objects)
        for name in ("02 | Detached sea stacks", "03 | Talus modules")
    }
    assert all(separate.values())
    sections = [make_section(row[0], 1) for row in SECTIONS]
    steepest_region = sections[7]
    crest, shoulder, notch = steepest_region[9], steepest_region[19], steepest_region[24]
    report = {
        "blender": bpy.app.version_string,
        "runtime": "PyPI bpy wheel, CPU Cycles",
        "coordinate_space": scene["coordinate_space"],
        "unit_scale_status": scene["unit_scale_status"],
        "source_cg_sha256": CG_SHA,
        "producer_script_sha256": digest(source),
        "mesh": mesh,
        "local_cross_section": {
            "crest": list(crest), "projecting_shoulder": list(shoulder), "recess_below": list(notch),
        },
        "separate_module_counts": separate,
        "files": check_outputs(root),
        "reopen": "PASS",
        "png_decode": "PASS",
        "G1": "BLOCKED",
        "G2": "NOT_RUN",
        "G4": "NOT_RUN",
    }
    for key in ("boundary_edges", "nonmanifold_edges", "inconsistent_edges", "zero_area_faces",
                "intersecting_nonadjacent_triangle_pairs"):
        assert mesh[key] == 0, (key, mesh[key])
    assert mesh["connected_components"] == 1 and mesh["signed_volume"] > 0
    assert shoulder[0] < notch[0] and shoulder[1] > notch[1]
    report["G3_structural_subset"] = "PASS"
    report["G3"] = "NOT_RUN"
    (root / "qa.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
