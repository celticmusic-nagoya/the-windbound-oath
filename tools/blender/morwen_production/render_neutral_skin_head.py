"""Non-destructive, isolated VRoid skin-head orthographic diagnostic."""
import bpy, json
from pathlib import Path
from mathutils import Vector
src=Path("render_output/morwen_vroid_review/Base_Female.vrm")
assert src.is_file(), "Pinned source missing"
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
face=next(o for o in bpy.context.scene.objects if o.type=="MESH" and o.name=="Face")
mesh=face.data
adj=[set() for _ in mesh.vertices]
for e in mesh.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for v in range(len(adj)):
 if v in seen:continue
 todo=[v];seen.add(v);ids=set()
 while todo:
  q=todo.pop();ids.add(q)
  for n in adj[q]:
   if n not in seen:seen.add(n);todo.append(n)
 components.append(ids)
candidates=[]
for ids in components:
 if len(ids)!=588:continue
 mats={mesh.materials[p.material_index].name for p in mesh.polygons if p.vertices[0] in ids and p.material_index<len(mesh.materials)}
 if any("SKIN" in m.upper() for m in mats):candidates.append(ids)
assert len(candidates)==1, "Skin island identification ambiguous"
ids=candidates[0]
ordered=sorted(ids);index={v:i for i,v in enumerate(ordered)}
verts=[tuple(face.matrix_world@mesh.vertices[i].co) for i in ordered]
polys=[tuple(index[v] for v in p.vertices) for p in mesh.polygons if all(v in ids for v in p.vertices)]
assert polys and len(verts)==588
for o in list(bpy.context.scene.objects):
 if o.type=="MESH":bpy.data.objects.remove(o,do_unlink=True)
new=bpy.data.meshes.new("NeutralSkinHeadMesh")
new.from_pydata(verts,[],polys);new.update()
obj=bpy.data.objects.new("NeutralSkinHead_588V",new);bpy.context.collection.objects.link(obj)
mat=bpy.data.materials.new("NeutralSkinDiagnostic");mat.diffuse_color=(.67,.52,.46,1)
new.materials.append(mat)
lo=Vector([min(v[i] for v in verts) for i in range(3)])
hi=Vector([max(v[i] for v in verts) for i in range(3)])
center=(lo+hi)*.5;extent=max(hi-lo)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=768;scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="Standard"
bpy.ops.object.light_add(type="AREA",location=center+Vector((extent,-extent,extent)))
bpy.context.object.data.energy=450;bpy.context.object.data.size=extent*2
out=Path("render_output/morwen_neutral_head");out.mkdir(parents=True,exist_ok=True)
for name,d in [("front",(0,1,0)),("right",(1,0,0)),("back",(0,-1,0)),("left",(-1,0,0))]:
 bpy.ops.object.camera_add(location=center+Vector(d)*extent*3)
 cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO";cam.data.ortho_scale=extent*1.65;scene.camera=cam
 scene.render.filepath=str((out/(name+"_neutral_skin.png")).resolve())
 bpy.ops.render.render(write_still=True)
assert len(new.vertices)==588
(out/"QA.json").write_text(json.dumps({"status":"NEUTRAL_SKIN_ISOLATED","source_modified":False,"source":"Base_Female.vrm","skin_vertices":len(new.vertices),"skin_faces":len(new.polygons),"views":["front","right","back","left"],"camera_orthographic":True,"same_camera_scale":True,"canonical_alignment":"NOT_DONE","G2":"NOT_APPROVED","G3":"RENDERED_DIAGNOSTIC_ONLY"},indent=2)+"\n")
