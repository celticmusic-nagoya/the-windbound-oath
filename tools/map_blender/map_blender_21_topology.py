"""MAP21-B: data-driven Rilde terrain, roads and cameras. Candidate only."""
import bpy,json,math,os,hashlib
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
data=json.loads((root/"map21_topology.json").read_text(encoding="utf-8"))
nodes={n["id"]:n for n in data["landmarks"]}
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"));out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
def mat(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
grass=mat("21 grass",(.29,.40,.24));trail=mat("21 footpaths",(.48,.36,.23));stone=mat("21 rock",(.42,.40,.35))
water=mat("21 water",(.15,.31,.41));timber=mat("21 timber",(.38,.27,.18));roof=mat("21 roofs",(.53,.25,.17));wall=mat("21 plaster",(.71,.64,.52))
def xy(id):return nodes[id]["xy"]
# Continuous river valley, northern hills, southwest cove and west sea cliff.
def terrain(x,y):
 ridge=4.2*math.exp(-((x+20)/5.8)**2)*math.exp(-((y-12)/20)**4)
 inland=.24*math.sin(.21*x)*math.cos(.16*y)
 river=-1.15*math.exp(-((x-16)/3.3)**2)
 coast=1.5/(1+math.exp((x+30)/2.8))
 inlet=-1.4*math.exp(-((x+27)/5)**2-((y+21)/7)**2)
 return ridge+inland+river+coast+inlet
# Walkable trail distance masks are derived from graph segments, not hardcoded coordinates.
segments=[(Vector((*xy(a),0)),Vector((*xy(b),0))) for a,b in data["edges"]]
def distance_path(x,y):
 p=Vector((x,y,0));best=1e9
 for a,b in segments:
  ab=b-a;t=max(0,min(1,(p-a).dot(ab)/max(1e-6,ab.length_squared)))
  best=min(best,(p-(a+t*ab)).length)
 return best
nx,ny=150,145
xs=[-45+90*i/(nx-1) for i in range(nx)]
ys=[-42+85*j/(ny-1) for j in range(ny)]
verts=[(x,y,terrain(x,y)) for y in ys for x in xs]
faces=[(j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i) for j in range(ny-1) for i in range(nx-1)]
mesh=bpy.data.meshes.new("MAP21 unified terrain");mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new("MAP21 unified terrain",mesh);bpy.context.collection.objects.link(obj)
for m in (grass,trail,stone):mesh.materials.append(m)
for p in mesh.polygons:
 x,y,_=p.center
 p.material_index=1 if distance_path(x,y)<1.1 else (2 if p.normal.z<.79 else 0)
 p.use_smooth=True
def cube(n,loc,dims,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
# Bridges and sea water are keyed by topology landmarks.
bx,by=xy("river_bridge");cube("MAP21 bridge",(bx,by,terrain(bx,by)+.5),(7,3,.5),timber)
cube("MAP21 eastern river",(16,0,-1.05),(3.5,82,.13),water)
cube("MAP21 western sea",(-50,0,-1.7),(16,95,.1),water)
# Provisional village houses. Later use modular building collection instances.
for i,id in enumerate(("aidan_home","village_square")):
 x,y=xy(id);x+=(-1 if i else 0);y+=(4 if i else 0);z=terrain(x,y)
 cube("MAP21 house "+id,(x,y,z+1.25),(3.3,3.0,2.5),wall)
 cube("MAP21 roof "+id,(x,y,z+2.8),(3.7,3.3,.55),roof)
def cam(name,loc,target,scale):
 bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.name=name
 c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
 c.data.type="ORTHO";c.data.ortho_scale=scale;return c
field=cam("MAP21 field camera",(37,-45,34),(0,0,0),55)
cx,cy=xy("sunset_view")
cliff=cam("MAP21 sunset camera",(cx-5,cy-9,12),(cx-22,cy+6,0),40)
bpy.ops.object.light_add(type="SUN",location=(0,0,40));bpy.context.object.data.energy=2
for c,name in ((field,"rilde_map21_field.png"),(cliff,"rilde_map21_cliff.png")):
 scene.camera=c;scene.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map21.blend"))
files=["rilde_map21_field.png","rilde_map21_cliff.png","rilde_map21.blend"]
report={"task":"MAP21-B","topology_sha256":hashlib.sha256((root/"map21_topology.json").read_bytes()).hexdigest(),"landmarks":len(nodes),"edges":len(segments),"field_render":"GENERATED","cliff_render":"GENERATED","event_occlusion":"NOT_VERIFIED","walkable_collision":"NOT_VERIFIED","art_qa":"NOT_RUN","sha256":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in files}}
(out/"map21_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("MAP21-B generated",len(nodes),"landmarks")
