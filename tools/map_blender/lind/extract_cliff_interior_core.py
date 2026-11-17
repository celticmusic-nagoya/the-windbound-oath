"""Inspect original local scan patch boundary and identify a safe interior core.

Read prior verified .blend; do not modify original or invent new rock shapes.
The core is an unoptimized source subset, NOT a retopologized final asset.
"""
import bpy,bmesh,sys,json,hashlib,collections
from pathlib import Path
from mathutils import Vector

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def main():
 import argparse
 p=argparse.ArgumentParser()
 p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
 out=Path(a.out).resolve()
 original=bpy.data.objects["LOCAL_PATCH_UNOPTIMIZED_SOURCE_GEOMETRY"]
 original.name="LOCAL_PATCH_ORIGINAL_IMMUTABLE"
 assert len(original.data.polygons)>30000
 bm=bmesh.new();bm.from_mesh(original.data);bm.faces.ensure_lookup_table()
 boundary=[e for e in bm.edges if e.is_boundary]
 nonmanifold=[e for e in bm.edges if not e.is_manifold and not e.is_boundary]
 # Erode source patch by face-adjacency rings, preventing raw cut edges
 # from being selected as the central surface.
 distances={}
 queue=collections.deque()
 for edge in boundary:
  for f in edge.link_faces:
   if f not in distances:distances[f]=0;queue.append(f)
 while queue:
  f=queue.popleft()
  for e in f.edges:
   for n in e.link_faces:
    if n not in distances:
     distances[n]=distances[f]+1;queue.append(n)
 # A fixed minimum ring depth is only a conservative first filter.
 threshold=12
 eligible={f for f in bm.faces if distances.get(f,0)>=threshold}
 if len(eligible)<1000:raise RuntimeError("Interior eroded away; stop and redesign region")
 # Disconnected eligible islands: keep largest only.
 remaining=set(eligible);components=[]
 while remaining:
  seed=remaining.pop();q=[seed];component=[seed]
  while q:
   f=q.pop()
   for e in f.edges:
    for n in e.link_faces:
     if n in remaining:remaining.remove(n);q.append(n);component.append(n)
  components.append(component)
 core=max(components,key=len)
 if len(core)<1000:raise RuntimeError("No meaningful connected interior core")
 # Source mesh original retained; new mesh is only a selected subset with
 # publisher UV loop values exactly copied.
 original_uv=original.data.uv_layers.active
 assert original_uv
 bm.faces.index_update()
 chosen={f.index for f in core}
 vertex_map={};vertices=[];faces=[];uvs=[]
 for poly in original.data.polygons:
  if poly.index not in chosen:continue
  fv=[];fu=[]
  for li in poly.loop_indices:
   old=original.data.loops[li].vertex_index
   if old not in vertex_map:
    vertex_map[old]=len(vertices)
    vertices.append(tuple(original.data.vertices[old].co))
   fv.append(vertex_map[old]);fu.append(tuple(original_uv.data[li].uv))
  faces.append(fv);uvs.append(fu)
 m=bpy.data.meshes.new("INTERIOR_CORE_SOURCE_TRIANGLES")
 m.from_pydata(vertices,[],faces);m.update()
 m.uv_layers.new(name="PUBLISHER_UV_UNCHANGED")
 for face,fu in zip(m.polygons,uvs):
  for li,uv in zip(face.loop_indices,fu):
   m.uv_layers.active.data[li].uv=uv
 for mat in original.data.materials:m.materials.append(mat)
 obj=bpy.data.objects.new("INTERIOR_CORE_REFERENCE_NOT_RETOPO",m)
 bpy.context.collection.objects.link(obj)
 original.hide_render=True
 bm2=bmesh.new();bm2.from_mesh(m)
 core_boundary=sum(e.is_boundary for e in bm2.edges)
 core_nonmanifold=sum(not e.is_manifold and not e.is_boundary for e in bm2.edges)
 bm2.free();bm.free()
 # Show interior under the same world and lighting; camera centers on core.
 bounds=[obj.matrix_world@Vector(c) for c in obj.bound_box]
 center=sum(bounds,Vector())/8
 span=max(max(v[i] for v in bounds)-min(v[i] for v in bounds) for i in range(3))
 cam=bpy.data.objects["PATCH_QA_CAMERA"]
 cam.data.ortho_scale=max(span*1.5,1)
 cam.location=center+Vector((span*.6,-span*1.5,span*.45))
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 lamp=bpy.data.objects["PATCH_AREA"]
 lamp.location=center+Vector((-span*.4,-span*.6,span*.7))
 lamp.rotation_euler=(center-lamp.location).to_track_quat("-Z","Y").to_euler()
 scene=bpy.context.scene;scene.camera=cam
 scene.render.filepath=str(out/"interior_core_pbr.png")
 bpy.ops.render.render(write_still=True)
 bpy.ops.file.pack_all()
 blend=out/"interior_core_reference.blend"
 bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 result={"method":"SOURCE_FACE_ADJACENCY_BOUNDARY_EROSION",
 "input_source_faces":len(original.data.polygons),"input_boundary_edges":len(boundary),
 "input_nonmanifold_edges":len(nonmanifold),"erosion_face_rings":threshold,
 "eligible_faces":len(eligible),"interior_component_count":len(components),
 "selected_core_faces":len(faces),"selected_core_vertices":len(vertices),
 "selected_core_boundary_edges":core_boundary,
 "selected_core_nonmanifold_edges":core_nonmanifold,
 "source_uv":"PRESERVED_EXACT_LOOP_VALUES",
 "status":"UNOPTIMIZED_REFERENCE_NOT_FINAL",
 "retopology":"NOT_RUN","normal_bake":"NOT_RUN",
 "outputs":{p.name:sha(p) for p in [out/"interior_core_pbr.png",blend]}}
 (out/"interior_core_metrics.json").write_text(json.dumps(result,indent=2)+"\n")
 print("INTERIOR_CORE_QA",json.dumps({k:result[k] for k in ("input_source_faces","input_boundary_edges","eligible_faces","selected_core_faces","selected_core_boundary_edges")}))
if __name__=="__main__":main()
