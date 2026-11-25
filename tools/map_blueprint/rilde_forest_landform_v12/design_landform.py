"""Area-scale bank/forest design feasibility, no native or canon edits."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union
from scipy.spatial.distance import cdist
from scipy.interpolate import CubicHermiteSpline
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent; P,A=map(Path,sys.argv[1:3]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653'];assert [sha(P),sha(A)]==expected
S=trimesh.load(P,force='scene',process=False);R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def mesh(name):
 t,g=S.graph[name];m=S.geometry[g];return trimesh.transform_points(m.vertices,t)@R,m.faces
polys=[];planes=[];grids=[]
for name in ['RIVER_CORRIDOR','MOSS_FOREST_A1']:
 v,f=mesh(name);t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=-n[:,:2]/n[:,2,None];polys.extend(sh.polygons(t[:,:,:2]));planes.extend(np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)]);grids.append((v,f))
polys=np.array(polys,dtype=object);planes=np.array(planes);tree=sh.STRtree(polys);domain=unary_union(polys);wv,wf=mesh('RIVER_WATER_CLIPPED');wet=unary_union(sh.polygons(wv[wf][:,:,:2]));B=np.load(A);end=B['road_xy'][0,4];endrow=B['road_z'][0];en=(B['road_xy'][0,-1]-B['road_xy'][0,0])/2;ed=np.array([en[1],-en[0]])
def z(q):
 q=np.asarray(q);a,b=tree.query(sh.points(q),predicate='intersects');o=np.full(len(q),np.nan);o[a]=(planes[b,:2]*q[a]).sum(1)+planes[b,2];assert np.isfinite(o).all();return o

def shore(y):return LineString([(225,float(y)),(375,float(y))]).intersection(wet).bounds[2]
def envelope(q,points,h,k):
 lo=np.empty(len(q));hi=lo.copy()
 for i in range(0,len(q),512):
  d=cdist(q[i:i+512],points)*k;lo[i:i+512]=np.max(h-d,axis=1);hi[i:i+512]=np.min(h+d,axis=1)
 return lo,hi
# Broad area between east bank and forest, not a narrow offset strip. Keep all wet geometry and prior V03 trail.
# Include exact water-boundary y breakpoints, protect north/south ends, outer eastern boundary.
ys=np.unique(np.r_[np.arange(-250,-100+.01,.5),wv[:,1][(wv[:,1]>-250)&(wv[:,1]<-100)]]);ys=np.array([ys[0]]+[x for i,x in enumerate(ys[1:],1) if x-ys[i-1]>1e-6]);edge=np.array([shore(y) for y in ys]);
# At y>-100 A1 unavailable; east boundary 400 is inside A1 for whole sampled domain.
u=np.linspace(0,1,153);X=edge[:,None]+(400-edge[:,None])*u;Y=np.broadcast_to(ys[:,None],X.shape);Q=np.stack([X,Y],-1);H=z(Q.reshape(-1,2)).reshape(X.shape);N,M=H.shape
# Existing road/shoulder polygon and exact V03 entry section. All V03 footprint protected from broad landform modification (not from prior design).
old=unary_union([Polygon(np.vstack([B[k][:,0],B[k][::-1,-1]])) for k in ['road_xy','left_xy','right_xy']]);pflat=Q.reshape(-1,2);oldmask=sh.covers(old,sh.points(pflat)).reshape(H.shape)
fixed=np.zeros_like(H,dtype=bool);fixed[:,0]=True;fixed[:,-1]=True;fixed[[0,-1]]=True;fixed|=oldmask
# Road as a whole-area breakline. Start near east shoreline, with a flat staging cross-section above water.
# Profile uses smooth 3m end blending and exact target full-width V03 terminal row.
def route(y0):
 start=np.array([shore(y0)+3,y0]);L0=np.linalg.norm(end-start);direct=(end-start)/L0;der=np.array([direct*L0,ed*L0]);C=CubicHermiteSpline([0,1],np.stack([start,end]),der,axis=0);t=np.linspace(0,1,4001);v=C(t);ar=np.r_[0,np.cumsum(np.linalg.norm(np.diff(v,axis=0),axis=1))];s=np.linspace(0,ar[-1],int(np.ceil(ar[-1]/.25))+1);tt=np.interp(s,ar,t);c=C(tt);d=C.derivative()(tt);d/=np.linalg.norm(d,axis=1)[:,None];n=np.c_[-d[:,1],d[:,0]];n[-1]=en;off=np.linspace(-1,1,9);xy=c[:,None,:]+off[None,:,None]*n[:,None,:];xy[-1]=B['road_xy'][0];h0=4+.012*(y0+250)+.24;w=np.minimum(np.minimum(s/3,(s[-1]-s)/3),1);w=np.clip(w,0,1);w=w*w*(3-2*w);inc=np.linalg.norm(np.diff(xy,axis=0),axis=2).min(1)*(w[1:]+w[:-1])/2;f=np.r_[0,np.cumsum(inc)];f/=f[-1];zz=h0+(endrow[4]-h0)*f;blend=np.clip((s-s[-1]+3)/3,0,1);blend=blend*blend*(3-2*blend);Z=zz[:,None]+blend[:,None]*(endrow-endrow[4]);Z[-1]=endrow
 i=(np.arange(len(s)-1)[:,None]*9+np.arange(8)).ravel();ff=np.stack([np.stack([i,i+9,i+10],1),np.stack([i,i+10,i+1],1)],1).reshape(-1,3);V=np.dstack([xy,Z]).reshape(-1,3);tr=V[ff];nn=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);g=-nn[:,:2]/nn[:,2,None];dd=np.repeat(d[:-1],16,axis=0);dn=np.c_[-dd[:,1],dd[:,0]];da=np.repeat(np.arccos(np.clip((d[:-1]*d[1:]).sum(1),-1,1)),16);bound=2*np.linalg.norm(g,axis=1)*np.sin(da/2);foot=Polygon(np.vstack([xy[:,0],xy[::-1,-1]]));return s,xy,Z,dict(y0=y0,start_xy=start.tolist(),length_m=float(s[-1]),start_z_m=h0,long_bound_pct=float(100*np.max(abs((g*dd).sum(1))+bound)),cross_bound_pct=float(100*np.max(abs((g*dn).sum(1))+bound)),folds=int(np.count_nonzero(nn[:,2]<=0)),wet_overlap_m2=foot.intersection(wet).area,old_overlap_m2=foot.intersection(old).area,outside_m2=foot.difference(domain).area)
# Road fixed elevation influence across entire bank. Bound constraints against exact sampled protected boundaries.
# Only road outer edges plus endpoints are needed for the support field; road interior remains exact separate contract.
attempts=[];best=None
for y0 in [-125.,-120.,-115.]:
 s,xy,Z,rr=route(y0);rxy=np.vstack([xy[:,0],xy[:,-1],xy[0,1:-1],xy[-1,1:-1]]);rz=np.r_[Z[:,0],Z[:,-1],Z[0,1:-1],Z[-1,1:-1]];fx=Q[fixed];fz=H[fixed]
 for k in [.45,.55,.65]:
  l,h=envelope(fx,rxy,rz,k);conf=np.maximum(l-fz,fz-h);mx=float(max(0,conf.max()));rec={**rr,'support_limit_pct':k*100,'protected_sample_conflicts':int(np.count_nonzero(conf>1e-5)),'max_protected_conflict_m':mx};attempts.append(rec);print(rec,flush=True)
  # A fixed-point conflict at the existing road approach is allowed ONLY for prior design vs source: do not silently ignore.
  if rr['long_bound_pct']<=15 and rr['cross_bound_pct']<=10 and rr['folds']==0 and rr['wet_overlap_m2']<1e-8 and rr['old_overlap_m2']<1e-8 and rr['outside_m2']<1e-8:
   rank=(mx>1e-5,mx,k,rr['length_m']);
   if best is None or rank<best[0]:best=(rank,rec,s,xy,Z,rxy,rz)
assert best is not None,'No plan candidate meets road predicates'
_,rec,s,xy,Z,rxy,rz=best;k=rec['support_limit_pct']/100;lo,hi=envelope(pflat,rxy,rz,k);lo=lo.reshape(H.shape);hi=hi.reshape(H.shape);assert np.max(lo-hi)<1e-8;T=np.clip(H,lo,hi);T[fixed]=H[fixed];delta=T-H
# Audit actual proposed support triangles, excluding the road and old V03 footprint (separate design surfaces).
i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();ff=np.stack([np.stack([i,i+1,i+M+1],1),np.stack([i,i+M+1,i+M],1)],1).reshape(-1,3);V=np.dstack([Q,T]).reshape(-1,3);tri=V[ff];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);assert (normal[:,2]>0).all();sl=np.linalg.norm(normal[:,:2]/normal[:,2,None],axis=1);src=np.dstack([Q,H]).reshape(-1,3)[ff];nn=np.cross(src[:,1]-src[:,0],src[:,2]-src[:,0]);base=np.linalg.norm(nn[:,:2]/nn[:,2,None],axis=1);foot=Polygon(np.vstack([xy[:,0],xy[::-1,-1]]));cent=tri.mean(1);eligible=~sh.covers(foot.union(old),sh.points(cent[:,:2]));changed=np.max(abs(delta.ravel()[ff]),axis=1)>1e-6;check=eligible&changed;area=normal[:,2]/2;dz=delta.ravel()[ff].mean(1);rec.update(support_grid_samples=int(H.size),support_fixed_samples=int(fixed.sum()),support_changed_samples=int(np.count_nonzero(abs(delta)>1e-6)),support_changed_triangles=int(check.sum()),support_max_changed_grade_pct=float(100*sl[check].max()),support_max_existing_same_triangles_pct=float(100*base[check].max()),support_triangles_above_50_pct=int(np.count_nonzero(check&(sl>.5+1e-9))),support_max_cut_m=float(-delta.min()),support_max_fill_m=float(delta.max()),approx_cut_m3=float(np.sum(area[eligible]*np.maximum(-dz[eligible],0))),approx_fill_m3=float(np.sum(area[eligible]*np.maximum(dz[eligible],0))),fixed_residual_m=float(abs(delta[fixed]).max()),road_endpoint_xyz_residual_m=float(max(abs(xy[-1]-B['road_xy'][0]).max(),abs(Z[-1]-endrow).max())))
# Terrain field is an overlapping design diagnostic, not final partition. No claim of seam at interpolated road boundary.
np.savez_compressed(O/'bank_landform_v12.npz',xy=Q,source_z=H,design_z=T,fixed=fixed,road_xy=xy,road_z=Z,road_s=s);assert np.array_equal(np.load(O/'bank_landform_v12.npz')['design_z'],T);assert [sha(P),sha(A)]==expected
fig,(a,b,c)=plt.subplots(1,3,figsize=(16,6),layout='constrained');im=a.pcolormesh(X,Y,H,cmap='terrain',shading='auto');a.plot(edge,ys,c='#467a98');a.plot(*xy[:,4].T,c='#332819',lw=2);a.set(aspect='equal',title='A | Existing bank and proposed alignment',xlabel='X (m)',ylabel='Y (m)');fig.colorbar(im,ax=a,label='Elevation (m)');im=b.pcolormesh(X,Y,delta,cmap='RdBu',shading='auto',vmin=-max(abs(delta).max(),.01),vmax=max(abs(delta).max(),.01));b.plot(*xy[:,4].T,c='#222',lw=1);b.set(aspect='equal',title='B | Area-scale correction field',xlabel='X (m)',ylabel='Y (m)');fig.colorbar(im,ax=b,label='Design − source (m)');c.plot(s,z(xy[:,4]),'--',label='Measured existing ground');c.plot(s,Z[:,4],label='Proposed walking grade');c.set(title='C | Route longitudinal section',xlabel='Station (m)',ylabel='Z (m)');c.grid(alpha=.2);c.legend(fontsize=8);fig.suptitle('MOSS FOREST V12 | AREA-SCALE RIVER BANK DESIGN — NOT NATIVE');fig.savefig(O/'bank_landform_v12.png',dpi=150);plt.close(fig)
q=dict(status='AREA_SCALE_FEASIBILITY_HOLD',inputs_sha256=expected,frame='provisional X east Y north Z up metres',attempts=attempts,selected=rec,limits=['Support field overlaps road design and is not a conforming partition; explicit road boundary only, not a welded seam. Protected samples at original terrain; continuous interpolation not certified. Area and cut/fill estimates use raster triangle centroids to exclude road/old V03.','Start 3m east of water, 0.24m above local water, not proof of a walkable shore shelf. Existing native bank slopes may exceed the assumed 50% natural slope. No formal CG, actual terrain, independent D4, Blender, navigation or adoption.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'bank_landform_v12.npz',O/'bank_landform_v12.png']});(O/'bank_landform_v12.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(rec,indent=2))
