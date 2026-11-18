"""Read-only saved local sculpt QA: real geometry, protected regions, residuals."""
from pathlib import Path
import bpy,json,os
import numpy as np
ROOT=Path(__file__).resolve().parents[2];QA=ROOT/'docs/qa/morwen-rebuild-01/body-local-v01'
D=np.load(QA/'local-edit.npz');free=D['free_mask'];rest=D['original_source_world']
paths=[ROOT/'assets/candidates/morwen-rebuild-01/body-fit-v02/MORWEN_BODY_FIT_V02_UNAPPROVED.blend',ROOT/'assets/candidates/morwen-rebuild-01/body-local-v01/MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend']
world=[];local=[];faces=[]
for path in paths:
 bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
 objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objs)==1
 o=objs[0];bpy.context.view_layer.update();world.append(np.array([list(o.matrix_world@v.co) for v in o.data.vertices]));local.append(np.array([list(v.co) for v in o.data.vertices]));faces.append([list(p.vertices) for p in o.data.polygons])
a,b=world;la,lb=local;f=faces[0];assert f==faces[1]
assert np.array_equal(la[~free],lb[~free]);assert np.isfinite(b).all()
delta=np.linalg.norm(b-a,axis=1);assert int((delta>1e-7).sum())==3422
x0,y0,z0=rest.T
regions={'central_chest':D['central_chest_mask'],'waist':(z0>.58)&(z0<.62)&(abs(x0)<.13),'pelvis':(z0>.43)&(z0<.58)&(abs(x0)<.13),'fixed_exterior':~free}
protection={name:{'vertices':int(mask.sum()),'exact_local_coordinates_preserved':bool(np.array_equal(la[mask],lb[mask])),'max_world_delta':float(delta[mask].max())} for name,mask in regions.items()}
assert all(d['exact_local_coordinates_preserved'] for d in protection.values())
metrics=[]
for name,z,limit,tgt,unc in [('shoulder_width',.775,None,180,10),('chest_width',.7,.10,140,10),('waist_width',.6,.125,100,6),('pelvis_width',.53,.125,198,8),('knee_outer_width',.29,None,124,10)]:
 mask=abs(z0-z)<.008
 if limit:mask &= abs(x0)<limit
 before=float(np.ptp(a[mask,0])*946);after=float(np.ptp(b[mask,0])*946)
 metrics.append({'measurement':name,'target_px':tgt,'uncertainty_px':unc,'before_px':before,'after_px':after,'before_abs_error_px':abs(before-tgt),'after_abs_error_px':abs(after-tgt),'selection':'same source vertex band, tracked through local edit; not calibrated silhouette IoU'})
# Chest band includes 34 edited lateral/axillary support vertices, not a globally locked chest.
ch=D['chest_band'];changed_ch=int(((delta>1e-7)&ch).sum())
chest_bbox_before=np.array([a[ch].min(0),a[ch].max(0)]);chest_bbox_after=np.array([b[ch].min(0),b[ch].max(0)])
N=lambda v:np.array([np.cross(v[q[1]]-v[q[0]],v[q[2]]-v[q[0]]) for q in f])
n0,na,nb=N(rest),N(a),N(b);bad0=(n0*na).sum(1)<0;bad1=(n0*nb).sum(1)<0
areas_a=np.linalg.norm(na,axis=1);areas_b=np.linalg.norm(nb,axis=1)
edges={}
for p in f:
 for i,j in zip(p,p[1:]+p[:1]):key=tuple(sorted((i,j)));edges[key]=edges.get(key,0)+1
neighbors=[[] for _ in a]
for i,j in edges:neighbors[i].append(j);neighbors[j].append(i)
L=lambda v:np.array([v[i]-v[js].mean(0) for i,js in enumerate(neighbors)])
lpa,lpb=L(a),L(b)
roughness={}
for name,m in [('shoulder_axilla',D['shoulder_mask']&free),('knee_lowerleg',D['leg_mask'])]:
 roughness[name]={'before_mean_one_ring_residual':float(np.linalg.norm(lpa[m],axis=1).mean()),'after_mean_one_ring_residual':float(np.linalg.norm(lpb[m],axis=1).mean()),'meaning':'Fairing mechanical diagnostic, not art acceptance'}
report={'task':'MORWEN-LOCAL-SURFACE-01','blender':bpy.app.version_string,'vertices':len(a),'faces':len(f),'changed_vertices':int((delta>1e-7).sum()),'max_world_delta':float(delta.max()),'topology_preserved':True,'quads':sum(len(q)==4 for q in f),'boundary_edges':sum(c==1 for c in edges.values()),'nonmanifold_edges_over_2':sum(c>2 for c in edges.values()),'protected_regions':protection,'chest_measurement_band_vertices':int(ch.sum()),'chest_band_vertices_changed':changed_ch,'entire_chest_unchanged':False,'chest_bbox_max_delta':float(abs(chest_bbox_after-chest_bbox_before).max()),'measurements':metrics,'one_ring_diagnostics':roughness,'normal_angle_flags_vs_pre_cage_source_before':int(bad0.sum()),'normal_angle_flags_vs_pre_cage_source_after':int(bad1.sum()),'normal_angle_flags_resolved':int((bad0&~bad1).sum()),'normal_angle_flags_new':int((~bad0&bad1).sum()),'new_zero_area_first_triangles':int(((areas_b<1e-12)&(areas_a>=1e-12)).sum()),'normal_flags_are_not_proof_of_self_intersection':True,'G1_body_reference':'PASS','G2':'FAIL','G3_character':'NOT_RUN','G3_reopen_topology_protection_screen':'PASS','G3_normal_diagnostic':'FAIL','G4':'NOT_RUN','reference_SHA_rechecked':False,'new_source_downloaded':False}
assert report['chest_bbox_max_delta']<1e-6
output=Path(os.environ.get('MORWEN_LOCAL_QA_OUTPUT',str(QA/'local-technical-qa.json')));output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
