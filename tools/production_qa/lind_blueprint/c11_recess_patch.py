"""C11 bounded fracture-wall patch experiment; never changes its input .blend.

Run with Blender 5.3.0:
 blender -b --factory-startup --python c11_recess_patch.py -- INPUT.blend OUT_DIR

The script deliberately refuses to save an unsafe or ambiguous patch. All
coordinates are provisional C10 asset-local units; no formal adoption implied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

SOURCE_SHA = "0b6b0f3f6e8e270594cdac5fc81008ffe5210b7e98de352d826360dfd6676508"
TARGET = "Cliff C8 B | joinable coastal segment"
SEAM_X = -5.95
HALF_WIDTH = 0.46
BOTTOM_Z, TOP_Z = 0.45, 4.25
DEPTH = 0.42


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def topology(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return {
            "vertices": len(bm.verts), "faces": len(bm.faces),
            "boundary_edges": sum(e.is_boundary for e in bm.edges),
            "nonmanifold_edges": sum(not e.is_manifold for e in bm.edges),
        }
    finally:
        bm.free()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source, output = args.source.resolve(), args.output.resolve()
    if bpy.app.version != (5, 3, 0):
        raise RuntimeError("Requires Blender 5.3.0")
    if not source.is_file() or sha(source) != SOURCE_SHA:
        raise RuntimeError("C10 hero input SHA mismatch; STOP, do not guess")
    if output == source.parent or source in output.parents:
        raise RuntimeError("Output must not overwrite or nest within source")
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    candidates = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name == TARGET]
    if len(candidates) != 1:
        raise RuntimeError("Expected exactly one verified carrier; available meshes: " + repr([o.name for o in bpy.data.objects if o.type == "MESH"]))
    obj = candidates[0]
    before = topology(obj)
    original = [tuple(v.co) for v in obj.data.vertices]
    original_count = len(original)
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        # Only fully interior faces qualify. The selection is intentionally
        # narrow to preserve a complete, fixed perimeter collar.
        region = []
        for face in bm.faces:
            if all(abs(v.co.x - SEAM_X) < HALF_WIDTH and
                   BOTTOM_Z < v.co.z < TOP_Z for v in face.verts):
                region.append(face)
        if len(region) < 8:
            raise RuntimeError(f"Insufficient local faces ({len(region)}); STOP")
        # The original coordinate window intersects multiple disconnected islands.
        # Select the single largest connected component deterministically; reject
        # tiny components rather than silently modifying unrelated coastal faces.
        pending = set(region)
        components = []
        while pending:
            seed = min(pending, key=lambda face: face.index)
            pending.remove(seed)
            stack, component = [seed], {seed}
            while stack:
                face = stack.pop()
                for edge in face.edges:
                    for neighbor in edge.link_faces:
                        if neighbor in pending:
                            pending.remove(neighbor)
                            component.add(neighbor)
                            stack.append(neighbor)
            components.append(component)
        components.sort(key=lambda group: (-len(group), min(f.index for f in group)))
        region = sorted(components[0], key=lambda face: face.index)
        if len(region) < 8:
            raise RuntimeError("Largest connected island too small; STOP")
        face_set = set(region)
        perimeter_edges = [edge for face in region for edge in face.edges
                           if sum(link in face_set for link in edge.link_faces) == 1]
        perimeter_edges = list(set(perimeter_edges))
        boundary = {v.index for edge in perimeter_edges for v in edge.verts}
        if len(boundary) < 6:
            raise RuntimeError("Patch boundary invalid; STOP")
        # Require exactly one closed perimeter: every perimeter vertex has degree 2.
        degree = {}
        for edge in perimeter_edges:
            for vertex in edge.verts:
                degree[vertex.index] = degree.get(vertex.index, 0) + 1
        if any(count != 2 for count in degree.values()):
            raise RuntimeError("Patch perimeter not a closed simple loop; STOP")
        perimeter_neighbors = {}
        for edge in perimeter_edges:
            a, b = [v.index for v in edge.verts]
            perimeter_neighbors.setdefault(a, set()).add(b)
            perimeter_neighbors.setdefault(b, set()).add(a)
        seen, stack = set(), [min(boundary)]
        while stack:
            current = stack.pop()
            if current not in seen:
                seen.add(current)
                stack.extend(perimeter_neighbors[current] - seen)
        if seen != boundary:
            raise RuntimeError("Multiple perimeter loops; STOP")
        # Persist a deterministic geometry diagnosis before any destructive edit.
        # A single selected island does not prove that inset will create a
        # cavity: diagnose interior vertices, face sizes and perimeter first.
        interior_original = {v.index for face in region for v in face.verts} - boundary
        diagnostic = {
            "stage": "BEFORE_INSET", "selected_faces": len(region),
            "component_sizes": [len(group) for group in components],
            "perimeter_edges": len(perimeter_edges),
            "perimeter_vertices": len(boundary),
            "interior_original_vertices": len(interior_original),
            "face_vertex_counts": {
                str(n): sum(len(face.verts) == n for face in region)
                for n in sorted({len(face.verts) for face in region})
            },
            "source_sha256": SOURCE_SHA,
            "G2": "NOT_RUN", "G3": "NOT_RUN",
        }
        (output / "c11_geometry_diagnostic.json").write_text(
            json.dumps(diagnostic, indent=2), encoding="utf-8")
        if len(region) < 16 or len(interior_original) < 3:
            raise RuntimeError("Patch lacks adequate interior topology; diagnose before another inset")
        # Method B: replace the selected face island with a recessed duplicate.
        # Original vertices remain in place; only faces in the bounded island
        # are replaced. A duplicate of each island vertex forms the new floor,
        # and an explicit quad strip joins the old perimeter to the new rim.
        # No inset_region operation is used.
        source_faces = [(face, [v for v in face.verts]) for face in region]
        source_vertices = {v for _, vertices in source_faces for v in vertices}
        duplicate = {v: bm.verts.new(v.co.copy()) for v in source_vertices}
        for v, copy in duplicate.items():
            height = max(0.0, min(1.0, (v.co.z - BOTTOM_Z) / (TOP_Z - BOTTOM_Z)))
            # The rim and floor both recede; a height-dependent, asymmetric
            # setback creates a non-planar wall rather than an exterior ridge.
            skew = 0.72 + 0.28 * height + 0.14 * (v.co.x - SEAM_X) / HALF_WIDTH
            copy.co.y += DEPTH * max(0.4, skew)
        # Preserve face winding and all nonselected face connections.
        for face, vertices in source_faces:
            bm.faces.new([duplicate[v] for v in vertices])
        # Each perimeter edge belongs to exactly one selected face.
        # Follow that face's winding to make a consistent bridge strip.
        for edge in perimeter_edges:
            selected = [face for face in edge.link_faces if face in face_set]
            if len(selected) != 1:
                raise RuntimeError("Ambiguous patch edge adjacency; STOP")
            winding = list(selected[0].verts)
            pair = None
            for i, vertex in enumerate(winding):
                nxt = winding[(i + 1) % len(winding)]
                if vertex in edge.verts and nxt in edge.verts:
                    pair = (vertex, nxt)
                    break
            if pair is None:
                raise RuntimeError("Cannot orient perimeter edge; STOP")
            a, b = pair
            bm.faces.new((a, b, duplicate[b], duplicate[a]))
        bmesh.ops.delete(bm, geom=region, context="FACES_ONLY")
        diagnostic["decision"] = "BOUNDARY_LOCKED_FACE_REPLACEMENT"
        diagnostic["replacement_faces"] = len(source_faces)
        diagnostic["bridge_faces"] = len(perimeter_edges)
        diagnostic["new_vertices"] = len(duplicate)
        (output / "c11_geometry_diagnostic.json").write_text(
            json.dumps(diagnostic, indent=2), encoding="utf-8")
        bm.normal_update()
        bm.to_mesh(obj.data)
        obj.data.update()
    finally:
        bm.free()
    after = topology(obj)
    if len(obj.data.vertices) < original_count:
        raise RuntimeError("Original vertex count decreased; STOP")
    moved_original = [
        i for i, (v, old) in enumerate(zip(obj.data.vertices, original))
        if tuple(v.co) != old
    ]
    report = {
        "status": "CANDIDATE_ONLY", "source_sha256": SOURCE_SHA,
        "before": before, "after": after,
        "selected_face_count": len(region),
        "discovered_component_sizes": [len(group) for group in components],
        "boundary_original_vertices": len(boundary),
        "changed_original_vertex_ids": moved_original[:40],
        "changed_original_vertex_count": len(moved_original),
        "original_vertex_count": original_count,
        "final_vertex_count": len(obj.data.vertices),
        "G1": "BLOCKED", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN",
    }
    (output / "c11_patch_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    # Refuse save until full original vertex lock and topology checks pass.
    if moved_original or after["boundary_edges"] or after["nonmanifold_edges"]:
        raise RuntimeError("C11 topology/boundary gate failed; JSON saved, blend rejected")
    bpy.context.scene["candidate"] = "C11_RECESS_PATCH_UNAPPROVED"
    destination = output / "c11_recess_patch_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
    print("C11_CANDIDATE_SAVED", sha(destination), flush=True)


if __name__ == "__main__":
    main()
