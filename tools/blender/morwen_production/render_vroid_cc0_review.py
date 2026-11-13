"""VRoid CC0 candidate inspection. No canonical Morwen assets are touched."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
src=Path("render_output/morwen_vroid_review/Base_Female.vrm")
assert src.is_file()
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
# VRM is glTF binary container. Blender glTF importer may reject VRM extensions.
bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert meshes,"VRM import yielded no meshes"
bpy.context.view_layer.update()
coords=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
mins=[min(p[i] for p in coords) for i in range(3)]
maxs=[max(p[i] for p in coords) for i in range(3)]
height=maxs[2]-mins[2]
assert height>0
center=Vector(((mins[0]+maxs[0])/2,(mins[1]+maxs[1])/2,maxs[2]-.12*height))
scene=bpy.context.scene
scene.render.engine="CYCLES";scene.cycles.samples=24
scene.render.resolution_x=768;scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
out=Path("render_output/morwen_vroid_review");out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.light_add(type="AREA",location=center+Vector((height,-height,height)))
bpy.context.object.data.energy=900;bpy.context.object.data.size=height*2
for name,delta in [("front",(0,1,0)),("right",(1,0,0)),("back",(0,-1,0)),("left",(-1,0,0)),("three_quarter",(.7,1,.35))]:
 bpy.ops.object.camera_add(location=center+Vector(delta).normalized()*height*1.7)
 cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO";cam.data.ortho_scale=height*.31
 scene.camera=cam
 scene.render.filepath=str((out/(name+"_head.png")).resolve())
 bpy.ops.render.render(write_still=True)
# Wireframe diagnostics are separate temporary copies, not canonical meshes.
for obj in meshes:
 obj.hide_render=True
wire=[]
for obj in meshes:
 duplicate=obj.copy()
 duplicate.data=obj.data.copy()
 bpy.context.collection.objects.link(duplicate)
 duplicate.hide_render=False
 modifier=duplicate.modifiers.new("Diagnostic_Wireframe","WIREFRAME")
 modifier.thickness=height*.00025
 modifier.use_replace=True
 wire.append(duplicate)
for name,delta in [("front",(0,1,0)),("right",(1,0,0)),("three_quarter",(.7,1,.35))]:
 bpy.ops.object.camera_add(location=center+Vector(delta).normalized()*height*1.7)
 cam=bpy.context.object
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO"
 cam.data.ortho_scale=height*.31
 scene.camera=cam
 scene.render.filepath=str((out/(name+"_wire.png")).resolve())
 bpy.ops.render.render(write_still=True)
# Dedicated facial inspection: derive camera target from the Face mesh, not whole-body bounds.
face=next((o for o in meshes if o.name=="Face"),None)
assert face is not None,"Expected source Face mesh missing"
face_points=[face.matrix_world@v.co for v in face.data.vertices]
face_min=Vector(tuple(min(v[i] for v in face_points) for i in range(3)))
face_max=Vector(tuple(max(v[i] for v in face_points) for i in range(3)))
face_center=(face_min+face_max)*.5
# Include the lower jaw and neck in the review; head mesh bounds can be misleading.
face_extent=max(face_max.x-face_min.x,face_max.y-face_min.y,face_max.z-face_min.z)
assert face_extent>0
face_center.z-=face_extent*.10
for obj in wire:
 obj.hide_render=True
for obj in meshes:
 obj.hide_render=False
for name,delta in [("front",(0,1,0)),("right",(1,0,0)),("left",(-1,0,0)),("three_quarter",(.7,1,.15))]:
 bpy.ops.object.camera_add(location=face_center+Vector(delta).normalized()*face_extent*3)
 cam=bpy.context.object
 cam.rotation_euler=(face_center-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO"
 cam.data.ortho_scale=face_extent*2.0
 scene.camera=cam
 scene.render.filepath=str((out/(name+"_face_detail.png")).resolve())
 bpy.ops.render.render(write_still=True)
# Mesh audit: record measurable geometry before any sculpt or style transfer.
from collections import Counter, defaultdict
face_mesh=face.data
edge_counts=Counter()
for poly in face_mesh.polygons:
 for k in range(len(poly.vertices)):
  a,b=poly.vertices[k],poly.vertices[(k+1)%len(poly.vertices)]
  edge_counts[tuple(sorted((a,b)))]+=1
face_audit={
 "object":face.name,
 "vertices":len(face_mesh.vertices),
 "edges":len(face_mesh.edges),
 "polygons":len(face_mesh.polygons),
 "triangles":sum(len(poly.vertices)==3 for poly in face_mesh.polygons),
 "quads":sum(len(poly.vertices)==4 for poly in face_mesh.polygons),
 "ngons":sum(len(poly.vertices)>4 for poly in face_mesh.polygons),
 "boundary_edges":sum(n==1 for n in edge_counts.values()),
 "nonmanifold_edges":sum(n>2 for n in edge_counts.values()),
 "dimensions_world":[round(face_max[i]-face_min[i],6) for i in range(3)],
 "source_materials":[mat.name if mat else None for mat in face_mesh.materials],
 "topology_deformation_approved":False,
 "canonical_proportions_matched":False,
 "notes":"Descriptive geometry audit only. Requires independent inspection of eye/mouth edge loops."
}
# Connected-component audit separates detached facial islands without modifying geometry.
adj=[set() for _ in face_mesh.vertices]
for e in face_mesh.edges:
 a,b=e.vertices
 adj[a].add(b);adj[b].add(a)
seen=set()
components=[]
vertex_component={}
for seed in range(len(adj)):
 if seed in seen: continue
 todo=[seed];seen.add(seed);ids=[]
 while todo:
  v=todo.pop();ids.append(v)
  for n in adj[v]:
   if n not in seen: seen.add(n);todo.append(n)
 for v in ids: vertex_component[v]=len(components)
 coords=[face.matrix_world @ face_mesh.vertices[i].co for i in ids]
 lo=[min(v[k] for v in coords) for k in range(3)]
 hi=[max(v[k] for v in coords) for k in range(3)]
 components.append({"vertices":len(ids),"bounds_min":[round(x,5) for x in lo],"bounds_max":[round(x,5) for x in hi],"centroid":[round(sum(v[k] for v in coords)/len(coords),5) for k in range(3)]})
material_counts=defaultdict(Counter)
for poly in face_mesh.polygons:
 cid=vertex_component[poly.vertices[0]]
 mat=face_mesh.materials[poly.material_index].name if poly.material_index<len(face_mesh.materials) else "UNASSIGNED"
 material_counts[cid][mat]+=1
for cid,c in enumerate(components):
 c["material_faces"]=dict(material_counts[cid])
 c["material_role_hint"]="; ".join(material_counts[cid].keys())
components.sort(key=lambda c:c["vertices"],reverse=True)
face_audit["connected_components"]=components
face_audit["component_count"]=len(components)
face_audit["component_labels"]="UNCLASSIFIED; skin, eyes and mouth require visual verification"
# Relative face metrics only: do not claim correspondence to canonical artwork.
skin_candidates=[c for c in components if any("face" in m.lower() or "skin" in m.lower() for m in c["material_faces"])]
skin=max(skin_candidates,key=lambda c:c["vertices"]) if skin_candidates else None
face_width=face_max.x-face_min.x
face_height=face_max.z-face_min.z
metrics={
 "status":"CANDIDATE_GEOMETRY_ONLY",
 "canonical_landmarks_measured":False,
 "source_coordinate_system":"Blender world, imported VRM",
 "face_mesh_bounds":{"width":round(face_width,6),"height":round(face_height,6),"depth":round(face_max.y-face_min.y,6)},
 "face_width_to_height":round(face_width/face_height,6) if face_height else None,
 "skin_component":{"vertices":skin["vertices"],"bounds_min":skin["bounds_min"],"bounds_max":skin["bounds_max"],"material_faces":skin["material_faces"]} if skin else None,
 "material_component_groups":{},
 "warnings":["Material labels and bounding boxes are not anatomical landmarks","Canonical front/profile landmark comparison requires explicit image annotation"]
}
for c in components:
 for m in c["material_faces"]:
  metrics["material_component_groups"].setdefault(m,[]).append({"vertices":c["vertices"],"centroid":c["centroid"],"bounds_min":c["bounds_min"],"bounds_max":c["bounds_max"]})
(out/"FACE_PROPORTION_CANDIDATE.json").write_text(json.dumps(metrics,indent=2)+"\n")
(out/"FACE_TOPOLOGY_AUDIT.json").write_text(json.dumps(face_audit,indent=2)+"\n")
report={"source":"Base_Female.vrm","objects":[{"name":o.name,"vertices":len(o.data.vertices),"faces":len(o.data.polygons)} for o in meshes],"bounds":{"min":mins,"max":maxs},"G1":"NOT_RUN","G2":"PENDING_ART_REVIEW","G3":"IMPORT_RENDER_AND_WIREFRAME","G4":"NOT_RUN","production_approved":False}
(out/"QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
