"""MAP20: independent unified heightfield prototype. Does not modify runtime maps."""
import bpy,math,os,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.world.color=(.23,.29,.34)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
grass=mat("MAP20 muted meadow",(.30,.41,.25));soil=mat("MAP20 earthen trail",(.47,.36,.23))
rock=mat("MAP20 coastal rock",(.37,.35,.32));water=mat("MAP20 water",(.13,.30,.39))
wall=mat("MAP20 plaster",(.68,.58,.44));wood=mat("MAP20 timber",(.36,.26,.18));roof=mat("MAP20 clay tile",(.52,.22,.14))
# A continuous field replaces all independent terrain cubes. Coordinates are provisional.
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def height(x,y):
 # low coastal rises with a continuous saddle; smooth rather than a rectangular wall
 ridge_x=-14+.8*math.sin(y*.16)
 ridge=5.2*math.exp(-((x-ridge_x)/4.6)**2)*math.exp(-((y-9)/16)**4)
 coast=2.0*smooth((-x-18)/9)*smooth((y+13)/9)
 south=.32*math.sin(x*.19)*math.sin(y*.17)
 # river valley along eastern side
 valley=1.0*math.exp(-((x-16)/4.5)**2)
 return ridge+coast+south-valley
nx,ny=131,121
xs=[-39+i*75/(nx-1) for i in range(nx)]
ys=[-30+j*61/(ny-1) for j in range(ny)]
vs=[(x,y,height(x,y)) for y in ys for x in xs]
faces=[]
for j in range(ny-1):
 for i in range(nx-1):
  a=j*nx+i;faces.append((a,a+1,a+nx+1,a+nx))
mesh=bpy.data.meshes.new("MAP20 unified terrain");mesh.from_pydata(vs,[],faces);mesh.update()
obj=bpy.data.objects.new("MAP20 unified terrain",mesh);bpy.context.collection.objects.link(obj)
for m in (grass,soil,rock):mesh.materials.append(m)
for p in mesh.polygons:
 p.use_smooth=True
 cx,cy,cz=p.center
 path=(abs(cx)<1.8 and cy>4) or (abs(cy)<2.2 and -8<cx<17)
 p.material_index=1 if path and cz<1.4 else (2 if p.normal.z<.76 else 0)
def cube(n,xyz,dim,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz)
 o=bpy.context.object;o.name=n;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o
# The river is in a shallow valley; bridge crosses its narrowest route.
cube("MAP20 river", (16,0,-.88),(4.3,59,.12),water)
cube("MAP20 timber bridge",(16,2,.12),(6.5,2.4,.34),wood)
# Irregular homes with pitched roofs; positions are provisional.
houses=[(-7,5,0.1),(-4,9,-.15),(6,8,.15),(10,0,-.12),(-7,-7,.18),(4,-8,-.15)]
for i,(x,y,a) in enumerate(houses):
 z=height(x,y)
 o=cube("MAP20 home %02d"%i,(x,y,z+1.2),(2.8,2.7,2.4),wall if i%2 else wood);o.rotation_euler.z=a
 roofmesh=bpy.data.meshes.new("MAP20 roof mesh %02d"%i)
 verts=[(-1.7,-1.55,2.3),(1.7,-1.55,2.3),(0,-1.55,3.5),(-1.7,1.55,2.3),(1.7,1.55,2.3),(0,1.55,3.5)]
 roofmesh.from_pydata(verts,[],[(0,1,2),(3,5,4),(0,2,5,3),(2,1,4,5)]);roofmesh.update()
 r=bpy.data.objects.new("MAP20 gable %02d"%i,roofmesh);bpy.context.collection.objects.link(r)
 r.location=(x,y,z);r.rotation_euler.z=a;roofmesh.materials.append(roof)
# A separate sea surface is placed west of the coastal shelf.
cube("MAP20 western sea",(-46,0,-1.7),(18,70,.1),water)
def camera(n,pos,target,scale):
 bpy.ops.object.camera_add(location=pos);o=bpy.context.object;o.name=n
 o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 o.data.type='ORTHO';o.data.ortho_scale=scale;return o
field=camera("MAP20 field preview",(35,-47,31),(0,0,0),54)
cliff=camera("MAP20 cliff provisional",(-29,17,9),(-12,4,1),32)
bpy.ops.object.light_add(type='SUN',location=(0,0,25));bpy.context.object.data.energy=2
# Reuse the provisional nine sample positions; their suitability for story events is unverified.
bvh=BVHTree.FromPolygons([Vector(v) for v in vs],faces,all_triangles=False)
observers=[(-21,8,5.2),(-20,10,5.2),(-19,12,5.2)]
targets=[(-8,4,3),(0,2,2.5),(6,6,3)]
hits=[]
for a in observers:
 for b in targets:
  d=Vector(b)-Vector(a)
  hits.append(bvh.ray_cast(Vector(a),d.normalized(),d.length)[0] is not None)
scene.camera=field;scene.render.filepath=str(out/"rilde_map20_field.png");bpy.ops.render.render(write_still=True)
scene.camera=cliff;scene.render.filepath=str(out/"rilde_map20_cliff.png");bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map20.blend"))
names=("rilde_map20_field.png","rilde_map20_cliff.png","rilde_map20.blend")
report={"task":"MAP-BLENDER-20","status":"INDEPENDENT_HEIGHTFIELD_CANDIDATE","synthetic_occlusion":{"blocked":sum(hits),"total":9},"cinematic_occlusion":"NOT_VERIFIED","route_connectivity":"NOT_VERIFIED","visual_qa":"NOT_RUN","runtime_modified":False,"files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map20_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"MAP20_occlusion":sum(hits),"rendered":2}))
