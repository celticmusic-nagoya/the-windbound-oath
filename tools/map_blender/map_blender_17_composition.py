"""MAP17 composition candidate: irregular village districts and separated landforms."""
import bpy,os,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
src=out/"rilde_map16.blend"
if not src.is_file():raise RuntimeError("MAP16 source missing")
source_sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src))
for name in ("Intervening ridge","MAP14 curved intervening ridge","MAP15 blended ridge"):
 o=bpy.data.objects.get(name)
 if o:o.hide_render=True
# Hide old regular grid without deleting its geometry; retain rollback.
for o in list(bpy.data.objects):
 if o.name.startswith(("House ","Roof ","MAP12 gable")):o.hide_render=True
def mat(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
earth=mat("MAP17 coastal earth",(.31,.34,.22))
turf=mat("MAP17 coastal turf",(.27,.39,.22))
timber=mat("MAP17 weathered timber",(.39,.27,.17))
plaster=mat("MAP17 warm plaster",(.66,.56,.41))
tile=mat("MAP17 red tile",(.52,.23,.14))
def box(name,loc,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 o=bpy.context.object;o.name=name;o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material);return o
# Low asymmetric hills with smooth shoulders; not a single occluding wall.
def hill(name,cx,cy,rx,ry,h,phase):
 n=28; rings=9;vs=[];fs=[]
 for i in range(rings):
  radius=i/(rings-1)
  for j in range(n):
   a=2*math.pi*j/n
   wobble=1+.075*math.sin(3*a+phase)+.05*math.cos(5*a+phase)
   x=cx+rx*radius*math.cos(a)*wobble
   y=cy+ry*radius*math.sin(a)*wobble
   z=h*(1-radius**2)**2+.08*math.sin(a*4+phase)*radius*(1-radius)
   vs.append((x,y,max(0,z)))
 for i in range(rings-1):
  for j in range(n):
   a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 mesh=bpy.data.meshes.new(name+" mesh");mesh.from_pydata(vs,[],fs);mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
 mesh.materials.append(earth);mesh.materials.append(turf)
 for p in mesh.polygons:
  p.material_index=1 if p.center.z>h*.55 else 0;p.use_smooth=True
 return ob
hills=[hill("MAP17 coastal rise A",-18,10,6,8,3.2,0.3),hill("MAP17 coastal rise B",-13,15,5,6,3.8,1.7),hill("MAP17 coastal rise C",-11,5,4,5,2.6,2.8)]
# Nonuniform village arrangement; preserve clear central square and bridge route.
houses=[(-8,4,0.18),(-5,8,-.12),(7,7,.13),(10,1,-.2),(-7,-7,.15),(5,-8,-.1)]
for i,(x,y,angle) in enumerate(houses):
 body=box("MAP17 cottage %02d"%i,(x,y,1.35),(3.0,2.8,2.7),plaster if i%2 else timber)
 body.rotation_euler.z=angle
 # Roof pair as pitched faces, not flat rectangular lids.
 mesh=bpy.data.meshes.new("MAP17 roof %02d"%i)
 v=[(-1.85,-1.65,2.75),(1.85,-1.65,2.75),(0,-1.65,4.05),(-1.85,1.65,2.75),(1.85,1.65,2.75),(0,1.65,4.05)]
 mesh.from_pydata(v,[],[(0,1,2),(3,5,4),(0,2,5,3),(2,1,4,5)],[])
 mesh.update()
 roof=bpy.data.objects.new("MAP17 pitched roof %02d"%i,mesh)
 bpy.context.collection.objects.link(roof);roof.location=(x,y,0);roof.rotation_euler.z=angle
 mesh.materials.append(tile)
# Visibility is a diagnostic, not a pass condition for an unapproved layout.
observers=[(-21,8,5.2),(-20,10,5.2),(-19,12,5.2)]
targets=[(-8,4,3),(0,2,2.5),(6,6,3)]
bvhs=[BVHTree.FromObject(h,bpy.context.evaluated_depsgraph_get()) for h in hills]
rays=[]
for a in observers:
 for b in targets:
  start=Vector(a);ray=Vector(b)-start
  blocked=any(tree.ray_cast(start,ray.normalized(),ray.length)[0] is not None for tree in bvhs)
  rays.append({"observer":a,"target":b,"blocked":blocked})
scene=bpy.context.scene;scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_map17_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map17.blend"))
files=["rilde_map17_preview.png","rilde_map17.blend"]
report={"task":"MAP-BLENDER-17","status":"COMPOSITION_CANDIDATE","source_sha256":source_sha,"occlusion":{"blocked":sum(r["blocked"] for r in rays),"total":len(rays),"cases":rays},"occlusion_acceptance":"NOT_VERIFIED","route_connectivity":"NOT_VERIFIED","visual_qa":"NOT_RUN","files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in files}}
(out/"map17_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"task":"MAP17","occlusion_samples":report["occlusion"]["blocked"]}))
