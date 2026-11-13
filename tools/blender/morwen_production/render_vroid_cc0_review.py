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
report={"source":"Base_Female.vrm","objects":[{"name":o.name,"vertices":len(o.data.vertices),"faces":len(o.data.polygons)} for o in meshes],"bounds":{"min":mins,"max":maxs},"G1":"NOT_RUN","G2":"PENDING_ART_REVIEW","G3":"IMPORT_RENDER_AND_WIREFRAME","G4":"NOT_RUN","production_approved":False}
(out/"QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
