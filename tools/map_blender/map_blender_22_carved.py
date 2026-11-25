"""MAP22 structural terrain: one mesh with carved river and road masks.
Independent candidate; no MAP21-D overlay objects or runtime changes.
"""
import bpy,math,os,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
d=json.loads((root/"map21_topology.json").read_text())
nodes={n["id"]:n["xy"] for n in d["landmarks"]}
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"));out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
grass=material("MAP22 meadow",(.29,.41,.27))
earth=material("MAP22 path",(.46,.34,.23))
stone=material("MAP22 stone",(.43,.41,.36))
water=material("MAP22 water",(.13,.29,.39))
# River centerline and bank profile are used by BOTH terrain and water surface.
def river_x(y):return 16+.65*math.sin(y*.13)+.3*math.sin(y*.37)
def river_distance(x,y):return abs(x-river_x(y))
def smoothstep(a,b,t):
 v=max(0,min(1,(t-a)/(b-a)));return v*v*(3-2*v)
def terrain(x,y):
 ridge=4.2*math.exp(-((x+20)/5.8)**2)*math.exp(-((y-12)/20)**4)
 hills=.25*math.sin(.19*x)*math.cos(.15*y)
 coast=1.45/(1+math.exp((x+31)/2.5))
 inlet=-1.35*math.exp(-((x+27)/5)**2-((y+21)/7)**2)
 dist=river_distance(x,y)
 # Carved channel: flat bed within 1.6, tapered banks out to 4.2
 cut=1.55*(1-smoothstep(1.5,4.2,dist))
 return ridge+hills+coast+inlet-cut
edges=[(nodes[a],nodes[b]) for a,b in d["edges"]]
def path_distance(x,y):
 best=1e8
 for (ax,ay),(bx,by) in edges:
  dx,dy=bx-ax,by-ay
  t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/max(.0001,dx*dx+dy*dy)))
  best=min(best,math.hypot(x-ax-t*dx,y-ay-t*dy))
 return best
nx,ny=221,201
xs=[-47+i*96/(nx-1) for i in range(nx)]
ys=[-44+j*90/(ny-1) for j in range(ny)]
vs=[(x,y,terrain(x,y)) for y in ys for x in xs]
fs=[(j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i) for j in range(ny-1) for i in range(nx-1)]
mesh=bpy.data.meshes.new("MAP22 carved terrain");mesh.from_pydata(vs,[],fs);mesh.update()
ob=bpy.data.objects.new("MAP22 carved terrain",mesh);bpy.context.collection.objects.link(ob)
for m in (grass,earth,stone):mesh.materials.append(m)
for face in mesh.polygons:
 x,y,_=face.center
 # Road is a FLAT surface material on terrain, not a beveled tube.
 face.material_index=1 if path_distance(x,y)<1.35 and river_distance(x,y)>2.3 else (2 if face.normal.z<.78 else 0)
 face.use_smooth=True
# Water ribbon conforms to river centerline at the carved channel water level.
v=[];f=[]
for j in range(241):
 y=-43+j*88/240;x=river_x(y)
 for side in (-1,1):v.append((x+side*1.5,y,-1.13))
 if j:
  k=j*2;f.append((k-2,k-1,k+1,k))
wm=bpy.data.meshes.new("MAP22 river surface");wm.from_pydata(v,[],f);wm.update();wm.materials.append(water)
wo=bpy.data.objects.new("MAP22 river surface",wm);bpy.context.collection.objects.link(wo)
# Western sea: horizon-facing broad plane, not a river cube.
bpy.ops.mesh.primitive_plane_add(size=2,location=(-56,0,-1.35))
sea=bpy.context.object;sea.name="MAP22 open sea";sea.scale=(23,65,1);sea.data.materials.append(water)
# Provisional wooden bridge centered on the data-defined river crossing.
bx,by=nodes["river_bridge"]
bpy.ops.mesh.primitive_cube_add(size=1,location=(river_x(by),by,.6))
bridge=bpy.context.object;bridge.name="MAP22 bridge provisional";bridge.dimensions=(9,3,.35)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bridge.data.materials.append(earth)
def cam(name,location,target,scale):
 bpy.ops.object.camera_add(location=location);o=bpy.context.object;o.name=name
 o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
 o.data.type="ORTHO";o.data.ortho_scale=scale;return o
field=cam("MAP22 field",(35,-45,33),(0,0,0),57)
cx,cy=nodes["sunset_view"]
# Sea-facing camera intentionally points west; check render, do not claim art acceptance.
cliff=cam("MAP22 sunset sea-facing",(cx+5,cy-11,10),(cx-24,cy+8,-1),46)
bpy.ops.object.light_add(type="SUN",location=(0,0,40));bpy.context.object.data.energy=2
names=[]
for c,name in ((field,"rilde_map22_field.png"),(cliff,"rilde_map22_cliff.png")):
 scene.camera=c;scene.render.filepath=str(out/name);bpy.ops.render.render(write_still=True);names.append(name)
blend="rilde_map22.blend";bpy.ops.wm.save_as_mainfile(filepath=str(out/blend));names.append(blend)
# Numeric structural gates are distinct from unverified cinematic and gameplay checks.
assert terrain(river_x(0),0)<terrain(river_x(0)+5,0)-.9
assert all(abs(v[2]+1.13)<1e-6 for v in wo.data.vertices)
report={"task":"MAP22","status":"STRUCTURAL_CANDIDATE","carved_river":"PASS","water_level":"PASS",
"roads":"TERRAIN_MATERIAL_NO_TUBES","event_occlusion":"NOT_VERIFIED",
"navigation_collision":"NOT_VERIFIED","art_qa":"NOT_RUN",
"files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map22_report.json").write_text(json.dumps(report,indent=2))
print("MAP22 structural checks PASS")
