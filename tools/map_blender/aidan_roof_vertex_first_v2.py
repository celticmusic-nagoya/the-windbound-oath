"""Vertex-first slate roof candidate v2. Geometry and spacing before material detail.
Blender 4.x/5.x. Independent collection, deterministic, no canon replacement.
"""
import bpy, math, random, json
from mathutils import Vector
SEED=1311
NAME="AIDAN_ROOF_VERTEX_FIRST_V2"
rng=random.Random(SEED)
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*c,1)
 m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.82
 return m
def mesh(c,name,vertices,faces,material):
 me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);c.objects.link(ob);ob.data.materials.append(material);return ob
def build():
 if bpy.data.collections.get(NAME):raise RuntimeError("Never overwrite prior candidate")
 c=bpy.data.collections.new(NAME);bpy.context.scene.collection.children.link(c)
 slates=[mat("v2 slate %02d"%i,v) for i,v in enumerate([(0.25,.30,.34),(.29,.35,.39),(.32,.38,.42),(.26,.32,.37)])]
 timber=mat("v2 dark timber",(.20,.15,.12))
 length=8.4; span=3.55; eave=3.05; ridge=6.60
 # Fix the architectural control vertices FIRST. 4 per plane; all other geometry derives from them.
 controls={}
 for side in (-1,1):
  controls[str(side)]=[[-length/2,0,ridge],[length/2,0,ridge],
                       [length/2,side*span,eave],[-length/2,side*span,eave]]
  mesh(c,"roof substrate "+str(side),controls[str(side)],[(0,1,2,3)],slates[0])
 # Every slate is a real closed 3D prism with a pitched underside and positive normal clearance.
 # Course overlap is 30% and the next course starts upslope from previous lower edge.
 count=0;min_clearance=1e9
 rows=14; pitch=span/rows; tiles=14
 for side in (-1,1):
  for row in range(rows):
   ytop=row*pitch; ybottom=min(span+.10,ytop+pitch*1.32)
   offset=(.5 if row%2 else 0)*length/tiles
   for col in range(-1,tiles+1):
    xa=-length/2+col*length/tiles+offset
    xb=xa+length/tiles*.985
    xa=max(-length/2,xa);xb=min(length/2,xb)
    if xb-xa<.08:continue
    # z on slope, +clearance avoids coplanar fighting. Thickness creates a visible eave.
    lift=.040+.004*(rows-row)/rows
    thickness=.026+rng.uniform(-.003,.004)
    z=lambda y:ridge-(ridge-eave)*y/span
    verts=[]
    for up in (0,1):
     h=lift+(thickness if up else 0)
     verts.extend([(xa,side*ytop,z(ytop)+h),(xb,side*ytop,z(ytop)+h),
                   (xb,side*ybottom,z(ybottom)+h),(xa,side*ybottom,z(ybottom)+h)])
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh(c,"slate %s %02d %02d"%(side,row,col),verts,faces,rng.choice(slates))
    count+=1;min_clearance=min(min_clearance,lift)
 # Full length timber fascia: structurally continuous.
 for side in (-1,1):
  y=side*(span+.12);z=eave-.12
  mesh(c,"fascia "+str(side),[(-4.3,y,z),(4.3,y,z),(4.3,y,z+.16),(-4.3,y,z+.16)],[(0,1,2,3)],timber)
 result={"status":"VERTEX_FIRST_GEOMETRY_CANDIDATE_NOT_ART_APPROVED","seed":SEED,
         "control_vertices":controls,"tiles":count,"minimum_surface_clearance":min_clearance,
         "tile_thickness":"0.023-0.030 normalized units","course_overlap":.32}
 print("VERTEX_FIRST_QA="+json.dumps(result,sort_keys=True))
 return result
if __name__=="__main__":build()
