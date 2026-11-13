import bpy, math, random, json, hashlib, os
from pathlib import Path
from mathutils import Vector
random.seed(41)
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"))/"rilde_phase1";out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
def material(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
M={k:material(k,v) for k,v in {"earth":(.48,.37,.23),"grass":(.26,.40,.19),"stone":(.42,.43,.40),"wood":(.36,.22,.12),"wall":(.70,.63,.46),"roof":(.27,.23,.20),"leaves":(.21,.36,.17),"skin":(.72,.51,.37),"cloth":(.20,.32,.43)}.items()}
def cube(n,loc,dims,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M[mat]);return o
def cyl(n,loc,r,h,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=h,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(M[mat]);return o
def rock(x,y):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.48,location=(x,y,.28));bpy.context.object.name="common/rock";bpy.context.object.data.materials.append(M["stone"])
def tree(x,y):
 cyl("common/tree/trunk",(x,y,.85),.18,1.7,"wood")
 for dx,dy,dz in [(-.35,0,1.9),(.3,.1,2.1),(0,-.3,2.3)]:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.75,location=(x+dx,y+dy,dz));bpy.context.object.name="common/tree/canopy";bpy.context.object.data.materials.append(M["leaves"])
def fence(x,y):
 for dx in [-.9,.9]:cube("rilde/fence/post",(x+dx,y,.48),(.13,.13,.96),"wood")
 for z in [.35,.7]:cube("rilde/fence/rail",(x,y,z),(1.95,.1,.1),"wood")
def house(x,y):
 cube("rilde/house/floor",(x,y,.12),(4.6,3.6,.24),"stone")
 cube("rilde/house/wall",(x,y,1.45),(4.35,3.35,2.65),"wall")
 for dx in [-2.2,2.2]:
  for dy in [-1.7,1.7]:cube("rilde/house/post",(x+dx,y+dy,1.55),(.2,.2,2.9),"wood")
 cube("rilde/house/door",(x,y-1.73,.95),(.85,.08,1.8),"wood")
 for dx in [-1.3,1.3]:cube("rilde/house/window",(x+dx,y-1.75,1.7),(.55,.08,.65),"wood")
 for side in [-1,1]:
  o=cube("rilde/house/roof",(x,y+side*.9,3.13),(5.1,2.55,.18),"roof");o.rotation_euler.x=side*math.radians(28)
for x in range(-12,14,2):
 for y in range(-10,12,2):cube("common/ground/"+("earth" if abs(x)<2 or abs(y)<2 else "grass"),(x,y,-.16),(2,2,.3),"earth" if abs(x)<2 or abs(y)<2 else "grass")
for x,y in [(-10,8),(-6,8),(6,8),(10,8),(-10,-8),(10,-8)]:tree(x,y)
for x,y in [(-8,-5),(8,6),(-6,6),(10,-4)]:rock(x,y)
for x,y in [(-7,3),(6,4),(-6,-5),(7,-5)]:house(x,y)
for x in [-10,-8,-6,-4,4,6,8,10]:fence(x,-8)
for x,y in [(-3,6),(3,-6),(10,1)]:cube("common/step",(x,y,.2),(2,1,.4),"stone")
cyl("rilde/well/base",(2,2,.36),.78,.72,"stone")
cyl("rilde/well/opening",(2,2,.76),.54,.10,"wood")
for x in [1.3,2.7]:cube("rilde/well/post",(x,2,1.32),(.12,.12,1.35),"wood")
cube("rilde/well/canopy",(2,2,2.1),(2.2,1.7,.15),"roof")
cyl("scale_proxy/legs",(0,-1,.42),.19,.83,"wood");cube("scale_proxy/torso",(0,-1,1.15),(.5,.32,.75),"cloth")
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.28,location=(0,-1,1.72));bpy.context.object.name="scale_proxy/head";bpy.context.object.data.materials.append(M["skin"])
world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.65,.72,.67,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.75
light=bpy.data.lights.new("Rilde warm sun","AREA");o=bpy.data.objects.new("Rilde warm sun",light);bpy.context.collection.objects.link(o);o.location=(-8,-7,16);light.energy=2300;light.shape="DISK";light.size=11
cam=bpy.data.cameras.new("Quarter view camera");o=bpy.data.objects.new("Quarter view camera",cam);bpy.context.collection.objects.link(o);o.location=(26,-35,37);o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat("-Z","Y").to_euler();cam.type="ORTHO";cam.ortho_scale=37
sc=bpy.context.scene;sc.camera=o;sc.render.engine="BLENDER_EEVEE_NEXT";sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.image_settings.file_format="PNG";sc.render.filepath=str(out/"rilde_base_game_view.png")
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_base.blend"));bpy.ops.render.render(write_still=True)
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/"rilde_base.blend",out/"rilde_base_game_view.png"]}
(out/"manifest.json").write_text(json.dumps({"status":"PROVISIONAL_NOT_CANON","camera":"provisional, not CG-calibrated","character":"neutral proxy","files":files},indent=2))
