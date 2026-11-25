"""MAP21-D visual structure candidate: replace straight river and faceted paths.
Consumes MAP21-B blend; keeps earlier stages immutable.
"""
import bpy,os,math,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"));out.mkdir(parents=True,exist_ok=True)
source=out/"rilde_map21.blend"
assert source.is_file(),"MAP21-B source blend missing"
bpy.ops.wm.open_mainfile(filepath=str(source))
d=json.loads((root/"map21_topology.json").read_text())
nodes={x["id"]:x["xy"] for x in d["landmarks"]}
def mat(name,c):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
 m.diffuse_color=(*c,1);return m
river_mat=mat("MAP21D muted river",(.13,.29,.36))
path_mat=mat("MAP21D warm earth",(.43,.33,.22))
for o in bpy.data.objects:
 if o.name in ("MAP21 eastern river","MAP21 western sea"):o.hide_render=True
# Meandering river: narrow triangulated ribbon with no axis-aligned rectangular edge.
verts=[];faces=[]
steps=140
for i in range(steps+1):
 y=-41+i*82/steps
 x=16+.7*math.sin(y*.13)+.32*math.sin(y*.37)
 w=1.65+.18*math.sin(y*.24)
 verts.extend([(x-w,y,-.95),(x+w,y,-.95)])
 if i: 
  j=2*i;faces.append((j-2,j-1,j+1,j))
mesh=bpy.data.meshes.new("MAP21D river ribbon");mesh.from_pydata(verts,[],faces);mesh.materials.append(river_mat);mesh.update()
obj=bpy.data.objects.new("MAP21D river ribbon",mesh);bpy.context.collection.objects.link(obj)
# Paths are smooth curves, with mild curvature between connected landmarks.
# This is a rendering prototype; traversability remains unverified.
for k,(a,b) in enumerate(d["edges"]):
 x1,y1=nodes[a];x2,y2=nodes[b]
 if math.hypot(x2-x1,y2-y1)<1:continue
 curve=bpy.data.curves.new("MAP21D path curve","CURVE");curve.dimensions="3D"
 curve.resolution_u=18;curve.bevel_depth=.52;curve.bevel_resolution=2
 spline=curve.splines.new("BEZIER");spline.bezier_points.add(2)
 mx,my=(x1+x2)/2,(y1+y2)/2
 dx,dy=x2-x1,y2-y1
 points=[(x1,y1),(mx-.07*dy,my+.07*dx),(x2,y2)]
 for p,(x,y) in zip(spline.bezier_points,points):
  p.co=(x,y,.28);p.handle_left_type="AUTO";p.handle_right_type="AUTO"
 o=bpy.data.objects.new("MAP21D path %02d"%k,curve);bpy.context.collection.objects.link(o)
 curve.materials.append(path_mat)
# Keep canonical field camera and record independent renders.
scene=bpy.context.scene
names=[]
for camname,filename in (("MAP21 field camera","rilde_map21d_field.png"),("MAP21 sunset camera","rilde_map21d_cliff.png")):
 scene.camera=bpy.data.objects[camname];scene.render.filepath=str(out/filename)
 bpy.ops.render.render(write_still=True);names.append(filename)
blend="rilde_map21d.blend";bpy.ops.wm.save_as_mainfile(filepath=str(out/blend));names.append(blend)
report={"task":"MAP21-D","source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
"rendered":2,"river":"MEANDERING_RIBBON","paths":"SMOOTH_CURVES",
"route_collision":"NOT_VERIFIED","cinematic_occlusion":"NOT_VERIFIED",
"art_qa":"NOT_RUN","files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map21d_report.json").write_text(json.dumps(report,indent=2))
print("MAP21-D candidate rendered")
