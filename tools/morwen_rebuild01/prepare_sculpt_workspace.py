"""Preserve source intake; remove broken optional display drivers in a new copy."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'assets/candidates/morwen-rebuild-01/base-source-intake/CC0_STYLIZED_BASE_INTAKE_NOT_MORWEN.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='718a3ef4240495a496cf1efc6f213f3ced35bebdf0f259f29e2e539a88a0d817'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False,load_ui=False)
obj=bpy.data.objects['CC0_STYLIZED_ANATOMY_SOURCE_NOT_FITTED_MORWEN']
coords=[[float(x) for x in v.co] for v in obj.data.vertices]
faces=[list(p.vertices) for p in obj.data.polygons]
sig=hashlib.sha256(json.dumps([coords,faces],separators=(',',':')).encode()).hexdigest()
assert sig=='606a5cbed38aa3318626a48185bde66d3ce9f9c1f39d2fe9b6e66783f9740c4c'
removed=[]
if obj.animation_data:
 for f in list(obj.animation_data.drivers):
  if f.data_path in ('modifiers["mask_arms"].show_viewport','modifiers["mask_legs"].show_viewport'):
   removed.append(f.data_path);obj.driver_remove(f.data_path)
assert len(removed)==2,removed
for name in ('mask_arms','mask_legs'):
 mod=obj.modifiers.get(name)
 if mod:
  mod.show_viewport=False;mod.show_render=False
bpy.context.view_layer.update()
mesh=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
vp=mesh.to_mesh();vp_count=len(vp.vertices);mesh.to_mesh_clear()
assert coords==[[float(x) for x in v.co] for v in obj.data.vertices]
assert not obj.animation_data or not obj.animation_data.drivers
obj['status']='SCULPT_WORKSPACE_NOT_FITTED_NOT_APPROVED'
obj.name='MORWEN_BODY_SCULPT_WORKSPACE_UNAPPROVED'
out=ROOT/'assets/candidates/morwen-rebuild-01/body-workspace'
out.mkdir(parents=True,exist_ok=True)
p=out/'MORWEN_BODY_SCULPT_WORKSPACE_UNAPPROVED.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(p))
bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False,load_ui=False)
ob=bpy.data.objects['MORWEN_BODY_SCULPT_WORKSPACE_UNAPPROVED']
assert not ob.animation_data or not ob.animation_data.drivers
assert all(n not in ob.modifiers or (not ob.modifiers[n].show_viewport and not ob.modifiers[n].show_render) for n in ('mask_arms','mask_legs'))
report={'task':'REBUILD01-BODY-WORKSPACE','removed_broken_optional_mask_drivers':removed,'source_geometry_unchanged':True,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'geometry_signature':sig,'viewport_evaluated_vertices':vp_count,'reopen':'PASS','G3_driver_cleanup_screen':'PASS','G2':'NOT_RUN','G3_character':'NOT_RUN','G4':'NOT_RUN','sculpt_or_retopology_performed':False,'blend_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(ROOT/'docs/qa/morwen-rebuild-01/BODY_WORKSPACE_QA.json').write_text(json.dumps(report,indent=2)+'\n')
print('BODY_WORKSPACE_DRIVER_CLEANUP_PASS_NOT_SCULPTED')
