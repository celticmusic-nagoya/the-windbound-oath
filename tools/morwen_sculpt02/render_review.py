"""Render and inventory an already sculpted .blend. No geometry generation/fitting.
Usage: Blender --python SCRIPT -- SOURCE.blend OUTPUT [samples]
Standalone bpy requires importing bpy before bmesh.
"""
import bpy
import bmesh
import hashlib,json,pathlib,sys,math
from mathutils import Vector
src,out=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:sys.argv.index('--')+3]);samples=int(sys.argv[-1]) if sys.argv[-1].isdigit() else 48
source_sha=hashlib.sha256(src.read_bytes()).hexdigest();assert source_sha=='90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b'
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False,load_ui=False)
assert bpy.context.scene['sculpt02_status']=='GUI_SCULPT_EXECUTED_UNAPPROVED'
body=bpy.data.objects['SCULPT02_FACE_BODY'];sc=bpy.context.scene
working=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SCULPT02_') and not o.hide_render];assert len(working)==22
# Verify the bytes of all five actual references embedded in the .blend.
manifest=json.loads(pathlib.Path('docs/qa/morwen-sculpt02/canonical_manifest.json').read_text())
packed={hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
for f in manifest['files']:
 assert f['sha256'] in packed, f['filename']
 im=next(im for im in bpy.data.images if im.packed_file and hashlib.sha256(im.packed_file.data).hexdigest()==f['sha256'])
 (out/f['filename']).write_bytes(im.packed_file.data)
key=body.data.shape_keys.key_blocks['SCULPT02_GUI_brush_layer'];base=body.data.shape_keys.key_blocks['PR399_frozen_start'];ds=[(a.co-b.co).length for a,b in zip(key.data,base.data)];assert sum(d>1e-7 for d in ds)==1067
report={'status':'REVIEW_OF_ALREADY_SCULPTED_SOURCE','source_sha256':source_sha,'blender':bpy.app.version_string,'samples':samples,'engine':'CYCLES CPU','seed':0,'view_transform':'AgX','references_verified':True,'face_changed_vertices':sum(d>1e-7 for d in ds),'face_max_displacement':max(ds),'meshes':[],'views':[]}
deps=bpy.context.evaluated_depsgraph_get()
for ob in working:
 ev=ob.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
 report['meshes'].append({'name':ob.name,'control_vertices':len(ob.data.vertices),'control_faces':len(ob.data.polygons),'evaluated_vertices':len(me.vertices),'evaluated_faces':len(me.polygons),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True),'finite_coordinates':all(math.isfinite(c) for v in me.vertices for c in v.co)})
 bm.free();ev.to_mesh_clear()
crown=key.data[8063].co;chin=key.data[8064].co;sole=min(v.co.z for v in key.data);report['head_count']=(crown.z-sole)/(crown.z-chin.z)
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=samples;sc.cycles.seed=0;sc.cycles.use_denoising=False
sc.render.film_transparent=True;sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=-.3;sc.view_settings.gamma=1
clay=bpy.data.materials.new('REVIEW_ONLY_neutral_clay');clay.diffuse_color=(.35,.35,.35,1);clay.use_nodes=True;p=clay.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.35,.35,.35,1);p.inputs['Roughness'].default_value=.75
from bpy_extras.object_utils import world_to_camera_view
for mode in ['color','clay']:
 sc.view_layers[0].material_override=clay if mode=='clay' else None
 for view in ['front','character_left','character_right','back','three_quarter','three_quarter_other']:
  cam=bpy.data.objects['SCULPT02_'+view];sc.camera=cam;bpy.context.view_layer.update()
  headpoints=[v.co for v in key.data if v.co.z>=chin.z-.005]
  for ob in working:
   if ob!=body:headpoints.extend(ob.matrix_world@v.co for v in ob.data.vertices)
  pts=[world_to_camera_view(sc,cam,p) for p in headpoints];bounds=[min(p.x for p in pts),min(p.y for p in pts),max(p.x for p in pts),max(p.y for p in pts)]
  file=mode+'_'+view+'.png';sc.render.filepath=str(out/file);bpy.ops.render.render(write_still=True)
  report['views'].append({'mode':mode,'view':view,'file':file,'camera':list(cam.location),'rotation':list(cam.rotation_euler),'ortho_scale':cam.data.ortho_scale,'head_bounds_uv':bounds,'head_framed':all(.01<v<.99 for v in bounds),'crop_policy':'full head; lower shoulders intentionally cropped'})
# Render changes are temporary; never save over the authored source.
assert hashlib.sha256(src.read_bytes()).hexdigest()==source_sha
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False,load_ui=False);assert bpy.data.objects['SCULPT02_FACE_BODY'].data.shape_keys.key_blocks['SCULPT02_GUI_brush_layer'].value==1
report['reopen_pass']=True;report['source_unchanged']=True
(out/'render_evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print('REVIEW_COMPLETE',json.dumps({'views':len(report['views']),'meshes':len(working),'head_count':report['head_count']}))
