"""MAP23 independent original modular asset kit. No third-party source geometry."""
import bpy,math,random,json,os,hashlib
from pathlib import Path
from mathutils import Vector
SEED=2301;random.seed(SEED)
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"));out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
def mat(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
wall=mat("warm limewashed plaster",(.70,.64,.48));timber=mat("weathered timber",(.29,.20,.14))
roof=mat("red brown slate",(.43,.19,.13));rock=mat("coastal grey stone",(.39,.42,.38))
moss=mat("moss",(.24,.38,.22));leaves=mat("windward foliage",(.27,.42,.25))
ground=mat("meadow",(.32,.43,.27))
def cube(name,loc,scale,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name
 o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new("soft edge","BEVEL");mod.width=bevel;mod.segments=2
  o.modifiers.new("weighted normals","WEIGHTED_NORMAL")
 return o
def cottage(x,y):
 cube("original cottage plaster",(x,y,1.65),(5.8,4.6,3.3),wall,.10)
 for dx in (-2.7,2.7):
  for dy in (-2.05,2.05):
   cube("timber corner",(x+dx,y+dy,1.7),(.22,.22,3.5),timber,.04)
 for z in (.35,3.05):
  cube("timber horizontal",(x,y-2.33,z),(5.8,.24,.2),timber,.03)
 # Roof is made from original prism geometry, not an imported mesh.
 verts=[(x-3.3,y-2.8,3.1),(x+3.3,y-2.8,3.1),(x,y-2.8,5.0),
        (x-3.3,y+2.8,3.1),(x+3.3,y+2.8,3.1),(x,y+2.8,5.0)]
 faces=[(0,1,2),(3,5,4),(0,3,4,1),(0,2,5,3),(1,4,5,2)]
 mesh=bpy.data.meshes.new("roof prism");mesh.from_pydata(verts,[],faces);mesh.materials.append(roof);mesh.update()
 obj=bpy.data.objects.new("original gabled roof",mesh);bpy.context.collection.objects.link(obj)
 cube("timber door",(x,y-2.39,1.05),(1.1,.12,2.1),timber,.03)
def wallstones(x,y):
 for i in range(12):
  px=x+i*.77
  for row in range(3):
   w=random.uniform(.56,.78);h=random.uniform(.35,.52)
   cube("individual fieldstone",(px+random.uniform(-.08,.08),y,row*.47+.2),(w,.65,h),rock,.07)
def boulder(x,y,z=0):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,z+.75))
 o=bpy.context.object;o.name="original coastal rock"
 o.scale=(random.uniform(.9,1.5),random.uniform(.8,1.4),random.uniform(.55,.95))
 o.data.materials.append(rock)
def tree(x,y):
 cube("wind-bent trunk",(x,y,1.7),(.48,.52,3.4),timber,.12)
 for i in range(4):
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x-1.1-i*.4,y+(-1)**i*.35,3.8+i*.3))
  o=bpy.context.object;o.name="wind-shaped foliage";o.scale=(1.25,1.0,.65);o.data.materials.append(leaves)
cube("asset studio ground",(0,0,-.2),(39,25,.3),ground,.05)
cottage(-11,1);wallstones(-3,-4)
for x,y in [(4,2),(6,4),(3,5),(8,1)]:boulder(x,y)
for x,y in [(12,-2),(15,3)]:tree(x,y)
bpy.ops.object.camera_add(location=(25,-34,23));camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.type="ORTHO";camera.data.ortho_scale=37;scene.camera=camera
bpy.ops.object.light_add(type="SUN",location=(0,0,30));bpy.context.object.data.energy=2
scene.world.color=(.35,.43,.51)
scene.render.image_settings.file_format="PNG";scene.render.filepath=str(out/"map23_original_kit.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"map23_original_kit.blend"))
files=["map23_original_kit.png","map23_original_kit.blend"]
(out/"map23_manifest.json").write_text(json.dumps({"task":"MAP23","seed":SEED,"status":"ORIGINAL_CANDIDATE","third_party_meshes":0,"art_qa":"NOT_RUN","runtime_integration":False,"files":{f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in files}},indent=2))
print("MAP23 original kit generated")
