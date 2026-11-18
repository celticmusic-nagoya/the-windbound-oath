"""Apply the solved local vertex sculpt and render diagnostic evidence."""
from pathlib import Path
import bpy,json
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
QA=ROOT/'docs/qa/morwen-rebuild-01/body-local-v01'
OUT=ROOT/'assets/candidates/morwen-rebuild-01/body-local-v01';OUT.mkdir(parents=True,exist_ok=True)
p=ROOT/'assets/candidates/morwen-rebuild-01/body-fit-v02/MORWEN_BODY_FIT_V02_UNAPPROVED.blend'
bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False,load_ui=False)
o=bpy.data.objects['MORWEN_BODY_FIT_V02_UNAPPROVED'];scene=bpy.context.scene
D=np.load(QA/'local-edit.npz');free=D['free_mask'];target=D['after_world']
local_before=np.array([list(v.co) for v in o.data.vertices]);face_before=[list(p.vertices) for p in o.data.polygons]
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
close={'shoulder_front':((0,-3,.787),.36),'shoulder_back':((0,3,.787),.36),'shoulder_right':((-3,0,.787),.34),'knee_front':((0,-3,.27),.47),'knee_right':((-3,0,.27),.47)}
for name,(position,scale) in close.items():
 data=bpy.data.cameras.new('LOCAL_'+name);cam=bpy.data.objects.new('LOCAL_'+name,data);scene.collection.objects.link(cam)
 cam.location=position;center=Vector((0,0,position[2]));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale

def render(name,cam,res=(512,512)):
 scene.camera=bpy.data.objects[cam];scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
# Only new regional before closeups; reuse existing v02 full-body before renders.
for name in close:render('before_'+name,'LOCAL_'+name)
inv=o.matrix_world.inverted()
for i in np.where(free)[0]:o.data.vertices[int(i)].co=inv@Vector(tuple(target[i]))
o.data.update();o.name='MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED'
o['method']='Pinned-boundary mesh-adjacency local surface sculpt'
o['parent_geometry']='Body-fit-v02 retained; global cage not rerun'
o['art_status']='INDEPENDENT_G2_FAIL_NOT_APPROVED'
local_after=np.array([list(v.co) for v in o.data.vertices])
assert np.array_equal(local_before[~free],local_after[~free])
assert face_before==[list(p.vertices) for p in o.data.polygons]
for name in ('front','back','right','left'):render(name,'SOURCE_REVIEW_'+name,(512,768))
for name in close:render('after_'+name,'LOCAL_'+name)
scene.camera=bpy.data.objects['SOURCE_REVIEW_front'];scene.render.resolution_x=512;scene.render.resolution_y=768
blend=OUT/'MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
# Diagnostic wire material only, after source save; no topology modifier added.
original_materials=list(o.data.materials);o.data.materials.clear()
mat=bpy.data.materials.new('LOCAL_QUAD_FLOW_DIAGNOSTIC');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links
wire=nodes.new('ShaderNodeWireframe');wire.use_pixel_size=True;wire.inputs['Size'].default_value=1.1
mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.32,.42,.50,1);mix.inputs[2].default_value=(.003,.003,.003,1)
links.new(wire.outputs['Fac'],mix.inputs[0]);links.new(mix.outputs[0],nodes.get('Principled BSDF').inputs['Base Color']);o.data.materials.append(mat)
for name in ('shoulder_front','knee_front'):render('wire_'+name,'LOCAL_'+name)
np.savez(QA/'stored-local-coordinate-delta.npz',before=local_before,after=local_after,free_mask=free)
print('LOCAL_EDIT_SAVED',int((np.linalg.norm(local_after-local_before,axis=1)>1e-7).sum()),'protected_exact',int((~free).sum()))
