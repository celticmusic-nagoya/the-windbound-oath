import bpy, math, random, json, hashlib, os
from pathlib import Path
from mathutils import Vector
random.seed(41)
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"))/"rilde_phase1";out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
def material(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*c,1);m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.9;return m
M={k:material(k,v) for k,v in {"earth":(.48,.37,.23),"grass":(.26,.40,.19),"stone":(.42,.43,.40),"wood":(.36,.22,.12),"wall":(.70,.63,.46),"roof":(.48,.22,.12),"water":(.13,.34,.43),"sand":(.59,.53,.36),"path":(.51,.43,.31),"moss":(.13,.29,.16),"leaves":(.21,.36,.17),"skin":(.72,.51,.37),"cloth":(.20,.32,.43),"roof_light":(.61,.31,.19),"roof_dark":(.34,.15,.09),"wood_light":(.47,.31,.18),"wall_shadow":(.55,.51,.41),"crop":(.53,.57,.19),"flower":(.65,.35,.16)}.items()}
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
  for i in range(8):
   for j in range(4):
    t=cube("rilde/house/roof_tile",(x-2.15+i*.61,y+side*(.27+j*.54),3.13+side*(j-1.5)*.015),(.58,.52,.045),"roof_light" if (i+j)%3 else "roof_dark");t.rotation_euler.x=side*math.radians(28)
 for dx in [-1.85,0,1.85]:
  cube("rilde/house/crossbeam",(x+dx,y-1.76,2.1),(.14,.12,1.05),"wood")
 cube("rilde/house/lintel",(x,y-1.78,2.57),(4.1,.14,.15),"wood_light")
 cube("rilde/house/chimney",(x+1.45,y+.65,3.66),(.55,.55,1.5),"stone")
 cube("rilde/house/chimney_cap",(x+1.45,y+.65,4.47),(.76,.76,.13),"stone")
# Approved geography (2026-11-08): west sea/cliff, SW harbor, center village,
# north farmland/trade road, east north-to-south river, SE Moss Forest.
# Coordinates are composition proxies; CG-verified shapes remain pending.
for x in range(-16,18,2):
 for y in range(-12,14,2):
  if x <= -12:
   cube("world/sea",(x,y,-.42),(2,2,.14),"water")
  else:
   kind="grass"
   if (abs(x)<3 and -6<y<7) or (abs(y-1)<2 and -11<x<13) or (abs(x-1)<2 and y>5):kind="earth"
   if x>=12 and y>-8:kind="water"
   if x>=7 and y<=-6:kind="moss"
   elevation=.12*math.sin(x*.32)+.11*math.cos(y*.38)+.08*math.sin((x+y)*.49)
   cube("world/ground/"+kind,(x,y,-.22+elevation/2),(2,2,.44+elevation),kind)
# West coastal cliff and southern fishing harbor: intentionally simplified silhouettes.
for y in [-8,-6,-4,-2,0,2,4,6,8,10]:
 rock(-11,y)
for x in [-10,-8,-6]:cube("world/harbor/pier",(x,-10,.05),(1.7,1.8,.18),"wood")
# East river with stone bridge; no artificial change to river flow on wind stop.
for y in range(-10,12,2):
 cube("world/river/surface",(12,y,-.03),(2.3,2,.08),"water")
for x in [10.5,12,13.5]:cube("world/bridge/deck",(x,1,.23),(1.7,2.2,.38),"stone")
for x,y in [(-6,4),(-2,5),(4,4),(5,-2)]:house(x,y)
# The wind stone is a prominent village landmark, not a generic rock.
cyl("rilde/windstone/plinth",(0,0,.28),.82,.56,"stone")
cube("rilde/windstone/monolith",(0,0,1.25),(.85,.48,1.7),"stone")
# North farmland and fortress trade route; route direction only, fort location not asserted.
for x in [-8,-6,-4,4,6,8]:
 for y in [8,10]:
  cube("world/farmland/plot",(x,y,.10),(1.55,1.55,.12),"earth")
  for k in range(4):cube("world/farmland/crop_row",(x-.55+k*.36,y,.19),(.12,1.4,.12),"crop")
for x in [-6,-4,4,6]:fence(x,7)
# Southeast Moss Forest, distinct from the northern fortress trade road.
for x,y in [(7,-7),(9,-9),(11,-7),(7,-11),(15,-10),(15,-6),(9,-5)]:tree(x,y)
for x,y in [(8,-10),(14,-8),(10,-11)]:rock(x,y)
# Small village vegetation and stones.
for x,y in [(-8,7),(-9,4),(7,5),(-8,-3)]:tree(x,y)
for x,y in [(-7,-5),(8,6),(5,-5)]:rock(x,y)
for x in [-8,-6,-4,4,6,8]:fence(x,-5)
# Roadside wear, scattered stones and hand-built garden borders.
for i in range(36):
 x=random.uniform(-10,9);y=random.uniform(-5,7)
 if abs(x)<2 and abs(y)<2:continue
 if i%4==0:rock(x,y)
 else:cube("rilde/clutter/ground_stone",(x,y,.09),(.17,.11,.09),"stone")
for x,y in [(-5,1),(4,-4),(6,2),(-7,2)]:
 for j in range(5):cube("rilde/garden/flower",(x+j*.21,y,.18),(.12,.12,.25),"flower")
cyl("rilde/well/base",(2,2,.36),.78,.72,"stone")
cyl("rilde/well/opening",(2,2,.76),.54,.10,"wood")
for x in [1.3,2.7]:cube("rilde/well/post",(x,2,1.32),(.12,.12,1.35),"wood")
cube("rilde/well/canopy",(2,2,2.1),(2.2,1.7,.15),"roof")
cyl("scale_proxy/legs",(0,-1,.42),.19,.83,"wood");cube("scale_proxy/torso",(0,-1,1.15),(.5,.32,.75),"cloth")
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.28,location=(0,-1,1.72));bpy.context.object.name="scale_proxy/head";bpy.context.object.data.materials.append(M["skin"])
world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.65,.72,.67,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.75
light=bpy.data.lights.new("Rilde warm sun","AREA");o=bpy.data.objects.new("Rilde warm sun",light);bpy.context.collection.objects.link(o);o.location=(-8,-7,16);light.energy=2300;light.shape="DISK";light.size=11
cam=bpy.data.cameras.new("Quarter view camera");o=bpy.data.objects.new("Quarter view camera",cam);bpy.context.collection.objects.link(o);o.location=(26,-35,42);o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat("-Z","Y").to_euler();cam.type="ORTHO";cam.ortho_scale=43
sc=bpy.context.scene;sc.camera=o;sc.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version >= (4,2,0) else "BLENDER_EEVEE";sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.image_settings.file_format="PNG";sc.render.filepath=str(out/"rilde_base_game_view.png")
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_base.blend"));bpy.ops.render.render(write_still=True)
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/"rilde_base.blend",out/"rilde_base_game_view.png"]}
(out/"manifest.json").write_text(json.dumps({"status":"WORLD_TOPOLOGY_APPROVED_2026_11_08_VISUAL_PROXY","camera":"provisional, not CG-calibrated","world":"west sea/cliff; southwest harbor; center Rilde; north trade road/farmland; east river/bridge; southeast Moss Forest","character":"neutral proxy","files":files},indent=2))
