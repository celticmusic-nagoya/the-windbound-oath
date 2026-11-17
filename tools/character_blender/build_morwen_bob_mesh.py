#!/usr/bin/env python3
"""Convert existing 33 hair guides into a renderable, editable hair-mesh candidate.

Produces individual tapered ribbon surfaces (not curves-as-finished-assets).
A visual/art QA PASS is never inferred from successful geometry generation.
"""
import argparse,hashlib,json,pathlib,math
import bpy
from mathutils import Vector

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--stage",required=True);p.add_argument("--output",required=True)
 a=p.parse_args();src=pathlib.Path(a.stage).resolve();out=pathlib.Path(a.output).resolve()
 if not src.is_file() or src==out or out.is_relative_to(src):raise SystemExit("BLOCKED invalid paths")
 sha=hashlib.sha256(src.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 body=bpy.data.objects.get("MORWEN_PROPORTION_STAGE_UNAPPROVED")
 guides=sorted([o for o in bpy.data.objects if o.name.startswith(("bob_guide_","fringe_guide_"))])
 if body is None or body.type!="MESH" or len(guides)!=33:raise SystemExit("BLOCKED missing source stage/guides")
 collection=bpy.data.collections.new("MORWEN_HAIR_MESH_CANDIDATE_UNAPPROVED")
 bpy.context.scene.collection.children.link(collection)
 mat=bpy.data.materials.new("Morwen_deep_violet_hair_CANDIDATE")
 mat.use_nodes=True;bsdf=mat.node_tree.nodes.get("Principled BSDF")
 bsdf.inputs["Base Color"].default_value=(.15,.065,.24,1)
 bsdf.inputs["Roughness"].default_value=.42
 mat.diffuse_color=(.15,.065,.24,1)
 records=[]
 for guide in guides:
  spline=guide.data.splines[0]
  pts=[p.co.copy() for p in spline.bezier_points]
  if len(pts)!=3:raise SystemExit("BLOCKED unexpected guide topology")
  # Ribbon width is independent of guide thickness. Deliberately editable
  # per strand, avoiding conversion of hair to opaque primitive cylinders.
  front=guide.name.startswith("fringe_")
  width=.016 if front else .027
  vertices=[];faces=[]
  for k in range(17):
   t=k/16
   if t<.5:
    u=t*2;pos=pts[0]*(1-u)+pts[1]*u
   else:
    u=(t-.5)*2;pos=pts[1]*(1-u)+pts[2]*u
   tangent=(pts[min(2,1 if t<.5 else 2)]-pts[0 if t<.5 else 1]).normalized()
   radial=Vector((pos.x, pos.y,0))
   radial-=Vector((pts[0].x,pts[0].y,0))
   if radial.length<1e-5:radial=Vector((1,0,0))
   side=tangent.cross(radial).normalized()
   if side.length<1e-5:side=Vector((1,0,0))
   taper=max(.08, math.sin(math.pi*(.07+.89*t)))
   vertices.extend([pos-side*width*taper,pos+side*width*taper])
  for k in range(16):faces.append((k*2,k*2+1,k*2+3,k*2+2))
  mesh=bpy.data.meshes.new(guide.name+"_surface")
  mesh.from_pydata(vertices,[],faces);mesh.update()
  ob=bpy.data.objects.new(guide.name.replace("_guide_","_mesh_"),mesh)
  collection.objects.link(ob);mesh.materials.append(mat)
  for face in mesh.polygons:face.use_smooth=True
  solid=ob.modifiers.new("hair_surface_thickness","SOLIDIFY");solid.thickness=.003
  ob["status"]="CANDIDATE_NOT_CANONICAL"
  records.append({"name":ob.name,"vertices":len(vertices),"faces":len(faces)})
  guide.hide_render=True
 body["hair_mesh_candidate"]=True
 body["hair_art_qa"]="NOT_RUN"
 out.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(out),load_ui=False)
 meshes=[o for o in bpy.data.objects if o.name.startswith(("bob_mesh_","fringe_mesh_"))]
 if len(meshes)!=33:raise SystemExit("FAIL hair meshes missing on reopen")
 if hashlib.sha256(src.read_bytes()).hexdigest()!=sha:raise SystemExit("FAIL source mutated")
 report={"status":"PASS_MESH_CONSTRUCTION_ONLY","hair_mesh_count":len(meshes),
 "total_vertices":sum(len(o.data.vertices) for o in meshes),
 "input_sha256":sha,"output_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
 "canonical_art_qa":"NOT_RUN","render_qa":"NOT_RUN","game_qa":"NOT_RUN",
 "source_unchanged":True,"meshes":records}
 (out.parent/"hair_mesh_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"meshes":len(meshes)}))
if __name__=="__main__":main()
