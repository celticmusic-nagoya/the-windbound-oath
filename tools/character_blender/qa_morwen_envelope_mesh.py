"""Independent geometric QA for a NON-PRODUCTION silhouette envelope.

Checks manifold topology, connected components, finite coordinates and source
provenance. This is not an artistic or anatomical validation.
Usage: python tools/character_blender/qa_morwen_envelope_mesh.py -- INPUT.blend OUTPUT.json
"""
import bpy
import hashlib
import json
import math
import pathlib
import sys
from collections import Counter, deque

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 2:
    raise SystemExit("usage: -- INPUT.blend OUTPUT.json")
src, dest = map(lambda p: pathlib.Path(p).resolve(), args)
if not src.is_file() or src.suffix != ".blend" or dest.suffix != ".json":
    raise SystemExit("BLOCKED missing input blend or invalid report")
bpy.ops.wm.open_mainfile(filepath=str(src))
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
errors = []
if len(meshes) != 1 or meshes[0].name != "QA_ONLY_SILHOUETTE_ENVELOPE_NOT_CHARACTER":
    errors.append("expected exactly one named QA envelope mesh")
if bpy.context.scene.get("asset_status") != "MEASUREMENT_ENVELOPE_ONLY":
    errors.append("scene status must remain non-production")
if not errors:
    obj = meshes[0]
    mesh = obj.data
    verts = [tuple(v.co) for v in mesh.vertices]
    if len(verts) < 100 or len(mesh.polygons) < 100:
        errors.append("insufficient geometry")
    if not all(math.isfinite(v) for xyz in verts for v in xyz):
        errors.append("non-finite vertex coordinates")
    edge_faces = Counter()
    graph = [set() for _ in verts]
    for poly in mesh.polygons:
        ids = list(poly.vertices)
        if len(ids) < 3:
            errors.append("degenerate face")
        for i, a in enumerate(ids):
            b = ids[(i + 1) % len(ids)]
            if a == b:
                errors.append("zero-length topological edge")
            edge_faces[tuple(sorted((a, b)))] += 1
            graph[a].add(b)
            graph[b].add(a)
    bad_edges = sum(n != 2 for n in edge_faces.values())
    if bad_edges:
        errors.append("nonmanifold edges: " + str(bad_edges))
    visited = set()
    components = 0
    for i in range(len(verts)):
        if i in visited:
            continue
        components += 1
        queue = deque([i])
        visited.add(i)
        while queue:
            for neighbor in graph[queue.popleft()]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
    if components != 1:
        errors.append("disconnected components: " + str(components))
    dimensions = [round(float(x), 6) for x in obj.dimensions]
    if any(x <= 0 for x in dimensions):
        errors.append("invalid mesh dimensions")
else:
    mesh = None
    bad_edges = None
    components = None
    dimensions = None
report = {
    "status": "PASS_GEOMETRY_TOPOLOGY_ONLY" if not errors else "FAIL_GEOMETRY_TOPOLOGY",
    "errors": errors,
    "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
    "mesh_vertices": len(mesh.vertices) if mesh else 0,
    "mesh_faces": len(mesh.polygons) if mesh else 0,
    "nonmanifold_edges": bad_edges,
    "connected_components": components,
    "dimensions_normalized": dimensions,
    "G1": "BLOCKED", "G2": "NOT_RUN",
    "G3": "TOPOLOGY_ONLY" if not errors else "FAIL",
    "G4": "NOT_RUN",
    "production_asset": False,
}
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(report, indent=2))
print(json.dumps(report))
if errors:
    raise SystemExit(1)
