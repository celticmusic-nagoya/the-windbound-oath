"""Render a noncanonical material board: limestone courses + directional beam."""
import bpy,sys,os,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from aidan_material_variation_v1 import stone_material,timber_material
from aidan_dressed_stone_v2 import create_dressed_stone_v2
out=Path(os.environ.get("AIDAN_MATERIAL_OUTPUT","/tmp/aidan-material-study"))
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
col=bpy.data.collections.new("AIDAN_MATERIAL_STUDY_ONLY")
bpy.context.scene.collection.children.link(col)
stones=[]
for row in range(5):
 for i in range(5):
  sid=row*5+i
  mat=stone_material(sid,low_course=(row<2),exposure=.65)
  obj=create_dressed_stone_v2("study stone %02d"%sid,
      ((i-2)*.41+(row%2)*.15,0,row*.29+.12),(.39,.28,.27),
      mat,col,seed=141127+sid)
  stones.append(obj)
assert len(stones)==25
assert len(set(o.data.materials[0].name for o in stones))==25
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-.22,1.8))
beam=bpy.context.object;beam.name="timber grain study"
beam.dimensions=(2.3,.22,.18)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
beam.data.materials.append(timber_material(1))
assert beam.data.materials[0].use_nodes
world=bpy.context.scene.world or bpy.data.worlds.new("neutral world")
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.5
bpy.ops.object.light_add(type="AREA",location=(-3,-4,6))
bpy.context.object.data.energy=950;bpy.context.object.data.size=3
bpy.ops.object.camera_add(location=(3,-6,3.4))
cam=bpy.context.object;cam.data.type="ORTHO";cam.data.ortho_scale=3.5
cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene;scene.camera=cam
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
scene.render.resolution_x=900;scene.render.resolution_y=700
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
p=out/"material_study.png";scene.render.filepath=str(p)
bpy.ops.render.render(write_still=True)
assert p.stat().st_size>1000
report={"status":"CANDIDATE_NOT_ART_APPROVED","stones":len(stones),
        "timber":1,"blender":bpy.app.version_string,
        "png_sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
(out/"manifest.json").write_text(json.dumps(report,indent=2))
print("AIDAN_MATERIAL_QA="+json.dumps(report))
