"""Reopen C9 mesh evidence and run the inherited seam and structural tests."""
import json
import sys
from pathlib import Path

import bpy
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "tools/map_blender/lind"))
from inspect_windwaiting_cliff_C8 import digest, headland_visibility, inspect_mesh, variants_qa

path = Path(sys.argv[1])
bpy.ops.wm.open_mainfile(filepath=str(path))
scene = bpy.context.scene
tiles, seams = variants_qa()
body = next(obj for obj in bpy.data.objects if obj.get("variant") == "B")
visibility = headland_visibility(scene, body)
debris = {}
for obj in bpy.data.objects:
    if not obj.name.startswith("C9 Scar"):
        continue
    assert obj.type == "MESH"
    metrics = inspect_mesh(obj.data)
    assert metrics["boundary_edges"] == metrics["nonmanifold_edges"] == metrics["intersecting_nonadjacent_triangle_pairs"] == 0
    z = [(obj.matrix_world @ vertex.co).z for vertex in obj.data.vertices]
    debris[obj.name] = {"min_z": min(z), "max_z": max(z), "scar_x": obj["collapse_site_x"]}
    assert min(z) < 0 < max(z)
files = {}
for candidate in sorted(path.parent.iterdir()):
    if candidate.suffix == ".png":
        with Image.open(candidate) as image:
            image.load()
            files[candidate.name] = {"size": image.size, "sha256": digest(candidate)}
    if candidate.suffix == ".blend":
        files[candidate.name] = {"sha256": digest(candidate)}
report = {
    "blender": bpy.app.version_string, "reopen": "PASS", "tiles": tiles, "seams": seams,
    "visibility": visibility, "debris": debris, "files": files,
    "G1": "BLOCKED", "G2": "NOT_RUN", "G3_structural_subset": "PASS", "G4": "NOT_RUN",
}
(path.parent / "qa.json").write_text(json.dumps(report, indent=2) + "\n")
