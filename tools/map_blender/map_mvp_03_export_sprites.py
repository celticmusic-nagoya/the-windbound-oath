"""MAP-MVP-03: render 3 independent provisional orthographic sprites.
Run: blender -b --python tools/map_blender/map_mvp_03_export_sprites.py
Output is CI artifact only; no production asset is replaced.
"""
import bpy, os, json, hashlib, math
from pathlib import Path
from mathutils import Vector
OUT=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"))/"map_mvp_03"
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE"
scene.render.film_transparent=True;scene.render.resolution_x=256;scene.render.resolution_y=256;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
plaster=mat("plaster",(.69,.61,.48));roof=mat("roof",(.44,.23,.16));wood=mat("wood",(.28,.19,.13));leaf=mat("leaf",(.28,.42,.26));rock=mat("rock",(.43,.46,.42))
def cube(name,loc,scale,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o
def ico(name,loc,scale,m):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m)
def house():
 cube("plaster",(0,0,1.3),(2.6,2.3,2.6),plaster)
 cube("door",(0,-1.19,.8),(.65,.12,1.6),wood)
 for x in (-.82,.82):cube("window",(x,-1.19,1.55),(.48,.10,.55),wood)
 for side in (-1,1):
  # roof as a rotated thin rectangular slab, mirrored
  o=cube("roof slope",(0,side*.66,3.1),(3.15,1.85,.14),roof);o.rotation_euler[0]=side*math.radians(38)
 cube("chimney",(.7,.45,3.45),(.4,.4,1),rock)
def tree():
 cube("trunk",(.0,0,1.15),(.4,.4,2.3),wood)
 for p,s in [((-.5,0,2.65),(1.0,.85,.75)),((.4,.25,3.0),(.9,.9,.85)),((-.1,-.35,3.45),(.85,.85,.7))]:ico("foliage",p,s,leaf)
def boulder():
 for p,s in [((0,0,.5),(1.15,.9,.65)),((.6,.1,.4),(.6,.7,.48))]:ico("boulder",p,s,rock)
bpy.ops.object.camera_add(location=(7,-10,7));cam=bpy.context.object;scene.camera=cam
cam.rotation_euler=(Vector((0,0,1.5))-cam.location).to_track_quat("-Z","Y").to_euler();cam.data.type="ORTHO";cam.data.ortho_scale=6.6
bpy.ops.object.light_add(type="SUN",location=(3,-4,9));bpy.context.object.data.energy=2.2
files={}
for name,fn in [("house",house),("tree",tree),("rock",boulder)]:
 # remove geometry only, preserve camera and sun
 for o in list(scene.objects):
  if o.type=="MESH":bpy.data.objects.remove(o,do_unlink=True)
 fn();p=OUT/(name+".png");scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
manifest={"task":"MAP-MVP-03","status":"PROVISIONAL","source":"procedural Blender primitives","camera":"orthographic","background":"transparent RGBA","runtime_integration":False,"art_qa":"NOT_RUN","files":files}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2))
print("MAP-MVP-03 exported",sorted(files))
