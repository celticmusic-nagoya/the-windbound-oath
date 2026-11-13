"""Import pinned VRM into an isolated Blender process and audit mesh topology."""
import bpy,sys,runpy
from pathlib import Path
source=Path("render_output/morwen_vroid_review/Base_Female.vrm")
assert source.is_file()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
assert any(o.type=="MESH" for o in bpy.data.objects)
script=Path("tools/blender/morwen_production/mesh_topology_audit.py")
sys.argv=[str(script),"--output","render_output/morwen_vroid_review/MESH_TOPOLOGY_AUDIT.json"]
runpy.run_path(str(script),run_name="__main__")
