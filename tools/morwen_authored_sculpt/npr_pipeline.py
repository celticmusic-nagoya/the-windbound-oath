"""TWO NPR preview + portable glTF conversion. Blender 5.2.4.
Usage: blender -b --python tools/morwen_authored_sculpt/npr_pipeline.py -- INPUT.glb OUTPUT_DIR
Never treats generated output as canonical. EEVEE-only nodes are not exported to glTF.
"""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args)!=2: raise SystemExit('Usage: -- INPUT.glb|fbx OUTPUT_DIR')
src=Path(args[0]).resolve();out=Path(args[1]).resolve()
if not src.is_file() or src.suffix.lower() not in ('.glb','.gltf','.fbx'):
 raise SystemExit('BLOCKED: supply existing .glb/.gltf/.fbx; never fabricate a canonical base model')
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
if src.suffix.lower()=='.fbx':bpy.ops.import_scene.fbx(filepath=str(src))
else:bpy.ops.import_scene.gltf(filepath=str(src))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not meshes:raise SystemExit('FAIL: imported asset has no mesh')
# Keep source materials for portable glTF export; render-only NPR overrides live on a duplicate collection.
base=bpy.data.collections.new('ORIGINAL_IMPORTED_PORTABLE');bpy.context.scene.collection.children.link(base)
for ob in meshes:
 for coll in list(ob.users_collection):coll.objects.unlink(ob)
 base.objects.link(ob)
preview=bpy.data.collections.new('NPR_PREVIEW_ONLY_NOT_FOR_EXPORT');bpy.context.scene.collection.children.link(preview)
for ob in meshes:
 dup=ob.copy();dup.data=ob.data.copy();preview.objects.link(dup);dup.name='NPR_'+ob.name
 for mat_slot in dup.material_slots:
  original=mat_slot.material
  color=tuple(original.diffuse_color[:3]) if original else (.65,.6,.75)
  m=bpy.data.materials.new('EEVEE_TOON_'+(original.name if original else 'default'))
  m.use_nodes=True;n=m.node_tree.nodes;n.clear();links=m.node_tree.links
  outnode=n.new('ShaderNodeOutputMaterial');rgb=n.new('ShaderNodeShaderToRGB')
  diffuse=n.new('ShaderNodeBsdfDiffuse');diffuse.inputs['Color'].default_value=(*color,1)
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT'
  ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
  for index,(pos,mul) in enumerate(((.0,.44),(.46,.72),(.72,1.0))):
   el=ramp.color_ramp.elements[0] if index==0 else ramp.color_ramp.elements.new(pos)
   el.position=pos;el.color=(*(min(1,c*mul) for c in color),1)
  emit=n.new('ShaderNodeEmission')
  links.new(diffuse.outputs['BSDF'],rgb.inputs['Shader'])
  links.new(rgb.outputs['Color'],ramp.inputs['Fac'])
  links.new(ramp.outputs['Color'],emit.inputs['Color'])
  links.new(emit.outputs['Emission'],outnode.inputs['Surface'])
  mat_slot.material=m
# Viewport silhouette via a duplicated, slightly inflated black backface mesh.
outline_mat=bpy.data.materials.new('NPR_OUTLINE_BACKFACE_ONLY')
outline_mat.diffuse_color=(.018,.012,.028,1);outline_mat.use_nodes=True
bsdf=outline_mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.018,.012,.028,1)
outline_mat.use_backface_culling=True
for ob in list(preview.objects):
 if ob.type!='MESH':continue
 edge=ob.copy();edge.data=ob.data.copy();preview.objects.link(edge);edge.name='OUTLINE_'+ob.name
 edge.data.materials.clear();edge.data.materials.append(outline_mat)
 solid=edge.modifiers.new('INVERTED_HULL_PREVIEW','SOLIDIFY');solid.thickness=.004;solid.offset=1;solid.use_flip_normals=True
# Object sets are mutually exclusive between portable export and NPR preview.
for o in base.objects:o.hide_render=True
for o in preview.objects:o.hide_render=False
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
bbox=[o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
center=sum(bbox,Vector())/len(bbox)
extent=max((max(p[i] for p in bbox)-min(p[i] for p in bbox)) for i in range(3))
extent=max(extent,.01)
for loc,power in [((2,-3,4),1100),((-3,-1,2),550)]:
 ld=bpy.data.lights.new('NPR_Review_Light','AREA');ld.energy=power;ld.size=4
 obj=bpy.data.objects.new('NPR_Review_Light',ld);scene.collection.objects.link(obj)
 obj.location=center+Vector(loc)*extent;obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
for name,offset in [('front',(0,-3,1)),('three_quarter',(2.5,-2.5,1.4)),('back',(0,3,1))]:
 bpy.ops.object.camera_add(location=center+Vector(offset)*extent)
 cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.type='ORTHO';cam.data.ortho_scale=extent*1.7;scene.camera=cam
 scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(cam,do_unlink=True)
# Export only ORIGINAL imported geometry and materials; no preview-only ShaderToRGB or hull.
bpy.ops.object.select_all(action='DESELECT')
for o in base.objects:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.export_scene.gltf(filepath=str(out/'portable_original_materials.glb'),export_format='GLB',use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'NPR_REVIEW_UNAPPROVED.blend'))
report={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'mesh_count':len(meshes),'status':'TECHNICAL_CANDIDATE_NOT_CANONICAL','preview_engine':'EEVEE','glb_shader':'original_imported_materials_not_NPR','G1':'BLOCKED_CANONICAL_MATCH','G2':'NOT_RUN_INDEPENDENT_ART','G3':'NOT_RUN_IMPORT_EXPORT_PARITY','G4':'NOT_RUN_GAME_ENGINE'}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('NPR_PIPELINE_OUTPUT_CREATED',len(meshes))
