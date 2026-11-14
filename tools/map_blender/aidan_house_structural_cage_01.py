"""Aidan house structural cage v1 — approved visual target, dimensions CANDIDATE.
No canon dimensions inferred from image. Blender 4.x/5.x.
"""
import bpy, json, math
from mathutils import Vector
NAME="AIDAN_HOUSE_STRUCTURE_CANDIDATE_01"
D={"length":8.4,"width":7.1,"foundation_z":0.0,"wall_top":3.05,"ridge_z":6.60,
   "wall_thickness":0.38,"door_width":1.25,"door_height":2.15,"roof_overhang":0.32}
def make_mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*color,1)
 return m
def add_mesh(col,name,vs,fs,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(mat);return ob
def box(col,name,x0,x1,y0,y1,z0,z1,mat):
 v=[(x,y,z) for z in (z0,z1) for y in (y0,y1) for x in (x0,x1)]
 f=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
 return add_mesh(col,name,v,f,mat)
def build():
 if bpy.data.collections.get(NAME):raise RuntimeError("Refuse to overwrite candidate")
 c=bpy.data.collections.new(NAME);bpy.context.scene.collection.children.link(c)
 stone=make_mat("cage stone placeholder",(.55,.51,.44))
 wood=make_mat("cage timber placeholder",(.31,.22,.16))
 opening=make_mat("cage openings placeholder",(.18,.15,.12))
 roof=make_mat("cage slate placeholder",(.27,.33,.39))
 L=D["length"]/2;W=D["width"]/2;T=D["wall_thickness"];H=D["wall_top"];R=D["ridge_z"]
 anchors={"foundation":[[-L,-W,0],[L,-W,0],[L,W,0],[-L,W,0]],
          "wall_top":[[-L,-W,H],[L,-W,H],[L,W,H],[-L,W,H]],
          "ridge":[[-L,0,R],[L,0,R]],
          "entrance_center":[0,-W,0],"chimney":"UNRESOLVED_CANDIDATE"}
 box(c,"stone foundation",-L,L,-W,W,-.30,0,stone)
 # Door opening physically reserved on south wall; no coplanar facade patch.
 door=D["door_width"]/2
 box(c,"front stone left",-L,-door,-W,-W+T,0,H,stone)
 box(c,"front stone right",door,L,-W,-W+T,0,H,stone)
 box(c,"front stone lintel",-door,door,-W,-W+T,D["door_height"],H,stone)
 box(c,"rear stone",-L,L,W-T,W,0,H,stone)
 box(c,"west stone",-L,-L+T,-W+T,W-T,0,H,stone)
 box(c,"east stone",L-T,L,-W+T,W-T,0,H,stone)
 for x in (-L,L):
  for y in (-W,W):
   box(c,"timber corner %s %s"%(x,y),x-.13,x+.13,y-.13,y+.13,0,H+.18,wood)
 for x in (-L,L):
  box(c,"eave beam %s"%x,x-.13,x+.13,-W-.30,W+.30,H-.17,H+.10,wood)
 # Roof cage: two continuous pitched deck surfaces with deliberate overhang.
 oh=D["roof_overhang"];yr=W+oh
 for side in (-1,1):
  vertices=[(-L-oh,0,R),(L+oh,0,R),(L+oh,side*yr,H-.08),(-L-oh,side*yr,H-.08)]
  add_mesh(c,"pitched roof cage %s"%side,vertices,[(0,1,2,3)],roof)
 # Real doorway recess and frame, not an image pasted on stone.
 box(c,"door leaf",-door+.08,door-.08,-W+.08,-W+.18,.04,D["door_height"]-.08,wood)
 for x in (-door,door):
  box(c,"door jamb %s"%x,x-.08,x+.08,-W-.10,-W+.23,0,D["door_height"]+.15,wood)
 box(c,"door header",-door-.09,door+.09,-W-.10,-W+.23,D["door_height"],D["door_height"]+.18,wood)
 result={"status":"WHOLE_HOUSE_STRUCTURE_CANDIDATE_NOT_ART_APPROVED","dimensions_candidate":D,
         "anchors":anchors,"objects":len(c.objects),"windows":"UNRESOLVED_CANDIDATE",
         "chimney":"UNRESOLVED_CANDIDATE","pbr":"NOT_APPLIED","uv":"NOT_RUN"}
 print("AIDAN_STRUCTURE_QA="+json.dumps(result,sort_keys=True))
 return result
if __name__=="__main__":build()
