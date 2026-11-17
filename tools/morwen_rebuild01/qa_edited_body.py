"""Reopen edited .blend and compare stored control vertices/topology to source."""
from pathlib import Path
import bpy,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/qa/morwen-rebuild-01/body-fit-v02'
source=ROOT/'assets/candidates/morwen-rebuild-01/body-workspace/MORWEN_BODY_SCULPT_WORKSPACE_UNAPPROVED.blend'
target=ROOT/'assets/candidates/morwen-rebuild-01/body-fit-v02/MORWEN_BODY_FIT_V02_UNAPPROVED.blend'
def load(p):
 bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False,use_scripts=False)
 objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objs)==1
 o=objs[0];bpy.context.view_layer.update()
 return np.array([list(o.matrix_world@v.co) for v in o.data.vertices]),[list(p.vertices) for p in o.data.polygons]
a,fa=load(source);b,fb=load(target);assert fa==fb and len(a)==len(b)
d=np.linalg.norm(b-a,axis=1);assert (d>1e-7).sum()==12502
assert np.isfinite(b).all()
def cross(v,f):
 return np.cross(v[f[1]]-v[f[0]],v[f[2]]-v[f[0]])
ca=np.array([cross(a,f) for f in fa]);cb=np.array([cross(b,f) for f in fb]);areas=np.linalg.norm(cb,axis=1)
oldareas=np.linalg.norm(ca,axis=1);valid=(oldareas>1e-12)&(areas>1e-12)
reversal=int(((ca[valid]*cb[valid]).sum(1)<0).sum())
report={'task':'RB01-EDITED-MESH-REOPEN-QA','blender':bpy.app.version_string,'source_vertices':len(a),'candidate_vertices':len(b),'faces':len(fb),'topology_preserved':fa==fb,'changed_vertices':int((d>1e-7).sum()),'max_world_delta':float(d.max()),'mean_world_delta':float(d.mean()),'finite':True,'reopened_stored_geometry_matches_saved_delta':bool(np.max(abs(b-np.load(OUT/'vertex-delta.npz')['after_world']))<1e-6),'new_zero_area_first_triangles':int(((areas<1e-12)&(oldareas>=1e-12)).sum()),'large_face_normal_changes_over_90_deg':reversal,'normal_change_is_not_a_self_intersection_test':True,'G3_local_screen':'PASS' if reversal==0 else 'FAIL','G3_character':'NOT_RUN','not_tested':['self-intersections','anatomical correctness','UV distortion','rig deformation','runtime'],'original_reference_not_reverified':True}
(OUT/'reopen-technical-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
