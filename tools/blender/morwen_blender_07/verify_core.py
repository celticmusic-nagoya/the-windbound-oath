"""Independent Blender geometry/rig QA for Morwen 07 candidate."""
import bpy
from pathlib import Path
import json
root=Path(__file__).resolve().parents[3]
out=root/"assets/candidates/morwen-blender-07"
rig=bpy.data.objects["Morwen_unified_17_candidate"]
core=bpy.data.objects["Morwen_07_continuous_core_candidate"]
old=bpy.data.objects["Morwen_unified_neutral_3d_candidate"]
assert len(rig.data.bones)==17
assert len(core.data.vertices)==168
assert len(core.data.polygons)==146
assert len(core.vertex_groups)==2
assert old.hide_render is False
assert any(m.type=="ARMATURE" and m.object==rig for m in core.modifiers)
assert all(len(v.groups)>=1 for v in core.data.vertices)
assert all(p.area>0 for p in core.data.polygons)
report=json.loads((out/"build_report.json").read_text())
assert report["production_use"] is False and report["full_body_continuous"] is False
print("MORWEN_07_RELOAD_GEOMETRY_RIG_QA_PASS")
