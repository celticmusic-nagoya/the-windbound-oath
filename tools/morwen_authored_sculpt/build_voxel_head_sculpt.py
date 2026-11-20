"""First editable voxel-sculpt head volume, candidate only; no legacy ring/cage import.
Use Blender 5.2.4. Anatomical clay masses are fused with voxel remesh,
then sculpt-smoothed; orthographic renders are neutral, NOT a G2 pass.
"""
import bpy, math, json, hashlib, sys, os
from mathutils import Vector
from pathlib import Path
out=Path(sys.argv[sys.argv.index("--")+1]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc["asset"]="MORWEN";sc["status"]="NEW_VOXEL_SCULPT_CANDIDATE_G2_NOT_RUN"
sc["axes"]="Z_UP_FACE_NEGATIVE_Y";sc["scale"]="PROVISIONAL_LOCAL_NOT_CANONICAL"
def uv(name,loc,scale):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,location=loc)
 o=bpy.context.object;o.name=name
 o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return o
# Anatomical volume assembly: cranial vault, temporal mass, cheeks, jaw, chin,
# nasal bridge and alar wings. The component spheres are *intermediate sculpt
# clay*, not final disconnected game geometry or a claimed completed face.
masses=[
 ("cranial_vault",(0,0,1.63),(.275,.235,.325)),
 ("lower_face",(0,-.042,1.385),(.216,.205,.205)),
 ("left_cheek",(-.147,-.122,1.468),(.119,.101,.108)),
 ("right_cheek",(.147,-.122,1.468),(.119,.101,.108)),
 ("jaw",(0,-.027,1.327),(.184,.174,.118)),
 ("chin",(0,-.143,1.262),(.106,.094,.072)),
 ("nose_bridge",(0,-.224,1.51),(.045,.068,.124)),
 ("nose_tip",(0,-.292,1.425),(.061,.058,.042)),
 ("alar_left",(-.047,-.258,1.420),(.037,.038,.028)),
 ("alar_right",(.047,-.258,1.420),(.037,.038,.028)),
 ("forehead",(0,-.159,1.686),(.197,.086,.151)),
]
obs=[uv(*a) for a in masses]
bpy.ops.object.select_all(action="DESELECT")
for o in obs:o.select_set(True)
bpy.context.view_layer.objects.active=obs[0]
bpy.ops.object.join()
head=bpy.context.object;head.name="MORWEN_Head_VoxelSculpt_CANDIDATE"
# Voxel remesh merges all sculpt clay into a single watertight surface.
head.data.remesh_voxel_size=.009
bpy.ops.object.voxel_remesh()
assert len([o for o in sc.objects if o.type=="MESH"])==1
# Sculpt-mode surface relaxation; keeps facial planes for further manual sculpt.
bpy.ops.object.modifier_add(type="SMOOTH")
mod=head.modifiers[-1];mod.factor=1.2;mod.iterations=5
bpy.ops.object.modifier_apply(modifier=mod.name)
for p in head.data.polygons:p.use_smooth=True
skin=bpy.data.materials.new("neutral_clay_review")
skin.diffuse_color=(.62,.57,.55,1);skin.use_nodes=True
skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.62,.57,.55,1)
head.data.materials.append(skin)
sc.render.engine="CYCLES";sc.cycles.device="CPU";sc.cycles.samples=20
sc.render.threads_mode="FIXED";sc.render.threads=4
sc.render.resolution_x=720;sc.render.resolution_y=840;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.render.film_transparent=True
camd=bpy.data.cameras.new("ORTHO_QA");cam=bpy.data.objects.new("ORTHO_QA",camd);sc.collection.objects.link(cam)
sc.camera=cam;camd.type="ORTHO";camd.ortho_scale=.92
lightd=bpy.data.lights.new("CLAY_QA_AREA","AREA");light=bpy.data.objects.new("CLAY_QA_AREA",lightd);sc.collection.objects.link(light)
lightd.energy=280;lightd.size=2
target=Vector((0,0,1.52));light.location=(1.1,-1.5,2.5)
light.rotation_euler=(target-light.location).to_track_quat("-Z","Y").to_euler()
views={"front":(0,-2.5,1.52),"right":(2.5,0,1.52),"back":(0,2.5,1.52),"left":(-2.5,0,1.52),"three_quarter":(1.6,-2,1.62)}
for name,pos in views.items():
 cam.location=pos
 cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
 sc.render.filepath=str(out/(name+".png"))
 bpy.ops.render.render(write_still=True)
 assert os.path.getsize(sc.render.filepath)>2000
sc["QA"]="VOXEL_MESH_EXISTS_RENDER_PASS_ART_NOT_RUN"
blend=out/"MORWEN_VOXEL_HEAD_FIRST_SCULPT_CANDIDATE.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
assert blend.stat().st_size>10000
report={"status":"CANDIDATE_NOT_ART_APPROVED","method":"fused_anatomical_clay_voxel_remesh_not_ring_mesh","blender":bpy.app.version_string,"head_vertices":len(head.data.vertices),"head_faces":len(head.data.polygons),"voxel_size":head.data.remesh_voxel_size,"local_axes":"Z_UP_NEG_Y_FRONT","units":"PROVISIONAL","renders":list(views),"blend_sha256":hashlib.sha256(blend.read_bytes()).hexdigest(),"G1":"NOT_RUN_VISUAL_CALIBRATION","G2":"NOT_RUN_INDEPENDENT_ART","G3":"PARTIAL_REOPEN_NOT_RUN","G4":"NOT_RUN"}
(out/"QA.json").write_text(json.dumps(report,indent=2)+"\n")
print("MORWEN_NEW_VOXEL_SCULPT_CANDIDATE",json.dumps(report))
