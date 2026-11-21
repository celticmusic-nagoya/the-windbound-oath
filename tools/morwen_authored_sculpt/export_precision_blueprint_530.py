"""Export auditable numeric geometry from the verified Blender Studio source candidate.
Blender 5.3 -b source.blend --python export_precision_blueprint_530.py -- OUTPUT_DIR
Candidate-only. Does not modify the source or canonical Morwen assets.
"""
import bpy
import gzip
import hashlib
import json
import sys
from pathlib import Path

out = Path(sys.argv[sys.argv.index("--") + 1])
out.mkdir(parents=True, exist_ok=True)
names = ("GEO-head_stylized", "GEO-body_female_stylized")
manifest = {
    "schema_version": "0.1",
    "asset_id": "MORWEN_BASE_SOURCE_BLUEPRINT_CANDIDATE",
    "candidate_status": "NOT_ADOPTED_NOT_MORWEN_SCULPT",
    "blender": bpy.app.version_string,
    "coordinate_contract": {"space": "OBJECT_LOCAL", "units": "SOURCE_BLEND_NATIVE_UNVERIFIED", "transform": "matrix_world_stored_per_part"},
    "source_archive_sha256": "811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515",
    "mesh_parts": [],
    "qa": {"G1": "PARTIAL", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"},
}
for name in names:
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != "MESH":
        raise RuntimeError("SOURCE_OBJECT_MISSING:" + name)
    mesh = ob.data
    mesh.calc_loop_triangles()
    verts = [[float(c) for c in v.co] for v in mesh.vertices]
    edges = [[int(i) for i in e.vertices] for e in mesh.edges]
    faces = [[int(i) for i in p.vertices] for p in mesh.polygons]
    normals = [[float(c) for c in v.normal] for v in mesh.vertices]
    polygon_materials = [int(p.material_index) for p in mesh.polygons]
    uv_layers = {}
    for layer in mesh.uv_layers:
        uv_layers[layer.name] = [[float(x) for x in item.uv] for item in layer.data]
    payload = {
        "object": name, "space": "OBJECT_LOCAL",
        "vertices": verts, "edges": edges, "faces": faces,
        "vertex_normals": normals, "polygon_material_indices": polygon_materials,
        "uv_layers_by_corner": uv_layers,
        "matrix_world_rows": [[float(ob.matrix_world[r][c]) for c in range(4)] for r in range(4)],
        "material_names": [mat.name if mat else None for mat in mesh.materials],
    }
    slug = "head" if "head" in name else "body_female"
    raw = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
    filename = slug + "_mesh_geometry.json.gz"
    with gzip.open(out / filename, "wb", compresslevel=6) as fp:
        fp.write(raw)
    with gzip.open(out / filename, "rb") as fp:
        restored = json.loads(fp.read())
    assert len(restored["vertices"]) == len(mesh.vertices)
    assert len(restored["edges"]) == len(mesh.edges)
    assert len(restored["faces"]) == len(mesh.polygons)
    assert restored["faces"] == faces
    assert restored["vertices"] == verts
    assert all(len(coords) == len(mesh.loops) for coords in restored["uv_layers_by_corner"].values())
    manifest["mesh_parts"].append({
        "object": name, "file": filename,
        "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        "vertices": len(verts), "edges": len(edges), "faces": len(faces),
        "loops": len(mesh.loops), "uv_layers": list(uv_layers),
        "dimensions": [float(x) for x in ob.dimensions],
        "bounds_local": [[float(x) for x in ob.bound_box[i]] for i in range(8)],
        "status": "NUMERIC_ROUNDTRIP_PASS_SOURCE_CANDIDATE_ONLY",
    })
(out / "blueprint.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("MORWEN_PRECISION_BLUEPRINT_NUMERIC_ROUNDTRIP_PASS", len(manifest["mesh_parts"]))
