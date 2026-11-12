"""Independent GLB export, no dependency on rendering success."""
import bpy,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
src=ROOT/"assets/candidates/morwen-blender-24/morwen_anatomical_torso_candidate.blend"
out=ROOT/"assets/candidates/morwen-blender-28"
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))
mesh=next(o for o in bpy.data.objects if o.type=="MESH" and "Morwen_24_" in o.name)
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
dest=out/"morwen_torso_candidate.glb"
bpy.ops.export_scene.gltf(filepath=str(dest),export_format="GLB",use_selection=True)
data=dest.read_bytes()
assert data[:4]==b"glTF" and struct.unpack_from("<I",data,8)[0]==len(data)
(out/"export_report.json").write_text(json.dumps({"glb":dest.name,"bytes":len(data),"art_qa":"NOT_RUN","production":False},indent=2)+"\n")
print("MORWEN_28_GLB_PASS")
