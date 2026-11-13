"""Aidan house: original Blender 4.x architectural candidate, not canon."""
import bpy, math, random, os, json, hashlib
from mathutils import Vector
rng=random.Random(1311)
out=os.environ.get("AIDAN_RENDER_OUTPUT","/tmp/aidan_home")
os.makedirs(out,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.cycles.samples=24
# Ubuntu apt Blender may be compiled without OpenImageDenoiser.
# Explicitly disable denoising on all view layers to avoid render abort.
for layer in sc.view_layers:
 layer.cycles.use_denoising=False
sc.render.resolution_x=1200
sc.render.resolution_y=900
sc.render.resolution_percentage=100
sc.render.film_transparent=True
sc.render.image_settings.file_format="PNG"
def mat(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
 m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*rgb,1)
 return m
stone=[mat("Limestone%02d"%i,(.32+i*.025,.31+i*.023,.28+i*.02)) for i in range(8)]
oak=[mat("Oak%02d"%i,(.16+i*.019,.09+i*.012,.05+i*.008)) for i in range(6)]
slate=[mat("Slate%02d"%i,(.16+i*.013,.18+i*.012,.17+i*.011)) for i in range(8)]
glass=mat("Amber_glass",(.52,.32,.13))
ground=mat("Grass",(.19,.27,.12))
def cube(name,xyz,scale,material,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz)
 ob=bpy.context.object;ob.name=name;ob.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 ob.data.materials.append(material)
 if bevel:
  mod=ob.modifiers.new("Weathered_edges","BEVEL");mod.width=bevel;mod.segments=2
  ob.modifiers.new("Weighted_normals","WEIGHTED_NORMAL")
 return ob
def organic_stone(name,xyz,scale,material):
 # Mesh vertex offsets are deterministic; retain an inward structural core.
 sx,sy,sz=scale
 verts=[]
 for zsign in (-1,1):
  for ysign in (-1,1):
   for xsign in (-1,1):
    verts.append((xsign*sx*.5+rng.uniform(-.035,.035),
                  ysign*sy*.5+rng.uniform(-.022,.022),
                  zsign*sz*.5+rng.uniform(-.014,.014)))
 faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
 ob.location=xyz;ob.data.materials.append(material)
 bevel=ob.modifiers.new("Soft_rock_edges","BEVEL");bevel.width=.018;bevel.segments=3
 ob.modifiers.new("Weighted_normals","WEIGHTED_NORMAL")
 ob["procedural_seed"]=1311
 return ob
def beam(name,a,b,thick,material):
 a,b=Vector(a),Vector(b)
 ob=cube(name,(a+b)/2,(thick,thick,(b-a).length),material)
 ob.rotation_euler=(b-a).to_track_quat("Z","Y").to_euler()
cube("Foundation",(0,0,.075),(8.3,6.7,.55),stone[4],.10)
# Structural roof/gable seam: solid triangular gables extend into roof skin.
# This is a closed profile, not a decorative beam or a flat bounding box.
def gable_mesh(name, y0, y1):
 profile=[(-3.92,.35),(3.92,.35),(3.92,3.48),(0,5.69),(-3.92,3.48)]
 verts=[(x,y,z) for y in (y0,y1) for x,z in profile]
 n=len(profile)
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
 faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
 ob.data.materials.append(stone[3]);ob["seam_overlap_m"]=.04
 return ob
gable_mesh("GABLE_FRONT",-3.17,-2.95)
gable_mesh("GABLE_REAR",2.95,3.17)
# Continuous roof substrate below the hand-laid slate tiles.
for sign in (-1,1):
 for i in range(12):
  t=(i+.5)/12
  x=sign*(.17+4.08*t);z=5.69-2.26*t
  ob=cube("ROOF_UNDERLAY",(x,0,z),(0.47,6.78,.14),slate[0],.012)
  ob.rotation_euler[1]=sign*.51
  ob["seam_overlap_m"]=.04
# Irregular staggered stonework with genuine openings on front wall.
for side in ("front","rear","left","right"):
 for row in range(11):
  z=.43+row*.26
  length=7.8 if side in ("front","rear") else 6.2
  cursor=-length/2+(-.23 if row%2 else 0)
  while cursor<length/2:
   span=min(rng.uniform(.43,.84),length/2-cursor)
   mid=cursor+span/2
   if span<.08:break
   opening=(side=="front" and ((abs(mid)<.73 and z<2.65) or (abs(abs(mid)-2.25)<.59 and 1.25<z<2.48)))
   if not opening:
    x,y=(mid,-3.1) if side=="front" else ((mid,3.1) if side=="rear" else ((-3.9,mid) if side=="left" else (3.9,mid)))
    dims=(span-.025,.32,.24) if side in ("front","rear") else (.32,span-.025,.24)
    organic_stone("Hand_set_stone",(x,y,z),dims,rng.choice(stone))
   cursor+=span
# Timber frame, ridge and rafters.
for x in (-3.72,3.72):
 for y in (-3.02,3.02):
  beam("Oak_corner_post",(x,y,.3),(x,y,3.5),.19,oak[2])
for y in (-3.08,3.08):
 for x in (-3.7,3.7):
  beam("Gable_rake",(x,y,3.45),(0,y,5.65),.20,oak[3])
beam("Ridge", (0,-3.5,5.65),(0,3.5,5.65),.19,oak[4])
for sign in (-1,1):
 for j in range(8):
  y=-3.25+j*.92
  beam("Roof_rafter",(0,y,5.62),(sign*4.3,y,3.20),.14,oak[3])
 # Individually overlapping roof slates in staggered rows.
 for row in range(14):
  t=(row+.5)/14
  x=sign*(.2+4.12*t)
  z=5.65-2.42*t
  for col in range(24):
   y=-3.44+(col+.5*(row%2))*.30
   ob=cube("Individual_roof_slate",(x,y,z),(.43,.35,.085),rng.choice(slate),.016)
   ob.rotation_euler[1]=sign*.51
# Door, window frame, chimney and lived-in architectural details.
cube("Solid_oak_door",(0,-3.30,1.38),(1.35,.13,2.48),oak[1],.05)
for x in (-2.25,2.25):
 cube("Window",(x,-3.31,1.88),(1.05,.10,1.08),glass,.015)
 beam("Window_mullion",(x,-3.40,1.35),(x,-3.40,2.43),.08,oak[4])
 beam("Window_transom",(x-.53,-3.40,1.88),(x+.53,-3.40,1.88),.08,oak[4])
for row in range(15):
 for j in range(4):
  theta=j*math.pi/2
  cube("Chimney_stone",(-2.6+.32*math.cos(theta),1.0+.32*math.sin(theta),3.2+row*.23),(.55,.55,.22),rng.choice(stone),.035)
cube("Chimney_cap",(-2.6,1,6.75),(1.12,1.12,.20),stone[2],.06)
for x in (-.9,.9):
 beam("Porch_post",(x,-4.0,.25),(x,-4.0,2.68),.18,oak[2])
 beam("Porch_brace",(x,-4,2.1),(x,-3.3,2.65),.14,oak[3])
cube("Porch_canopy",(0,-3.66,2.78),(2.35,1.3,.18),slate[4],.04)
for i in range(3):
 cube("Entrance_step",(0,-3.65-i*.34,.20-i*.065),(1.7+i*.2,.45,.17),stone[4],.06)
cube("Ground",(0,0,-.18),(19,17,.23),ground,.08)
for i in range(60):
 x,y=rng.uniform(-8,8),rng.uniform(-7,7)
 if abs(x)<4.4 and abs(y)<4.3:continue
 cube("Scattered_stone",(x,y,.02),(rng.uniform(.2,.6),rng.uniform(.2,.5),.15),rng.choice(stone),.05)
world=bpy.data.worlds.new("Soft_daylight")
sc.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
bpy.ops.object.light_add(type="AREA",location=(-6,-7,11))
bpy.context.object.data.energy=1700;bpy.context.object.data.size=8
# G0 runs on the generated geometry before any costly image rendering.
import sys
sys.path.insert(0,os.path.dirname(__file__))
from aidan_g0_preflight import inspect
inspect()
views={"front":(11,-14,9),"rear":(-11,14,9),"left":(-14,-8,9),"right":(14,8,9),"game":(12,-15,18)}
for name,location in views.items():
 bpy.ops.object.camera_add(location=location)
 cam=bpy.context.object;cam.name="Camera_"+name
 cam.rotation_euler=(Vector((0,0,2.8))-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO";cam.data.ortho_scale=16 if name=="game" else 14
 sc.camera=cam
 sc.render.filepath=os.path.join(out,"aidan_"+name+".png")
 bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,"aidan_candidate.blend"))
report={"status":"CANDIDATE_NOT_CANON","seed":1311,"blender":bpy.app.version_string,"views":{},"qa":{"G1":"PENDING","G2":"PENDING","G3":"RENDERED_NOT_INDEPENDENTLY_VERIFIED","G4":"NOT_RUN"}}
for name in views:
 p=os.path.join(out,"aidan_"+name+".png")
 report["views"][name]=hashlib.sha256(open(p,"rb").read()).hexdigest()
with open(os.path.join(out,"manifest.json"),"w") as f:json.dump(report,f,indent=2)
print("AIDAN_RENDER_COMPLETE",out)
