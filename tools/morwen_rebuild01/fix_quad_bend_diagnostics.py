"""Correct diagnostic arm-group membership; rest topology/coordinates untouched."""
from pathlib import Path
import bpy,json,sys,math
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01';OUT=ROOT/'assets/candidates/morwen-rebuild-01/body-quad-v01'
sys.path.insert(0,str(ROOT/'tools/morwen_rebuild01'));from check_quad_intersections import screen
p=OUT/'MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED.blend';bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False,load_ui=False);o=bpy.data.objects['MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED'];m=o.data;s=bpy.context.scene
before=np.array([list(v.co) for v in m.vertices]);world=np.array([list(o.matrix_world@v.co) for v in m.vertices]);R=np.c_[[x.value for x in m.attributes['RB_REST_X'].data],[x.value for x in m.attributes['RB_REST_Y'].data],[x.value for x in m.attributes['RB_REST_Z'].data]];inv=o.matrix_world.inverted()
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
threshold=np.interp(R[:,2],[0,.64,.70,.76,.82,1],[.14,.14,.11,.065,.065,.065]);w=smooth(threshold-.008,threshold+.012,abs(R[:,0]))*smooth(.40,.45,R[:,2])*(1-smooth(.78,.82,R[:,2]));sg=np.where(R[:,0]>=0,1.,-1.)
assert not np.any(w[(R[:,2]>.43)&(R[:,2]<.62)&(abs(R[:,0])<.12)]>0)
old=json.loads((Q/'bend-qa.json').read_text());new_reports=[]
for angle in (30,60):
 key=m.shape_keys.key_blocks[f'QA_ONLY_shoulder_{angle}deg'];pivot=np.c_[sg*.085,np.zeros(len(R)),np.full(len(R),.812)];d=world-pivot;t=-sg*math.radians(angle);rot=d.copy();rot[:,0]=np.cos(t)*d[:,0]+np.sin(t)*d[:,2];rot[:,2]=-np.sin(t)*d[:,0]+np.cos(t)*d[:,2];pos=world+w[:,None]*(pivot+rot-world)
 for v,x in zip(key.data,pos):v.co=inv@Vector(tuple(x))
 key.value=1;bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();verts=[list(ev.matrix_world@v.co) for v in em.vertices];faces=[list(f.vertices) for f in em.polygons];ev.to_mesh_clear();test=screen(verts,faces,[x.value for x in m.attributes['RB_PATCH_ID'].data])
 new_reports.append({'pose':key.name,'angle_degrees':angle,'diagnostic_only_not_production_rig':True,'finite':bool(np.isfinite(verts).all()),'strict_nonadjacent_face_pairs':test['strict_non_coplanar_face_pairs'],'patch_involved_pairs':test['patch_involved_strict_face_pairs'],'adjacent_face_penetrations':test['adjacent_face_interior_penetration_count'],'patch_quad_fold_flags':sum(x['patch']>0 for x in test['quad_fold_flags']),'strict_pairs':test['patch_involved_strict_pairs'],'waist_membership_bug_fixed':True})
 for suffix,cam,full in [('front','SOURCE_REVIEW_front',True),('close','LOCAL_shoulder_right',False)]:
  s.camera=bpy.data.objects[cam]
  if full:s.camera.data.ortho_scale=1.5 if angle==60 else 1.2
  s.render.resolution_x=512;s.render.resolution_y=768 if full else 512;s.render.filepath=str(OUT/f'pose_shoulder_{angle}_{suffix}.png');bpy.ops.render.render(write_still=True)
 key.value=0;bpy.context.view_layer.update()
assert np.array_equal(before,np.array([list(v.co) for v in m.vertices]))
s.camera=bpy.data.objects['SOURCE_REVIEW_front'];s.camera.data.ortho_scale=1.2;s.render.resolution_x=512;s.render.resolution_y=768;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(p))
old['poses']=new_reports+[x for x in old['poses'] if 'knee' in x['pose']];old['diagnostic_setup_correction']='Initial shoulder weight selector mistakenly affected pelvis/upper thigh; initial results retained separately. Corrected anatomical arm membership and60deg framing only. Rest mesh unchanged.';(Q/'bend-qa.json').write_text(json.dumps(old,indent=2)+'\n');print('DIAGNOSTIC_WEIGHT_SETUP_FIXED_REST_MESH_UNCHANGED')
