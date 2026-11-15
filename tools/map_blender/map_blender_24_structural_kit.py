"""MAP24 structural kit. Provisional independent assets; never writes canonical maps."""
import bpy, math, random, os, json, hashlib
from pathlib import Path
from mathutils import Vector
SEED=2401
rng=random.Random(SEED)
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"));out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
def material(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
plaster=material("warm plaster",(.68,.60,.46));wood=material("aged timber",(.27,.18,.12))
slate=[material("roof slate %d"%i,c) for i,c in enumerate([(.35,.17,.12),(.43,.23,.17),(.32,.18,.16)])]
stone=[material("fieldstone %d"%i,c) for i,c in enumerate([(.37,.40,.36),(.43,.44,.38),(.31,.35,.33)])]
leaf=material("foliage",(.25,.38,.22));leaf2=material("foliage light",(.31,.43,.26))
grass=material("meadow",(.33,.42,.26));dark=material("door and windows",(.12,.12,.10))
def block(name,pos,dim,mat,bevel=.02):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.dimensions=dim
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  b=o.modifiers.new("rounded edges","BEVEL");b.width=bevel;b.segments=2
  o.modifiers.new("weighted normals","WEIGHTED_NORMAL")
 return o
def beam(name,start,end,width,mat):
 a,b=Vector(start),Vector(end);v=b-a
 o=block(name,(a+b)*.5,(width,width,v.length),mat,.035)
 o.rotation_euler=v.to_track_quat("Z","Y").to_euler();return o
def cottage(x,y):
 block("cottage walls",(x,y,1.65),(5.8,4.6,3.3),plaster,.08)
 for dx in [-2.8,2.8]:
  for dy in [-2.23,2.23]:beam("corner timber",(x+dx,y+dy,.15),(x+dx,y+dy,3.35),.20,wood)
 for z in [.25,3.1]:
  block("timber beam",(x,y-2.34,z),(5.9,.20,.18),wood)
 block("entrance door",(x,y-2.40,1.08),(1.1,.09,2.12),dark)
 for dx in [-1.85,1.85]:
  block("window recess",(x+dx,y-2.40,1.85),(.78,.11,.95),dark)
  beam("window mullion",(x+dx,y-2.49,1.4),(x+dx,y-2.49,2.32),.07,wood)
  block("window sill",(x+dx,y-2.49,1.36),(.94,.17,.10),stone[1])
 # Two roof planes and overhanging ridge, with thin staggered slate courses.
 for side in [-1,1]:
  yedge=y+side*2.85
  for j in range(8):
   t0=j/8;t1=(j+1)/8
   ya=yedge*(1-t0)+y*t0;yb=yedge*(1-t1)+y*t1
   za=3.12+1.95*t0;zb=3.12+1.95*t1
   for k in range(13):
    xa=x-3.4+k*.55+(.26 if j%2 else 0)
    if xa>x+3.35:continue
    a=Vector((xa,(ya+yb)/2,(za+zb)/2))
    o=block("individual slate",a,(.58,.75,.09),slate[(k+j)%3],.01)
    slope=Vector((0,yb-ya,zb-za));o.rotation_euler=slope.to_track_quat("Y","Z").to_euler()
 beam("ridge cap",(x-3.45,y,5.12),(x+3.45,y,5.12),.19,wood)
 block("chimney",(x+1.7,y+.5,5.1),(.72,.68,1.45),stone[1],.05)
 block("chimney cap",(x+1.7,y+.5,5.88),(.91,.88,.16),stone[0])
def wall(x,y):
 for row in range(3):
  cursor=x+(.32 if row%2 else 0)
  while cursor<x+9:
   w=rng.uniform(.52,.94);h=rng.uniform(.34,.48)
   block("staggered fieldstone",(cursor+w/2,y+rng.uniform(-.08,.08),row*.43+h/2),(w,.7,h),rng.choice(stone),.055)
   cursor+=w+rng.uniform(.015,.075)
def rock(x,y):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,.48))
 o=bpy.context.object;o.name="grounded coastal boulder"
 for v in o.data.vertices:
  v.co.x*=rng.uniform(.85,1.2);v.co.y*=rng.uniform(.85,1.18);v.co.z*=rng.uniform(.7,1.0)
 o.scale=(1.25,1.0,.8);o.data.materials.append(rng.choice(stone))
def tree(x,y):
 trunk=[(x,y,.1),(x-.14,y,1.1),(x-.55,y,2.5),(x-1.15,y,3.65)]
 for a,b in zip(trunk,trunk[1:]):beam("bent trunk",a,b,.45 if a[2]<2 else .33,wood)
 for j in range(4):
  base=trunk[2] if j<2 else trunk[3]
  end=(x-1.8-j*.42,y+(-1)**j*.65,3.4+j*.25)
  beam("supporting branch",base,end,.20,wood)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=end)
  o=bpy.context.object;o.name="attached foliage";o.scale=(1.15,.85,.65)
  o.data.materials.append(leaf if j%2 else leaf2)
block("studio ground",(0,0,-.18),(39,25,.3),grass)
cottage(-11,1);wall(-3,-4)
for x,y in [(4,2),(6,4),(3,5),(8,1)]:rock(x,y)
for x,y in [(12,-2),(15,3)]:tree(x,y)
bpy.ops.object.camera_add(location=(25,-34,23));cam=bpy.context.object
cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO";cam.data.ortho_scale=37;scene.camera=cam
bpy.ops.object.light_add(type="SUN",location=(0,0,30));bpy.context.object.data.energy=2.3
scene.world.color=(.35,.43,.51)
scene.render.image_settings.file_format="PNG"
png=out/"map24_structural_kit.png";blend=out/"map24_structural_kit.blend"
scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [png,blend]}
(out/"map24_manifest.json").write_text(json.dumps({"task":"MAP24","seed":SEED,"status":"ART_QA_PENDING","source":"independent procedural primitives","runtime_integration":False,"canon_replacement":False,"files":files},indent=2))
print("MAP24 structural candidate generated")
