"""Correct V06 forced terminal tangent, audit candidate ribbon, no native edit."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy.interpolate import CubicHermiteSpline,PchipInterpolator
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;P,V,A=map(Path,sys.argv[1:4]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','3aee7f0034968cc9fc96a610df15f96f7b0d93ff078bd19f7e8c79508a9079e6','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653'];assert list(map(sha,[P,V,A]))==expected
S=trimesh.load(P,force='scene',process=False);R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def mesh(name):
 t,g=S.graph[name];m=S.geometry[g];return trimesh.transform_points(m.vertices,t)@R,m.faces
polys=[];planes=[]
for name in ['RIVER_CORRIDOR','MOSS_FOREST_A1']:
 v,f=mesh(name);t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);g=-n[:,:2]/n[:,2,None];polys.extend(sh.polygons(t[:,:,:2]));planes.extend(np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)])
polys=np.array(polys,dtype=object);planes=np.array(planes);tree=sh.STRtree(polys);domain=unary_union(polys);wv,wf=mesh('RIVER_WATER_CLIPPED');wet=unary_union(sh.polygons(wv[wf][:,:,:2]));B=np.load(V);C=np.load(A);old=B['xy'];oc=old[:,4];end=C['road_xy'][0,4];row=C['road_z'][0];en=(C['road_xy'][0,-1]-C['road_xy'][0,0])/2;ed=np.array([en[1],-en[0]]);trail=Polygon(np.vstack([C['left_xy'][:,-1],C['right_xy'][::-1,-1]]));h0=B['design_z'][0,4]
def z(x):
 shape=x.shape[:-1];x=x.reshape(-1,2);a,b=tree.query(sh.points(x),predicate='intersects');o=np.full(len(x),np.nan);o[a]=(planes[b,:2]*x[a]).sum(1)+planes[b,2];return o.reshape(shape)
def faces(N,M):
 i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();return np.stack([np.stack([i,i+M,i+M+1],1),np.stack([i,i+M+1,i+1],1)],1).reshape(-1,3)
def measure(Q,Z,d):
 N,M=Z.shape;t=np.dstack([Q,Z]).reshape(-1,3)[faces(N,M)];nn=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);g=-nn[:,:2]/nn[:,2,None];dd=np.repeat(d[:-1],2*(M-1),axis=0);dn=np.c_[-dd[:,1],dd[:,0]];da=np.repeat(np.arccos(np.clip(np.sum(d[:-1]*d[1:],axis=1),-1,1)),2*(M-1));bound=2*np.linalg.norm(g,axis=1)*np.sin(da/2);return dict(folded_triangles=int(np.count_nonzero(nn[:,2]<=0)),min_signed_double_area_m2=float(nn[:,2].min()),max_long_pct=float(100*np.max(abs((g*dd).sum(1))+bound)),max_cross_pct=float(100*np.max(abs((g*dn).sum(1))+bound)))
oldn=(old[:,-1]-old[:,0])/2;oldd=np.c_[oldn[:,1],-oldn[:,0]];before=measure(old,B['design_z'],oldd)
# Use a cubic Hermite terminal replacement with an actual derivative matching V03, not a forced final normal. Preserve prior PCHIP centerline until join.
u=-oc[:,1];base=PchipInterpolator(u,oc[:,0]);attempts=[];best=None
for run in [8,12,16,20]:
 a=u[-1]-run;last=CubicHermiteSpline([a,u[-1]],[float(base(a)),end[0]],[float(base.derivative()(a)),ed[0]/(-ed[1])]);yy=np.linspace(u[0],u[-1],5001);x=np.where(yy<=a,base(yy),last(yy));cc=np.c_[x,-yy];ss=np.r_[0,np.cumsum(np.linalg.norm(np.diff(cc,axis=0),axis=1))];s=np.linspace(0,ss[-1],int(np.ceil(ss[-1]/.25))+1);y=np.interp(s,ss,yy);c=np.c_[np.where(y<=a,base(y),last(y)),-y];der=np.where(y<=a,base.derivative()(y),last.derivative()(y));d=np.c_[der,-np.ones(len(y))];d/=np.linalg.norm(d,axis=1)[:,None];n=np.c_[-d[:,1],d[:,0]];off=np.linspace(-1,1,9);Q=c[:,None,:]+off[None,:,None]*n[:,None,:];H=z(Q);poly=Polygon(np.vstack([Q[:,0],Q[::-1,-1]]));r=dict(terminal_run_m=run,valid_polygon=bool(poly.is_valid),outside_samples=int(np.isnan(H).sum()))
 if not poly.is_valid or not np.isfinite(H).all():attempts.append(r);continue
 w=np.clip(np.minimum(s/3,(s[-1]-s)/3),0,1);w=w*w*(3-2*w);inc=np.minimum(np.linalg.norm(np.diff(Q,axis=0),axis=2).min(1),np.diff(s))*(w[1:]+w[:-1])/2;uu=np.r_[0,np.cumsum(inc)];uu/=uu[-1];zz=h0+(row[4]-h0)*uu;t=np.clip((s-s[-1]+3)/3,0,1);t=t*t*(3-2*t);Z=zz[:,None]+t[:,None]*(row-row[4]);Z[-1]=row;delta=Z-H;angles=np.unwrap(np.arctan2(d[:,1],d[:,0]));radius=np.diff(s)/np.maximum(abs(np.diff(angles)),1e-15);r.update(measure(Q,Z,d));r.update(length_m=float(s[-1]),min_sampled_radius_m=float(radius.min()),wet_overlap_m2=poly.intersection(wet).area,forest_overlap_m2=poly.intersection(trail).area,outside_m2=poly.difference(domain).area,max_cut_m=float(max(0,-delta.min())),max_fill_m=float(max(0,delta.max())),seam_xyz_error_m=float(np.max(abs(np.dstack([Q,Z])[-1]-np.c_[C['road_xy'][0],row]))));r['pass_ribbon']=bool(r['folded_triangles']==0 and r['max_long_pct']<=15 and r['max_cross_pct']<=10 and max(r['wet_overlap_m2'],r['forest_overlap_m2'],r['outside_m2'])<1e-8 and r['seam_xyz_error_m']<1e-8);attempts.append(r);print(r,flush=True)
 if r['pass_ribbon'] and (best is None or r['min_sampled_radius_m']>best[0]['min_sampled_radius_m']):best=(r,s,Q,H,Z)
assert list(map(sha,[P,V,A]))==expected
q=dict(status='HOLD_NO_PASS' if best is None else 'RIBBON_ONLY_PASS_SHOULDERS_LANDING_HOLD',inputs_sha256=expected,before=before,attempts=attempts,selected=None if best is None else best[0],source_unchanged=True,limitations=['Sampled ribbon repair only. No native ground edit or continuous curvature proof. Full shoulder and landing redesign required; D4 not run.'])
fig,ax=plt.subplots(figsize=(8,6),layout='constrained');ax.plot(*oc[-80:].T,'--',label='V06 center');ax.plot(*old[-80:,0].T,c='#aa4433');ax.plot(*old[-80:,-1].T,c='#aa4433',label='V06 edges');
if best:
 r,s,Q,H,Z=best;np.savez_compressed(O/'bank_route_v08.npz',station=s,xy=Q,source_z=H,design_z=Z);assert np.array_equal(np.load(O/'bank_route_v08.npz')['design_z'],Z);ax.plot(*Q[-80:,4].T,c='#214c32',label='V08 center');ax.plot(*Q[-80:,0].T,c='#33724b');ax.plot(*Q[-80:,-1].T,c='#33724b',label='V08 edges')
ax.plot(*C['road_xy'][:30,4].T,c='#345b91',label='V03 continuation');ax.set(aspect='equal',title='V06 terminal tangent repair — design audit',xlabel='X (m)',ylabel='Y (m)');ax.grid(alpha=.2);ax.legend();fig.savefig(O/'bank_route_v08.png',dpi=150);plt.close(fig);q['outputs']={p.name:sha(p) for p in [Path(__file__),O/'bank_route_v08.png']+([O/'bank_route_v08.npz'] if best else [])};(O/'bank_route_v08.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
