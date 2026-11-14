"""Read-only EYELID-05 lid margin inspection in Blender.

Run: EYELID_06_DIAGNOSTIC_JSON=/tmp/lid06_diagnostic.json \
 blender -b MORWEN_EYELID_05_CANDIDATE.blend --python inspect_lid_geometry_06.py

Does not modify or save a .blend. Extracts margin topology and world coordinates
for later correspondence/QA. Output is diagnostic, not a production asset.
"""
import hashlib
import json
import os
from pathlib import Path

import bpy


def inspect():
    blend = Path(bpy.data.filepath)
    if not blend.is_file():
        raise RuntimeError("EYELID-05 saved .blend is required")
    face = bpy.data.objects["Face"]
    mesh = face.data
    attr = mesh.attributes.get("elm_patch")
    if attr is None:
        raise RuntimeError("Missing elm_patch attribute")
    tags = [int(x.value) for x in attr.data]
    if not mesh.shape_keys:
        raise RuntimeError("Missing shape keys")
    keys = list(mesh.shape_keys.key_blocks)
    expected = [f"target_{i}" for i in range(56)]
    if [k.name for k in keys[1:57]] != expected:
        raise RuntimeError("56 protected keys mismatch")
    edge_faces = {}
    for p in mesh.polygons:
        for edge in p.edge_keys:
            edge_faces.setdefault(tuple(sorted(edge)), []).append(p.index)
    sides = {}
    for side, pid in (("R", 1), ("L", 2)):
        seam = set()
        edges = []
        for edge, adjacent in edge_faces.items():
            a, b = edge
            if tags[a] != pid or tags[b] != pid:
                continue
            has_wall = any(any(tags[v] == pid+10 for v in mesh.polygons[i].vertices) for i in adjacent)
            has_lid = any(all(tags[v] == pid for v in mesh.polygons[i].vertices) for i in adjacent)
            if has_wall and has_lid:
                seam.update(edge)
                edges.append(list(edge))
        if len(seam) < 8:
            raise RuntimeError(f"{side}: insufficient margin vertices ({len(seam)})")
        degree = {v: 0 for v in seam}
        for a,b in edges:
            degree[a] += 1
            degree[b] += 1
        # Open canthus-to-canthus chains are expected; a single degree-2 ring is also possible.
        if any(d not in (1,2) for d in degree.values()):
            raise RuntimeError(f"{side}: non-chain margin topology")
        world = face.matrix_world
        coords = {str(i): [round(float(q), 8) for q in (world @ mesh.vertices[i].co)] for i in sorted(seam)}
        sides[side] = {"margin_vertices": len(seam), "margin_edges": len(edges),
                       "degree_one": sum(d==1 for d in degree.values()),
                       "degree_two": sum(d==2 for d in degree.values()),
                       "edges": sorted(edges), "world_xyz_m": coords}
    return {"status": "DIAGNOSTIC_ONLY_NOT_ART_APPROVAL",
            "input_blend": blend.name,
            "input_sha256": hashlib.sha256(blend.read_bytes()).hexdigest(),
            "blender_version": bpy.app.version_string,
            "shape_keys": [k.name for k in keys],
            "sides": sides, "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"}


def main():
    dest = Path(os.environ["EYELID_06_DIAGNOSTIC_JSON"]).resolve()
    if dest.exists():
        raise RuntimeError("Refusing to overwrite diagnostic output")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(inspect(), indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
