"""MAP-BLENDER-11: additive Rilde visual-detail pass; original blockout unchanged."""
import bpy, os, json, hashlib, random
from pathlib import Path
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
source=out/"rilde_blockout.blend"
if not source.is_file(): raise RuntimeError("Missing base blockout; do not synthesize replacement")
bpy.ops.wm.open_mainfile(filepath=str(source))
random.seed(1108)
def mat(name,rgb):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
 m.diffuse_color=(*rgb,1)
 return m
wall=mat("Lime plaster",(0.70,0.65,0.52))
beam=mat("Exposed timber",(0.29,0.18,0.11))
leaf=mat("Leaf canopy",(0.18,0.34,0.16))
flower=mat("Flower accents",(0.67,0.35,0.29))
cobble=mat("Cobblestone",(0.51,0.48,0.42))
def block(name,loc,dims,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 obj=bpy.context.object;obj.name=name;obj.dimensions=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 obj.data.materials.append(material)
 return obj
for i,(x,y) in enumerate([(-8,4),(-4,7),(6,6),(9,1),(-7,-5),(4,-7)]):
 # Keep canonical blockout geometry; add independent facade and timber trim
 block("DETAIL_house_%02d_facade"%i,(x,y-1.58,1.3),(2.95,0.08,2.25),wall)
 for side in (-1,1):
  block("DETAIL_house_%02d_post_%d"%(i,side),(x+side*1.35,y-1.66,1.3),(0.18,0.13,2.6),beam)
 block("DETAIL_house_%02d_crossbeam"%i,(x,y-1.67,2.4),(2.9,0.13,0.16),beam)
 block("DETAIL_house_%02d_door"%i,(x,y-1.72,0.73),(0.72,0.13,1.45),beam)
for i in range(42):
 x=random.uniform(-4.1,4.1);y=random.uniform(-3.6,3.6)
 block("DETAIL_cobble_%03d"%i,(x,y,0.075),(random.uniform(.28,.65),random.uniform(.2,.5),.04),cobble)
for i,(x,y) in enumerate([(-12,-8),(-11,9),(12,-8),(11,10),(-2,-12),(7,-12)]):
 block("DETAIL_tree_trunk_%02d"%i,(x,y,1.1),(.38,.38,2.2),beam)
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1.5,location=(x,y,2.9))
 obj=bpy.context.object;obj.name="DETAIL_tree_canopy_%02d"%i;obj.data.materials.append(leaf)
for i,(x,y) in enumerate([(-9,-8),(-5,-9),(8,-9),(11,5)]):
 block("DETAIL_flowerbed_%02d"%i,(x,y,.16),(1.2,.6,.3),flower)
scene=bpy.context.scene
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_detail_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_detail.blend"))
files=["rilde_detail_preview.png","rilde_detail.blend"]
report={"task":"MAP-BLENDER-11","status":"DETAIL_CANDIDATE","source":"rilde_blockout.blend","source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"canon_coordinates":"PROVISIONAL","art_direction_qa":"NOT_VERIFIED","android_qa":"NOT_RUN","runtime_modified":False,"files":{p:hashlib.sha256((out/p).read_bytes()).hexdigest() for p in files}}
(out/"detail_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))
