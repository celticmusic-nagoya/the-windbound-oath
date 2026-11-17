"""Post-retopology correspondence test; retiring face IDs is not a PASS."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib.tri import Triangulation
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01'
S=json.loads((Q/'source-mesh.json').read_text());C=json.loads((Q/'candidate-mesh.json').read_text());R=json.loads((Q/'quad-patch-recipe.json').read_text());D=np.load(ROOT/'docs/qa/morwen-rebuild-01/body-local-v01/local-edit.npz')
a=np.array(S['world']);b=np.array(C['world']);al=np.array(S['local']);bl=np.array(C['local']);rest=D['original_source_world'];oldfaces=S['faces'];srcids=C['source_vertex_ids'];vmap={sid:i for i,sid in enumerate(srcids)};fmap={sid:i for i,sid in enumerate(C['source_face_ids'])};retired=set(R['retired_source_faces']);free=D['free_mask']
protected=np.where(~free)[0];assert all(int(i) in vmap for i in protected);assert np.array_equal(al[protected],bl[[vmap[int(i)] for i in protected]])
retained_faces=[]
for i,face in enumerate(oldfaces):
 if i not in retired:
  j=fmap[i];assert [srcids[k] for k in C['faces'][j]]==face;retained_faces.append(i)
patch_maps={};old_to_patch={}
for pi,p in enumerate(R['patches']):
 uv=np.array(p['new_uv']);xyz=b[[vmap[k] for k in p['new_source_vertex_ids']]];tri=[];parent=[]
 for j,face in enumerate(p['new_faces']):
  for k in range(1,len(face)-1):tri.append([face[0],face[k],face[k+1]]);parent.append(j)
 tri=np.array(tri);finder=Triangulation(uv[:,0],uv[:,1],tri).get_trifinder();old_uv={sid:np.array(t) for sid,t in zip(p['source_vertex_ids'],p['source_uv'])}
 patch_maps[pi]=(p,uv,xyz,tri,parent,finder,old_uv)
 for fi in p['source_faces']:old_to_patch[fi]=pi

def sample(pi,uvpoint):
 p,uv,xyz,tri,parent,finder,old_uv=patch_maps[pi];ti=int(finder(float(uvpoint[0]),float(uvpoint[1])));assert ti>=0,(p['name'],uvpoint)
 ids=tri[ti];t=uv[ids];M=np.vstack([t.T,np.ones(3)]);weights=np.linalg.solve(M,np.r_[uvpoint,1.]);pos=weights@xyz[ids];normal=np.cross(xyz[ids[1]]-xyz[ids[0]],xyz[ids[2]]-xyz[ids[0]]);normal/=np.linalg.norm(normal)
 return pos,normal,int(parent[ti])
warning=json.loads((Q/'warning15.json').read_text());tracks=[]
for w in warning:
 fi=w['face_id'];pi=old_to_patch[fi];f=oldfaces[fi];p,uv,xyz,tri,parent,finder,old_uv=patch_maps[pi];ref=np.cross(rest[f[1]]-rest[f[0]],rest[f[2]]-rest[f[0]]);ref/=np.linalg.norm(ref);samples=[]
 for weights in ([1/3]*3,[.6,.2,.2],[.2,.6,.2],[.2,.2,.6]):
  point=np.array(weights)@np.array([old_uv[i] for i in f[:3]]);pos,n,face=sample(pi,point);ang=float(np.degrees(np.arccos(np.clip(n@ref,-1,1))));samples.append({'old_triangle_barycentric':weights,'new_patch_face':face,'world_position':pos.tolist(),'angle_vs_original_source_normal':ang,'flag_over_90':ang>90})
 tracks.append({'old_face_id':fi,'patch':p['name'],'old_face_retired':fi not in fmap,'samples':samples,'resolved_at_all_samples':not any(x['flag_over_90'] for x in samples)})
# Track old measurement-band vertices onto the replacement surface where necessary.
new_positions=a.copy();retired_vertex_patch={}
for pi,p in enumerate(R['patches']):
 for sid in p['retired_interior_vertices']:retired_vertex_patch[sid]=pi
for sid in range(len(a)):
 if sid in vmap:new_positions[sid]=b[vmap[sid]]
 elif sid in retired_vertex_patch:
  pi=retired_vertex_patch[sid];new_positions[sid]=sample(pi,patch_maps[pi][-1][sid])[0]
 else:raise AssertionError(sid)
metrics=[]
for name,z,limit,target in [('shoulder_width',.775,None,180),('chest_width',.7,.1,140),('waist_width',.6,.125,100),('pelvis_width',.53,.125,198),('knee_outer_width',.29,None,124)]:
 mask=abs(rest[:,2]-z)<.008
 if limit:mask &=abs(rest[:,0])<limit
 before=float(np.ptp(a[mask,0])*946);after=float(np.ptp(new_positions[mask,0])*946)
 metrics.append({'measurement':name,'target_px':target,'before_px':before,'after_correspondence_px':after,'before_error_px':abs(before-target),'after_error_px':abs(after-target),'no_accuracy_regression_2px_tolerance':abs(after-target)<=abs(before-target)+2})
edges={}
for f in C['faces']:
 for i,j in zip(f,f[1:]+f[:1]):e=tuple(sorted((i,j)));edges[e]=edges.get(e,0)+1
loose=set(range(len(b)))-{i for f in C['faces'] for i in f}
report={'task':'MORWEN-ANATOMICAL-QUAD-PATCH-01','source_vertices':len(a),'candidate_vertices':len(b),'source_faces':len(oldfaces),'candidate_faces':len(C['faces']),'retired_faces':len(retired),'new_patch_faces':sum(len(p['new_faces']) for p in R['patches']),'new_quads':sum(p['quad_count'] for p in R['patches']),'new_triangles':sum(p['triangle_count'] for p in R['patches']),'protected_vertices_exact':len(protected),'retained_exterior_faces_exact':len(retained_faces),'boundary_edges':sum(c==1 for c in edges.values()),'nonmanifold_edges_over2':sum(c>2 for c in edges.values()),'loose_vertices':len(loose),'warning_tracking':'4 old first-triangle barycentric UV samples per warning, evaluated on new actual triangles; not deleted-ID counting','warning15_resolved':sum(x['resolved_at_all_samples'] for x in tracks),'warning15_remaining':sum(not x['resolved_at_all_samples'] for x in tracks),'warnings':tracks,'measurements':metrics,'G2':'NOT_RUN','G3':'NOT_RUN'}
(Q/'correspondence-qa.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('warnings','measurements')});print(metrics)
