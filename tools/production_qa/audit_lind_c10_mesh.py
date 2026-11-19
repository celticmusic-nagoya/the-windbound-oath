"""Independent C10 mesh audit; does not change the .blend or claim artistic approval."""
import json
import sys
from pathlib import Path
import bpy
import bmesh

source = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
output = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
bpy.ops.wm.open_mainfile(filepath=str(source))
report = {"blender_version": bpy.app.version_string, "source": source.name,
          "gate": "G3_PARTIAL", "meshes": [], "failures": []}
for obj in bpy.data.objects:
    if obj.type != "MESH" or not obj.get("status", "").startswith("UNAPPROVED_C10"):
        continue
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        nonmanifold = sum(not e.is_manifold for e in bm.edges)
        boundary = sum(e.is_boundary for e in bm.edges)
        degenerate = sum(f.calc_area() < 1e-8 for f in bm.faces)
        row = {"object": obj.name, "vertices": len(bm.verts), "faces": len(bm.faces),
               "boundary_edges": boundary, "nonmanifold_edges": nonmanifold,
               "degenerate_faces": degenerate}
        report["meshes"].append(row)
        if nonmanifold or degenerate:
            report["failures"].append(row)
    finally:
        bm.free()
if len(report["meshes"]) != 4:
    report["failures"].append({"expected_C10_rock_meshes": 4, "found": len(report["meshes"])})
report["result"] = "FAIL" if report["failures"] else "PASS_TOPOLOGY_ONLY"
report["limitations"] = ["no self-intersection test", "no rock-carrier intersection test",
                         "no UV/PBR audit", "no artistic or canonical CG approval"]
output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print("C10_GEOMETRY_AUDIT=" + report["result"], flush=True)
if report["failures"]:
    raise SystemExit(2)
