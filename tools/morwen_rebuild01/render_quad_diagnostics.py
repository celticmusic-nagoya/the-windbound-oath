"""Fixed-candidate render and diagnostic bend validation; no new modelling."""
from pathlib import Path
import bpy,json,sys,math
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01';OUT=ROOT/'assets/candidates/morwen-rebuild-01/body-quad-v01'
sys.path.insert(0,str(ROOT/'tools/morwen_rebuild01'))
from check_quad_intersections import screen
source=ROOT/'assets/candidates/morwen-rebuild-01/body-local-v01/MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend'
candidate=OUT/'MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED.blend'

def setup():
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=False;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';return s

def render(s,name,cam,full=False):
 s.camera=bpy.data.objects[cam];s.render.resolution_x=512;s.render.resolution_y=768 if full else 512;s.render.resolution_percentage=100;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)

def true_wire(o):
 black=bpy.data.materials.new('QA_POLYGON_EDGE_BLACK');black.diffuse_color=(.002,.002,.002,1);o.data.materials.append(black)
 m=o.modifiers.new('QA_TRUE_POLYGON_EDGES','WIREFRAME');m.use_replace=False;m.thickness=.00035;m.offset=1;m.material_offset=1;m.use_boundary=True
 return m

# Only task-specific original polygon wire views; existing rest-before PNGs reused.
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False,load_ui=False);o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0];s=setup();m=true_wire(o)
for name in ('shoulder_front','shoulder_back','knee_front'):render(s,'before_wire_'+name,'LOCAL_'+name)
bpy.ops.wm.open_mainfile(filepath=str(candidate),use_scripts=False,load_ui=False);o=bpy.data.objects['MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED'];s=setup();base=np.array([list(v.co) for v in o.data.vertices])
for view in ('front','back','right','left'):render(s,view,'SOURCE_REVIEW_'+view,True)
for name in ('shoulder_front','shoulder_back','shoulder_right','knee_front','knee_right'):render(s,'after_'+name,'LOCAL_'+name)
# Diagnostic shape-key skin bending, expressly not a production rig.
mesh=o.data;R=np.c_[[x.value for x in mesh.attributes['RB_REST_X'].data],[x.value for x in mesh.attributes['RB_REST_Y'].data],[x.value for x in mesh.attributes['RB_REST_Z'].data]]
world=np.array([list(o.matrix_world@v.co) for v in mesh.vertices]);inv=o.matrix_world.inverted()
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
o.shape_key_add(name='Basis');reports=[]
for kind,angle in [('shoulder',30),('shoulder',60),('knee',45),('knee',90)]:
 pos=world.copy()
 if kind=='shoulder':
  threshold=np.interp(R[:,2],[0,.64,.70,.76,.82,1],[.14,.14,.11,.065,.065,.065]);w=smooth(threshold-.008,threshold+.012,abs(R[:,0]))*smooth(.40,.45,R[:,2])*(1-smooth(.78,.82,R[:,2]));sg=np.where(R[:,0]>=0,1.,-1.)
  pivot=np.c_[sg*.085,np.zeros(len(R)),np.full(len(R),.812)];d=world-pivot;t=-sg*math.radians(angle);rot=d.copy();rot[:,0]=np.cos(t)*d[:,0]+np.sin(t)*d[:,2];rot[:,2]=-np.sin(t)*d[:,0]+np.cos(t)*d[:,2]
 else:
  w=(1-smooth(.306,.371,world[:,2]))*(R[:,2]<.43);sg=np.where(R[:,0]>=0,1.,-1.);pivot=np.c_[sg*.045,np.full(len(R),.006),np.full(len(R),.326)];d=world-pivot;t=math.radians(angle);rot=d.copy();rot[:,1]=math.cos(t)*d[:,1]-math.sin(t)*d[:,2];rot[:,2]=math.sin(t)*d[:,1]+math.cos(t)*d[:,2]
 pos=world+w[:,None]*(pivot+rot-world);key=o.shape_key_add(name=f'QA_ONLY_{kind}_{angle}deg')
 for v,p in zip(key.data,pos):v.co=inv@Vector(tuple(p))
 key.value=1;bpy.context.view_layer.update();ob=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ob.to_mesh();ev=[list(ob.matrix_world@v.co) for v in em.vertices];faces=[list(p.vertices) for p in em.polygons];ob.to_mesh_clear()
 pid=[x.value for x in mesh.attributes['RB_PATCH_ID'].data];test=screen(ev,faces,pid)
 report={'pose':key.name,'angle_degrees':angle,'diagnostic_only_not_production_rig':True,'finite':bool(np.isfinite(ev).all()),'strict_nonadjacent_face_pairs':test['strict_non_coplanar_face_pairs'],'patch_involved_pairs':test['patch_involved_strict_face_pairs'],'adjacent_face_penetrations':test['adjacent_face_interior_penetration_count'],'patch_quad_fold_flags':sum(x['patch']>0 for x in test['quad_fold_flags']),'strict_pairs':test['patch_involved_strict_pairs']}
 reports.append(report)
 if kind=='shoulder':
  bpy.data.objects['SOURCE_REVIEW_front'].data.ortho_scale=1.5 if angle==60 else 1.2
  render(s,f'pose_{kind}_{angle}_front','SOURCE_REVIEW_front',True);render(s,f'pose_{kind}_{angle}_close','LOCAL_shoulder_right')
 else:
  render(s,f'pose_{kind}_{angle}_right','SOURCE_REVIEW_right',True);render(s,f'pose_{kind}_{angle}_close','LOCAL_knee_right')
 key.value=0;bpy.context.view_layer.update()
assert np.array_equal(base,np.array([list(v.co) for v in mesh.vertices]))
o['diagnostic_bends']='Shape keys: shoulder30/60deg, knee45/90deg; not an animation-ready rig'
o['quality']='FAIL: 2/15 tracked normal warnings remain; intersections/folds present'
s.camera=bpy.data.objects['SOURCE_REVIEW_front'];s.camera.data.ortho_scale=1.2;s.render.resolution_x=512;s.render.resolution_y=768;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
(Q/'bend-qa.json').write_text(json.dumps({'method':'Diagnostic rotation-weight shape keys; no production rig claimed','rest_basis_unchanged':True,'poses':reports,'G3_bend_validation':'FAIL'},indent=2)+'\n')
m=true_wire(o)
for name in ('shoulder_front','shoulder_back','knee_front'):render(s,'after_wire_'+name,'LOCAL_'+name)
print('FIXED_QUAD_CANDIDATE_REST_POSE_WIRE_EVIDENCE_SAVED')
