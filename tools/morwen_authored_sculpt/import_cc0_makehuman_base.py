"""Read-only CC0 MakeHuman base mesh import and geometry QA. No character adoption.
Usage: blender -b --factory-startup --python-exit-code 1 --python this.py -- input.obj output_dir
"""
import bpy,sys,pathlib,hashlib,json
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:];src=pathlib.Path(argv[0]);out=pathlib.Path(argv[1]);out.mkdir(parents=True,exist_ok=True)
assert src.is_file() and src.stat().st_size>100000
sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(src),forward_axis="Y",up_axis="Z")
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert meshes,"OBJ_IMPORT_NO_MESH"
verts=sum(len(o.data.vertices) for o in meshes);faces=sum(len(o.data.polygons) for o in meshes)
assert verts>10000 and faces>10000,(verts,faces)
for ob in meshes:
 ob.name="CC0_MAKEHUMAN_UNMODIFIED_SOURCE_"+ob.name
 ob["source_url"]="https://github.com/makehumancommunity/mpfb2/blob/master/src/mpfb/data/3dobjs/base.obj"
 ob["source_sha256"]=sha
 ob["status"]="UNMODIFIED_SOURCE_ONLY_NOT_MORWEN"
scene=bpy.context.scene
scene["asset_status"]="CC0_SOURCE_IMPORT_NOT_CHARACTER_SCULPT"
scene["source_sha256"]=sha
scene["design_reference"]="MORWEN_LAYER0_NOT_YET_ALIGNED"
scene["license"]="CC0_BUNDLED_MAKEHUMAN_BASE_VERIFY_UPSTREAM"
blend=out/"MAKEHUMAN_CC0_UNMODIFIED_BASE_IMPORT_CANDIDATE.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
report={"status":"SOURCE_IMPORT_ONLY_NOT_SCULPT","source_sha256":sha,"source_size":src.stat().st_size,"blender":bpy.app.version_string,"meshes":len(meshes),"vertices":verts,"faces":faces,"blend_sha256":hashlib.sha256(blend.read_bytes()).hexdigest(),"G1":"NOT_RUN_MORWEN_FIT","G2":"NOT_RUN","G3":"PARTIAL_IMPORT_ONLY","G4":"NOT_RUN"}
(out/"source_import_qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("MAKEHUMAN_CC0_SOURCE_IMPORT",json.dumps(report))
