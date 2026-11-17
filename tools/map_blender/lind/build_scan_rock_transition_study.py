"""Noncanonical boundary-attached rock transition mesh study; never changes source scan."""
import argparse,bpy,sys,collections,json,hashlib,math
from pathlib import Path
from mathutils import Vector
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--source-blend",required=True);p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:]);out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 source=Path(a.source_blend).resolve();bpy.ops.wm.open_mainfile(filepath=str(source))
 obj=bpy.data.objects["SCAN_LED_OPEN_SURFACE_NOT_PRODUCTION"];mesh=obj.data
 original=(len(mesh.vertices),len(mesh.polygons))
 owners=collections.Counter()
 for poly in mesh.polygons:
  v=list(poly.vertices)
  for x,y in zip(v,v[1:]+v[:1]):owners[tuple(sorted((x,y)))]+=1
 boundary=[e for e,c in owners.items() if c==1]
 neighbors=collections.defaultdict(set)
 for x,y in boundary:neighbors[x].add(y);neighbors[y].add(x)
 assert len(boundary)==462 and all(len(v)==2 for v in neighbors.values())
 start=min(neighbors);ordered=[start];prev=None;cur=start
 while True:
  candidates=sorted(neighbors[cur]-({prev} if prev is not None else set()))
  nxt=candidates[0]
  if nxt==start:break
  assert nxt not in ordered
  ordered.append(nxt);prev,cur=cur,nxt
 assert len(ordered)==len(boundary)
 points=[mesh.vertices[i].co.copy() for i in ordered];n=len(points)
 center=sum(points,Vector((0,0,0)))/n
 span=max(max(v[k] for v in points)-min(v[k] for v in points) for k in range(3))
 # Author a separate layered join with deterministic locally varying stone buttress widths.
 # The join is NOT a final geologic design, only a measured attachment test.
 vertices=[];rings=[]
 for layer in range(3):
  ids=[]
  for i,v in enumerate(points):
   radial=Vector((v.x-center.x,v.y-center.y,0))
   if radial.length<1e-6:radial=Vector((1,0,0))
   radial.normalize()
   # small underlap at attachment, outward irregular rock support, lowered foot
   if layer==0:
    p=v+radial*(-.012*span)+Vector((0,0,-.004*span))
   elif layer==1:
    w=.065*span*(1+.14*math.sin(i*.43)+.09*math.sin(i*.17+1.2))
    p=v+radial*w+Vector((0,0,-.06*span))
   else:
    w=.11*span*(1+.10*math.sin(i*.27+.5)+.08*math.sin(i*.11))
    p=v+radial*w+Vector((0,0,-.14*span))
   ids.append(len(vertices));vertices.append(tuple(p))
  rings.append(ids)
 faces=[]
 for a,b in zip(rings,rings[1:]):
  for i in range(n):j=(i+1)%n;faces.append((a[i],a[j],b[j],b[i]))
 new=bpy.data.meshes.new("ROCK_TRANSITION_SEPARATE_MESH_STUDY")
 new.from_pydata(vertices,[],faces);new.update()
 transition=bpy.data.objects.new("ROCK_TRANSITION_NOT_PRODUCTION",new)
 bpy.context.collection.objects.link(transition)
 mat=bpy.data.materials.new("QA_TRANSITION_WARM_ROCK");mat.diffuse_color=(.42,.32,.23,1);new.materials.append(mat)
 obj.hide_render=False
 assert original==(len(mesh.vertices),len(mesh.polygons))
 scene=bpy.context.scene
 scene.render.engine="BLENDER_WORKBENCH";scene.display.shading.color_type="MATERIAL";scene.display.shading.light="STUDIO";scene.display.shading.show_cavity=True
 scene.render.resolution_x=1100;scene.render.resolution_y=760;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format="PNG";scene.render.filepath=str(out/"rock_transition_study.png")
 bpy.ops.render.render(write_still=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(out/"rock_transition_study.blend"))
 assert original==(len(mesh.vertices),len(mesh.polygons))
 metrics={"source_sha256":sha(source),"source_vertices":original[0],"source_faces":original[1],"source_unchanged":True,"boundary_edges":n,"transition_vertices":len(vertices),"transition_quads":len(faces),"separate_transition_object":True,"open_ends":True,"not_collision":True,"not_production":True,"render_sha256":sha(out/"rock_transition_study.png"),"blend_sha256":sha(out/"rock_transition_study.blend"),"G1":"BLOCKED","G2":"NOT_RUN","G3":"ATTACHMENT_GEOMETRY_CREATED","G4":"NOT_RUN"}
 (out/"rock_transition_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
 print("TRANSITION_MESH_CREATED",json.dumps(metrics),flush=True)
if __name__=="__main__":main()
