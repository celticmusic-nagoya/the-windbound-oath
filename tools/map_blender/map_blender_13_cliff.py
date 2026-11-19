"""MAP-BLENDER-13: non-destructive coastal cliff mesh study, no canon promotion."""
import bpy,os,json,hashlib,math,random
from pathlib import Path
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
source=out/"rilde_map12.blend"
if not source.is_file():raise RuntimeError("Missing MAP12 predecessor")
sha=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
cfg={"seed":1313,"cliff_center":[-23,10],"half_width":5.5,"half_length":8.5,"rings":7,"segments":18,"top_height":4.85,"base_height":-0.4,"noise":0.55}
rng=random.Random(cfg["seed"])
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
rock=mat("MAP13 coastal weathered rock",(.37,.35,.31))
grass=mat("MAP13 coastal turf",(.27,.36,.22))
# Hide the placeholder but retain its mesh in the source scene.
old=bpy.data.objects.get("Western cliff plateau")
if old:old.hide_render=True
cx,cy=cfg["cliff_center"];w=cfg["half_width"];d=cfg["half_length"]
n=cfg["segments"];rings=cfg["rings"]
verts=[]
for r in range(rings):
 t=r/(rings-1)
 z=cfg["base_height"]+(cfg["top_height"]-cfg["base_height"])*t
 for j in range(n):
  a=2*math.pi*j/n
  wave=.25*math.sin(3*a+1)+.17*math.sin(7*a)
  radius=(1.06-.13*t)+wave*.35+rng.uniform(-.06,.06)
  x=cx+math.cos(a)*w*radius
  y=cy+math.sin(a)*d*radius
  verts.append((x,y,z+rng.uniform(-cfg["noise"],cfg["noise"])*(.5 if r==rings-1 else 1)))
faces=[]
for r in range(rings-1):
 for j in range(n):
  k=r*n+j;next_j=r*n+(j+1)%n
  faces.append((k,next_j,next_j+n,k+n))
faces.append(tuple(range((rings-1)*n,rings*n)))
mesh=bpy.data.meshes.new("MAP13 coastal cliff mesh")
mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new("MAP13 coastal cliff",mesh)
bpy.context.collection.objects.link(obj);mesh.materials.append(rock)
# Separate thin turf cap; original rock remains independently editable.
capverts=[(x,y,z+.12) for x,y,z in verts[(rings-1)*n:]]
capmesh=bpy.data.meshes.new("MAP13 turf mesh")
capmesh.from_pydata(capverts,[],[tuple(range(n))]);capmesh.update()
cap=bpy.data.objects.new("MAP13 cliff turf",capmesh)
bpy.context.collection.objects.link(cap);capmesh.materials.append(grass)
scene=bpy.context.scene
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_map13_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map13.blend"))
names=["rilde_map13_preview.png","rilde_map13.blend"]
report={"task":"MAP-BLENDER-13","status":"CLIFF_CANDIDATE","source_sha256":sha,"config":cfg,"cliff_occlusion_qa":"NOT_RUN","visual_qa":"NOT_RUN","runtime_modified":False,"files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map13_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
