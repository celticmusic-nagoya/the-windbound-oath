"""V82-D isolated native oak foliage candidate. Source-aware component selection,
no QEM. Choose one bounded reduction using actual mesh dimensions and face counts;
then verify 12 alpha-aware matched views. Retain source, no forest replacement.
"""
import bpy,bmesh,hashlib,json,sys,math
from pathlib import Path
from collections import Counter
from mathutils import Vector
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v82_oak_card_selection import select_cards
LOCK='43cd20b42a4e4350cd00cb1dcccd08b436ecdf23bf497efb47dd0655fd9cdf27'
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
assert sha(src)==LOCK and bpy.app.version[:3]==(5,3,0)
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
mesh=bpy.data.meshes['island_trees_01_blockout_cleaned']
assert len(mesh.materials)>1 and mesh.materials[1] and any(x in mesh.materials[1].name.lower() for x in ('leaf','leaves','foliage','branches')), [m.name if m else None for m in mesh.materials]
# Slot 1 used as foliage by V80 oak_lod. Preserve every other slot.
foliage={1}
verts=[tuple(v.co) for v in mesh.vertices];faces=[tuple(p.vertices) for p in mesh.polygons];slots=[p.material_index for p in mesh.polygons]
lo=Vector(tuple(min(v[a] for v in verts) for a in range(3)));hi=Vector(tuple(max(v[a] for v in verts) for a in range(3)));center=(lo+hi)*.5;extent=(hi-lo).length
mesh.calc_loop_triangles();total=len(mesh.loop_triangles)
counts=Counter(t.polygon_index for t in mesh.loop_triangles)
qa={'candidate_only':True,'source_sha256':LOCK,'source_mesh':mesh.name,'source_materials':[m.name if m else None for m in mesh.materials],'source_triangles':total,'calibration':[],'limits':['No QEM or leaf enlargement','Slot 1 designation follows existing V80 authoring; actual material inventory recorded','12 alpha views are diagnostics, not a visual or runtime PASS','No forest placement changes, no Android QA']}
# One bounded sweep in memory, no repeated expensive renders: select the least aggressive
# candidate that reaches 25% triangle savings; cap at 60% to protect crowns.
chosen=None
for fraction in (.015,.025,.04,.06,.09,.12):
    cell=extent*fraction;sel=select_cards(verts,faces,slots,foliage,cell_size=cell,keep_per_cell=2)
    reduction=sum(counts[i] for i in sel['remove'])/total
    qa['calibration'].append({'cell_size_local':cell,'triangle_reduction':reduction,'leaf_components':sel['leaf_components'],'protected_faces':sel['protected_faces']})
    if .25<=reduction<=.60 and chosen is None:chosen=(cell,sel,reduction)
    elif 0<reduction<.25 and (chosen is None or chosen[2]<reduction):chosen=(cell,sel,reduction)
    if chosen and chosen[2]>=.25:break
(out/'v82d_calibration.json').write_text(json.dumps(qa,indent=2))
assert chosen is not None, 'No bounded component reduction; inspect source topology instead of repeating QEM'
cell,selection,reduction=chosen
def signature(m,protected_only=False):
    uv=m.uv_layers.active
    return Counter((p.material_index,tuple((tuple(m.vertices[m.loops[i].vertex_index].co),tuple(uv.data[i].uv) if uv else ()) for i in p.loop_indices)) for p in m.polygons if not protected_only or p.material_index not in foliage)
original=signature(mesh,True)
copy=mesh.copy();copy.name='V82D_oak_spatial_leaf_candidate'
bm=bmesh.new();bm.from_mesh(copy);bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.faces[i] for i in selection['remove']],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(copy);bm.free();copy.update()
assert signature(copy,True)==original and not copy.validate(verbose=False)
copy.calc_loop_triangles();assert len(copy.loop_triangles)==total-sum(counts[i] for i in selection['remove'])
qa.update({'cell_size_local':cell,'keep_per_cell':2,'selection':{k:v for k,v in selection.items() if k not in ('keep','remove')},'triangles_after':len(copy.loop_triangles),'reduction':reduction,'wood_coordinate_uv_exact':True})
study=bpy.data.scenes.new('V82D_OAK_ASSET_STUDY');study.render.engine='CYCLES';study.cycles.samples=24;study.cycles.use_denoising=True;study.render.resolution_x=512;study.render.resolution_y=512;study.render.resolution_percentage=100;study.render.film_transparent=True
world=bpy.data.worlds.new('V82D_ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.8,.8,.8,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8;study.world=world
ob=bpy.data.objects.new('V82D_oak_candidate',copy);study.collection.objects.link(ob)
reference=bpy.data.objects.new('V82D_oak_reference',mesh);study.collection.objects.link(reference)
cd=bpy.data.cameras.new('V82D_review_camera');cd.type='ORTHO';camera=bpy.data.objects.new('V82D_review_camera',cd);study.collection.objects.link(camera);study.camera=camera
cd.ortho_scale=extent*1.05;cd.clip_end=extent*8+10
study.render.image_settings.file_format='PNG';study.render.image_settings.color_mode='RGBA'
qa['alpha_views']=[]
for angle in (0,90,180,270):
    for elevation in (0,35,-35):
        az=math.radians(angle);el=math.radians(elevation);direction=Vector((math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)))
        camera.location=center+direction*(extent*2+1);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        masks=[]
        for name,active in (('source',reference),('candidate',ob)):
            ob.hide_render=active!=ob;reference.hide_render=active!=reference
            file=out/f'oak_{angle}_{elevation}_{name}.png';study.render.filepath=str(file.resolve())
            with bpy.context.temp_override(scene=study):bpy.ops.render.render(write_still=True,scene=study.name)
            im=bpy.data.images.load(str(file),check_existing=False);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);masks.append(a[3::4]);bpy.data.images.remove(im)
        a,b=masks;union=np.maximum(a,b).sum();assert union>0
        qa['alpha_views'].append({'azimuth':angle,'elevation':elevation,'soft_alpha_iou':float(np.minimum(a,b).sum()/union),'coverage_ratio':float(b.sum()/max(a.sum(),1e-8))})
        (out/'v82d_oak_qa.json').write_text(json.dumps(qa,indent=2))
qa['min_alpha_iou']=min(v['soft_alpha_iou'] for v in qa['alpha_views'])
qa['max_coverage_deviation']=max(abs(v['coverage_ratio']-1) for v in qa['alpha_views'])
qa['diagnostic_thresholds']={'min_soft_iou':.92,'max_coverage_deviation':.10}
qa['diagnostic_result']='PASS' if qa['min_alpha_iou']>=.92 and qa['max_coverage_deviation']<=.10 else 'HOLD'
reference.hide_render=True;ob.hide_render=False
window=bpy.context.window;assert window is not None;window.scene=study
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str((out/'v82d_oak_candidate.glb').resolve()),export_format='GLB',use_selection=True,export_animations=False)
qa['glb_sha256']=sha(out/'v82d_oak_candidate.glb')
for sc in list(bpy.data.scenes):
    if sc!=study:bpy.data.scenes.remove(sc)
bpy.ops.wm.save_as_mainfile(filepath=str((out/'v82d_oak_candidate.blend').resolve()),compress=True)
qa['native_sha256']=sha(out/'v82d_oak_candidate.blend')
bpy.ops.wm.open_mainfile(filepath=str((out/'v82d_oak_candidate.blend').resolve()))
assert signature(bpy.data.objects['V82D_oak_candidate'].data,True)==original
qa['reopen_wood_exact']=True;qa['source_unchanged']=sha(src)==LOCK;assert qa['source_unchanged']
(out/'v82d_oak_qa.json').write_text(json.dumps(qa,indent=2));print('V82D_OAK_DONE',json.dumps(qa))
