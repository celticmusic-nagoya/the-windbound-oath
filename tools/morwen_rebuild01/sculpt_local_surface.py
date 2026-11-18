"""Local differential-surface sculpt, not a full-body coordinate cage.
Uses fixed boundary vertices + local anatomical displacement handles and a
mesh-adjacency bi-Laplacian fairing solve. No source acquisition or global fit.
Python-authored vertex sculpt; no manual GUI sculpt or retopology is claimed.
"""
import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix,eye,diags
from scipy.sparse.linalg import spsolve
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/qa/morwen-rebuild-01/body-local-v01';OUT.mkdir(parents=True,exist_ok=True)
j=json.loads(Path('/tmp/morwen-local-source.json').read_text());v=np.array(j['coords']);faces=j['faces']
old=np.load(ROOT/'docs/qa/morwen-rebuild-01/body-fit-v02/vertex-delta.npz')['before_world']
x0,y0,z0=old.T;x,y,z=v.T
# Hard protected central thoracic surface, whole waist/pelvis, hands/feet/head.
shoulder=(z0>.65)&(z0<.812)&(abs(x0)>.035)
central_chest=(z0>=.65)&(z0<=.745)&((abs(x0)<.058)|((y0<.005)&(abs(x0)<.085)))
shoulder &= ~central_chest
leg=(z0>.055)&(z0<.43)
free=shoulder|leg
# Preserve before/after chest measurement extents exactly (same band vertices).
chest_band=(abs(z0-.7)<.008)&(abs(x0)<.10)
pinned_extrema=[]
for axis in range(3):
 ids=np.where(chest_band)[0]
 pinned_extrema += [int(ids[np.argmin(v[ids,axis])]),int(ids[np.argmax(v[ids,axis])])]
free[pinned_extrema]=False
# Original topology defines the editing operator; outside patch is hard pinned.
edges=set()
for f in faces:
 for a,b in zip(f,f[1:]+f[:1]):edges.add(tuple(sorted((a,b))))
row=[];col=[]
for a,b in edges:row.extend([a,b]);col.extend([b,a])
n=len(v);adj=coo_matrix((np.ones(len(row)),(row,col)),shape=(n,n)).tocsr()
deg=np.array(adj.sum(1)).ravel();L=eye(n,format='csr')-diags(1/deg)@adj
# Selected shoulders: lift the lateral roundness, relax the pointed superior tip.
target=v.copy();ax=abs(x);sg=np.sign(x)
w=np.exp(-((z-.805)/.045)**2-((ax-.079)/.036)**2)
target[shoulder,0] += (sg*.013*w)[shoulder]
target[shoulder,2] -= (.005*np.exp(-((z-.824)/.018)**2)*w)[shoulder]
# Knee–shin sculpt handles: correct centers towards the observed standing line.
# Strokes remain local to each leg, with a fixed foot/thigh boundary.
k=np.exp(-((z-.327)/.065)**2);c=np.exp(-((z-.235)/.080)**2)
total=k+c;envelope=np.minimum(1.,total);den=np.maximum(total,1e-12)
dx=-(.0105*k+.008*c)/den*envelope
dy=-(.020*k+.009*c)/den*envelope
center=.052
radial=(ax-center)
target[leg,0]+=(sg*(dx-.07*radial*k))[leg]
target[leg,1]+=dy[leg]
# Softly flatten the patellar prominence and calf plane changes, not the torso.
data_weight=np.full(n,.035);data_weight[leg]=.08
# Anatomical handles retain position while unconstrained neighbours fair curvature.
data_weight[shoulder] += .15*w[shoulder]
data_weight[leg] += .12*envelope[leg]
ids=np.where(free)[0];fixed=np.where(~free)[0]
# Fair only rows touching the patch so protected regions are never re-fitted.
rows=np.where((np.array(adj[:,ids].sum(1)).ravel()>0)|free)[0]
Lf=L[rows][:,ids];Lc=L[rows][:,fixed]
A=(Lf.T@Lf)*6 + diags(data_weight[ids])
boundary=-(Lf.T@(Lc@v[fixed]))*6
out=v.copy()
for axis in range(3):out[ids,axis]=spsolve(A,boundary[:,axis]+data_weight[ids]*target[ids,axis])
# Immutable chest-band bounding planes prohibit regression while allowing axilla neighbours.
for axis in range(3):
 low,high=v[chest_band,axis].min(),v[chest_band,axis].max()
 movable=chest_band&free;out[movable,axis]=np.clip(out[movable,axis],low,high)
assert np.array_equal(out[~free],v[~free])
assert np.isfinite(out).all()
np.savez(OUT/'local-edit.npz',before_world=v,after_world=out,free_mask=free,shoulder_mask=shoulder,leg_mask=leg,central_chest_mask=central_chest,chest_band=chest_band,original_source_world=old)
(OUT/'local-targets.json').write_text(json.dumps({'method':'Pinned-boundary differential local surface sculpt (adjacency bi-Laplacian)','manual_GUI_sculpt':False,'retopology':False,'full_body_cage_executed':False,'source':'body-fit-v02/MORWEN_BODY_FIT_V02_UNAPPROVED.blend','free_vertices':int(free.sum()),'shoulder_patch_vertices':int((shoulder&free).sum()),'leg_patch_vertices':int(leg.sum()),'hard_fixed_vertices':int((~free).sum()),'all_fixed_vertices_exactly_preserved':True,'pinned_chest_band_extrema':pinned_extrema,'reference_notes':'Source Layer0 views have uncalibrated perspective/pose; joint centers inferred. Knee and shoulder target extents use existing measurement table, not new source SHA checks.','solve':'min 6||L X||^2 + sum local_handle_weights||X-target||^2 with hard exterior boundary'},indent=2)+'\n')
print('LOCAL_SURFACE_SCULPT',int((np.linalg.norm(out-v,axis=1)>1e-7).sum()),'fixed',int((~free).sum()))
