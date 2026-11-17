"""SCULPT03 non-destructive editable workspace; NOT an artistic retopology."""
import bpy, hashlib, json, sys
from pathlib import Path

SOURCE=Path("assets/candidates/morwen-sculpt02/morwen_sculpt02_v02_UNAPPROVED.blend")
EXPECTED="90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b"
OUT=Path("qa_output/morwen-sculpt03")
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
assert SOURCE.exists() and digest(SOURCE)==EXPECTED,"SCULPT02 SOURCE HASH MISMATCH"
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE.resolve()))
assert "SCULPT02_FACE_BODY" in bpy.data.objects,"FACE MESH MISSING"
if bpy.context.object and bpy.context.object.mode!="OBJECT":bpy.ops.object.mode_set(mode="OBJECT")
scene=bpy.context.scene
coll=bpy.data.collections.new("SCULPT03_UNAPPROVED_EDIT_WORKSPACE")
scene.collection.children.link(coll)
face=bpy.data.objects["SCULPT02_FACE_BODY"]
clone=face.copy()
clone.data=face.data.copy()
clone.name="SCULPT03_FACE_RETOTOPO_TARGET_UNEDITED"
coll.objects.link(clone)
clone.hide_render=True
clone.hide_set(True)
clone["status"]="UNEDITED_WORKSPACE_ONLY_NOT_RETOPO"
clone["source_sha256"]=EXPECTED
hair=[o for o in bpy.data.objects if o.name.startswith("SCULPT02_HAIR_")]
assert len(hair)>=8, f"Expected >=8 hair objects, got {len(hair)}"
for obj in hair:
    obj["sculpt03_legacy_hair_candidate"]=True
    # Preserve original scene visibility and render outputs for comparison.
# Camera, materials, meshes and official packed reference images are retained.
target=OUT/"morwen_sculpt03_WORKSPACE_ONLY_UNAPPROVED.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(target.resolve()),compress=True)
assert digest(SOURCE)==EXPECTED,"SOURCE MODIFIED"
manifest={"status":"WORKSPACE_ONLY_NOT_SCULPTED","source_sha256":EXPECTED,
"workspace_sha256":digest(target),"face_clone":clone.name,
"face_clone_vertices":len(clone.data.vertices),"face_clone_polygons":len(clone.data.polygons),
"legacy_hair_objects":len(hair),"actual_retopology_completed":False,
"new_hair_geometry_completed":False,"G1":"BLOCKED","G2":"FAIL_EXISTING_CANDIDATE",
"G3":"NOT_RUN_FOR_NEW_SCULPT","G4":"NOT_RUN"}
(OUT/"workspace_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("SCULPT03_WORKSPACE_CREATED",manifest["workspace_sha256"])
