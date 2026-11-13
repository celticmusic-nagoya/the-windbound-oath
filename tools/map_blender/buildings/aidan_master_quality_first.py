import bpy,math,random,os,json,hashlib
from pathlib import Path
from mathutils import Vector
random.seed(27)
root=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"))/"aidan_master";root.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
names=["01_Foundation","02_Walls_Timber","03_Roof_Thatch","04_Openings","05_Props_Life","06_Ground_Blend"]
C={}
for n in names:
 c=bpy.data.collections.new(n);bpy.context.scene.collection.children.link(c);C[n]=c
def mat(n,h,rough=.88):
 m=bpy.data.materials.new(n);m.use_nodes=True
 p=m.node_tree.nodes.get("Principled BSDF");rgb=tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
 p.inputs["Base Color"].default_value=(*rgb,1);p.inputs["Roughness"].default_value=rough
 noise=m.node_tree.nodes.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=45
 bump=m.node_tree.nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.14;bump.inputs["Distance"].default_value=.025
 m.node_tree.links.new(noise.outputs["Fac"],bump.inputs["Height"]);m.node_tree.links.new(bump.outputs["Normal"],p.inputs["Normal"])
 return m
M={k:mat(k,h) for k,h in {"stone":"#7A766E","plaster":"#DFD6C5","wood":"#4A3525","thatch":"#8C734B","straw_light":"#A68C5D","straw_dark":"#675335","earth":"#75644C","grass":"#596C3C","glass":"#456766","iron":"#302A25"}.items()}
def place(o,n,m,c):
 o.name=n;o.data.materials.append(M[m])
 for col in list(o.users_collection):col.objects.unlink(o)
 C[c].objects.link(o);return o
def cube(n,p,dim,m,c,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=dim
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);place(o,n,m,c)
 if bevel:
  b=o.modifiers.new("soft handmade edge","BEVEL");b.width=min(bevel,min(dim)*.22);b.segments=2
  o.modifiers.new("weighted normals","WEIGHTED_NORMAL")
 return o
def mesh(n,verts,faces,m,c):
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(n,me);C[c].objects.link(o);o.data.materials.append(M[m]);return o
def beam(n,a,b,width,m,c):
 a,b=Vector(a),Vector(b);o=cube(n,(a+b)*.5,(width,width,(b-a).length),m,c)
 o.rotation_euler=(b-a).to_track_quat("Z","Y").to_euler();return o
# Stone foundation: staggered irregular masonry rather than a monolithic box.
cube("earth skirt",(0,0,-.08),(6.4,5.4,.38),"earth","06_Ground_Blend")
for side in (-1,1):
 for row in range(2):
  for i in range(12):
   x=-2.85+i*.52+(row%2)*.10
   o=cube("handlaid stone",(x,side*2.52,.12+row*.2),(.48,.32,.20),"stone","01_Foundation",.07)
   o.rotation_euler.z=random.uniform(-.06,.06)
 for row in range(2):
  for i in range(9):
   y=-2.2+i*.54
   cube("side masonry",(side*3.02,y,.12+row*.2),(.29,.49,.2),"stone","01_Foundation",.05)
cube("floor",(0,0,.41),(5.8,4.8,.16),"wood","01_Foundation")
# Segmented plaster walls preserve actual door/window apertures.
z0=.4;top=2.6;front=-2.48
def wall(x0,x1,z1,z2):
 if x1>x0 and z2>z1:cube("plaster facade",((x0+x1)/2,front,(z1+z2)/2),(x1-x0,.15,z2-z1),"plaster","02_Walls_Timber")
for a,b in [(-3,-2.22),(-1.38,-.62),(.62,1.38),(2.22,3)]:wall(a,b,z0,top)
for x in (-1.8,1.8):
 wall(x-.42,x+.42,z0,1.35);wall(x-.42,x+.42,2.22,top)
wall(-.62,.62,2.48,top)
cube("rear plaster",(0,2.48,1.5),(6,.16,2.2),"plaster","02_Walls_Timber")
for x in (-2.95,2.95):cube("side plaster",(x,0,1.5),(.13,4.9,2.2),"plaster","02_Walls_Timber")
for x in (-2.9,2.9):
 for y in (-2.48,2.48):beam("timber post",(x,y,.42),(x,y,2.65),.19,"wood","02_Walls_Timber")
for y in (-2.5,2.5):
 beam("wall plate",(-3,y,2.62),(3,y,2.62),.19,"wood","02_Walls_Timber")
 for x in (-2.2,2.2):beam("diagonal brace",(x,y,1.55),(x+.55,y,2.5),.13,"wood","02_Walls_Timber")
# Roof geometry is an authored curved surface, not rotated cubes.
def roof_z(y):
 t=abs(y)/2.95
 return 4.8-2.15*t-.09*math.sin(math.pi*t)
for sign in (-1,1):
 verts=[];faces=[]
 for i in range(15):
  x=-3.38+i*6.76/14
  for j in range(15):
   y=sign*j*3.02/14
   verts.append((x,y,roof_z(y)+.035*math.sin(x*1.3)))
 for i in range(14):
  for j in range(14):
   a=i*15+j;faces.append((a,a+15,a+16,a+1))
 o=mesh("curved thatch roof",verts,faces,"thatch","03_Roof_Thatch")
 solid=o.modifiers.new("thatch thickness","SOLIDIFY");solid.thickness=.18
 for i in range(70):
  x=random.uniform(-3.2,3.2);y=sign*random.uniform(.3,2.96)
  a=(x,y,roof_z(y)+.12);b=(x+random.uniform(-.08,.08),y+sign*.32,roof_z(y+sign*.32)+.09)
  beam("loose straw bundle",a,b,random.uniform(.014,.028),"straw_light" if i%3 else "straw_dark","03_Roof_Thatch")
for i in range(22):
 x=-3.15+i*.30
 beam("hand-bound ridge straw",(x,0,4.84),(x+.13,.07,4.82),.07,"straw_light","03_Roof_Thatch")
cube("stone chimney",(1.8,.85,4.45),(.65,.65,1.65),"stone","03_Roof_Thatch")
cube("chimney cap",(1.8,.85,5.33),(.84,.84,.14),"stone","03_Roof_Thatch")
cube("oak door",(0,-2.58,1.48),(1.14,.13,2.06),"wood","04_Openings")
for x in (-1.8,1.8):
 cube("window glazing",(x,-2.56,1.79),(.75,.05,.79),"glass","04_Openings")
 for dx in (-.4,.4):cube("window frame",(x+dx,-2.65,1.79),(.10,.13,.94),"wood","04_Openings")
 for zz in (1.36,2.22):cube("window lintel",(x,-2.65,zz),(.90,.13,.10),"wood","04_Openings")
 cube("window crossbar",(x,-2.67,1.79),(.07,.12,.84),"wood","04_Openings")
cube("door step",(0,-3.05,.17),(1.55,.62,.25),"stone","01_Foundation")
for i in range(8):
 cube("stacked firewood",(-3.35+i*.14,1.55,.25),(.12,.75,.16),"wood","05_Props_Life")
for x,y in [(-3.5,-1.8),(3.45,-1.7),(-2.5,-3.5),(2.4,-3.5)]:
 for i in range(7):
  xx=x+random.uniform(-.35,.35);yy=y+random.uniform(-.35,.35)
  beam("grass tuft",(xx,yy,.03),(xx+.08,yy,.30+random.uniform(0,.15)),.025,"grass","06_Ground_Blend")
# Camera and outputs
sc=bpy.context.scene;sc.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.image_settings.file_format="PNG"
world=sc.world;world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Strength"].default_value=.7
sun=bpy.data.lights.new("warm sun","AREA");so=bpy.data.objects.new("warm sun",sun);sc.collection.objects.link(so);so.location=(-6,-8,11);sun.energy=1800;sun.size=8
cam=bpy.data.cameras.new("game camera");co=bpy.data.objects.new("game camera",cam);sc.collection.objects.link(co);sc.camera=co;cam.type="ORTHO";cam.ortho_scale=11.5
for name,loc in [("game_view",(9,-12,10)),("front",(0,-14,5)),("side",(14,0,5)),("rear",(0,14,5))]:
 co.location=loc;co.rotation_euler=(Vector((0,0,2.3))-co.location).to_track_quat("-Z","Y").to_euler()
 sc.render.filepath=str(root/("aidan_"+name+".png"));bpy.ops.render.render(write_still=True)
blend=root/"aidan_master.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob("*") if p.suffix in (".png",".blend")}
(root/"manifest.json").write_text(json.dumps({"status":"CANDIDATE_ART_QA_PENDING","collections":names,"files":files},indent=2))
