"""Fail-closed Morwen production preflight. Does not replace visual art QA."""
import bpy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REF=ROOT.parent/"production_mesh_08"
OUT=Path("render_output/morwen_walk");OUT.mkdir(parents=True,exist_ok=True)
errors=[]
manifest=json.loads((REF/"layer0_reference_manifest.json").read_text())
for entry in manifest["images"]:
    path=REF/"references"/entry["filename"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]:
        errors.append("Canonical image missing or hash mismatch: "+entry["view"])
rig=bpy.data.objects.get("MORWEN_MASTER_RIG")
body=bpy.data.objects.get("MORWEN_PRODUCTION_MESH")
expected=["root","pelvis","spine_01","chest","neck","head",
"clavicle.L","upper_arm.L","forearm.L","hand.L","clavicle.R","upper_arm.R","forearm.R","hand.R",
"thigh.L","shin.L","foot.L","toe.L","thigh.R","shin.R","foot.R","toe.R",
"hat","cape.L","cape.R","satchel"]
if not rig or rig.type!="ARMATURE":errors.append("MORWEN_MASTER_RIG armature missing")
else:
    missing=set(expected)-set(rig.data.bones.keys())
    if missing:errors.append("Missing bones: "+", ".join(sorted(missing)))
    if len(rig.data.bones)!=26:errors.append("Expected 26 bones")
if not body or body.type!="MESH":errors.append("MORWEN_PRODUCTION_MESH missing")
else:
    if len(body.data.vertices)<1000:errors.append("Mesh detail below minimum")
    if not rig or not any(m.type=="ARMATURE" and m.object==rig for m in body.modifiers):
        errors.append("Armature modifier missing")
    if not body.vertex_groups:errors.append("Skin weights missing")
if not bpy.data.objects.get("MORWEN_GARTER_RIGHT_ONLY"):
    errors.append("Right-leg-only garter object missing")
if bpy.data.objects.get("MORWEN_GARTER_LEFT"):
    errors.append("Forbidden left-leg garter present")
report={"errors":errors,"technical_pass":not errors,"G1":"REFERENCE_HASH_ONLY",
"G2":"NOT_RUN","G3":"PASS" if not errors else "FAIL","G4":"NOT_RUN","production_approved":False}
(OUT/"preflight.json").write_text(json.dumps(report,indent=2))
if errors:raise RuntimeError("; ".join(errors))
