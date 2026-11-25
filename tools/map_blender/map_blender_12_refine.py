"""MAP-BLENDER-12: additive parametric roof and terrain candidate."""
import bpy,os,json,hashlib,random
from pathlib import Path
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
source=out/"rilde_detail.blend"
if not source.is_file():raise RuntimeError("Missing MAP11 source")
sha=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
config={"seed":1211,"houses":[[-8,4],[-4,7],[6,6],[9,1],[-7,-5],[4,-7]],"roof_width":4.3,"roof_depth":4.2,"ridge_z":4.3,"eave_z":3.0,"grass_count":60}
random.seed(config["seed"])
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
terracotta=material("MAP12 terracotta",(.5,.19,.11))
green=material("MAP12 grass",(.25,.39,.2))
stone=material("MAP12 stone",(.47,.44,.4))
def block(name,xyz,dimensions,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz)
 o=bpy.context.object;o.name=name;o.dimensions=dimensions
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(mat)
for i,(x,y) in enumerate(config["houses"]):
 old=bpy.data.objects.get("Roof %02d"%i)
 if old:old.hide_render=True
 w=config["roof_width"]/2;d=config["roof_depth"]/2
 z=config["eave_z"];h=config["ridge_z"]
 vertices=[(x-w,y-d,z),(x+w,y-d,z),(x,y-d,h),(x-w,y+d,z),(x+w,y+d,z),(x,y+d,h)]
 faces=[(0,1,2),(3,5,4),(0,3,4,1),(0,2,5,3),(2,1,4,5)]
 mesh=bpy.data.meshes.new("MAP12 roof mesh");mesh.from_pydata(vertices,[],faces);mesh.update()
 obj=bpy.data.objects.new("MAP12 gable %02d"%i,mesh);bpy.context.collection.objects.link(obj)
 obj.data.materials.append(terracotta)
for i in range(config["grass_count"]):
 x=random.uniform(-16,12);y=random.uniform(-14,14)
 if abs(x)<5 and abs(y)<5:continue
 block("MAP12 grass %03d"%i,(x,y,.07),(.32,.38,.12),green)
for i in range(45):
 x=random.uniform(-4,4);y=random.uniform(-3.5,3.5)
 block("MAP12 cobble %03d"%i,(x,y,.11),(.35,.25,.06),stone)
scene=bpy.context.scene
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_map12_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map12.blend"))
names=["rilde_map12_preview.png","rilde_map12.blend"]
report={"task":"MAP-BLENDER-12","status":"CANDIDATE_ONLY","source_sha256":sha,"config":config,"visual_qa":"NOT_RUN","runtime_modified":False,"files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map12_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
