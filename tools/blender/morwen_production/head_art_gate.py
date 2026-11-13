"""Independent Morwen head geometry gate. Run inside Blender on candidate .blend.
Rejects smooth capsule-like heads even when PNG rendering succeeds.
This is a necessary, not sufficient, art gate.
"""
import bpy, json, sys
from pathlib import Path
scene=bpy.context.scene
heads=[o for o in bpy.data.objects if o.type=="MESH" and "HEAD" in o.name.upper()]
out={"schema":"MORWEN-HEAD-ART-GATE-01","candidates":[],"G2":"FAIL"}
for obj in heads:
 mesh=obj.data
 # Deformation-ready face needs localized topology and named anatomical structures.
 parts={o.name.lower() for o in bpy.data.objects}
 required=("nose","ear_l","ear_r","eyelid_l","eyelid_r","mouth")
 present={n:any(n in name for name in parts) for n in required}
 polys=len(mesh.polygons)
 # Review topology is all 32-vertex rings; this cannot provide eyes/nose/mouth.
 quad_count=sum(len(p.vertices)==4 for p in mesh.polygons)
 material_count=len(mesh.materials)
 passes=polys>=600 and all(present.values()) and quad_count/max(polys,1)>=.8
 out["candidates"].append({"name":obj.name,"polygons":polys,"quad_fraction":round(quad_count/max(polys,1),3),"materials":material_count,"required_anatomical_parts":present,"structural_gate":"PASS" if passes else "FAIL"})
out["G2"]="STRUCTURAL_GATE_PASS_ART_REVIEW_REQUIRED" if out["candidates"] and all(c["structural_gate"]=="PASS" for c in out["candidates"]) else "FAIL"
out["limitations"]="Topology checks cannot replace official design comparison or human aesthetic review."
path=Path("render_output/morwen_head_review/ART_GATE.json")
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out))
if out["G2"]=="FAIL":sys.exit(2)
