"""Read-only design: rounded trail alignment and bounded height correction, not native mesh."""
import hashlib,json,sys,heapq
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import LineString,box
from shapely.ops import unary_union
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent; S=Path(sys.argv[1]); P=Path(sys.argv[2]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)=='e30fb940ed2ca2ce3b82d3ac5dddfa7c390247804df47fa14d4ec3aafdb4fcfd'
T=[('a1',(400,-200,0),'b5e3d099fedbf694d38331bd41ff947bc38f1e48fa9b785d22839c1ff140b19d'),('a2',(500,-300,0),'2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc'),('a3',(600,-400,0),'e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b')];R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
tris=[];planes=[];bounds=[];grids=[]
for k,o,h in T:
 p=S/f'moss_forest_{k}.glb';assert sha(p)==h;m=trimesh.load(p,force='mesh',process=False);v=m.vertices@R+o;f=m.faces;t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=-n[:,:2]/n[:,2,None];tris.extend(sh.polygons(t[:,:,:2]));planes.extend(np.column_stack([g,t[:,0,2]-np.sum(g*t[:,0,:2],axis=1)]));bounds.append(box(*np.r_[v[:,:2].min(0),v[:,:2].max(0)]));grids.append((v,f))
tris=np.array(tris,dtype=object);planes=np.array(planes);tree=sh.STRtree(tris);domain=unary_union(bounds)
old=np.array(json.loads(P.read_text())['route_xy']);start,end=old[[0,-1]]
def z(xy):
 a,b=tree.query(sh.points(xy),predicate='intersects');out=np.full(len(xy),np.nan);out[a]=(planes[b,:2]*xy[a]).sum(1)+planes[b,2];assert np.isfinite(out).all();return out
# Exact circular fillet: first corner only; remaining zigzag removed. Continuous tangent, R=12m.
def rounded(mid,r=12):
 u=(mid-start)/np.linalg.norm(mid-start);v=(end-mid)/np.linalg.norm(end-mid);ang=np.arccos(np.clip(u@v,-1,1));sign=np.sign(np.cross(np.r_[u,0],np.r_[v,0])[2]);t=r*np.tan(ang/2);a=mid-t*u;b=mid+t*v;n=sign*np.array([-u[1],u[0]]);center=a+r*n;ang0=np.arctan2(*(a-center)[::-1]);L1=np.linalg.norm(a-start);L2=r*ang;L3=np.linalg.norm(end-b);L=L1+L2+L3;s=np.linspace(0,L,int(np.ceil(L/.25))+1);q=np.zeros((len(s),2));d=q.copy();i=s<=L1;j=(s>L1)&(s<L1+L2);k=~(i|j);q[i]=start+s[i,None]*u;d[i]=u;theta=ang0+sign*(s[j]-L1)/r;q[j]=center+r*np.c_[np.cos(theta),np.sin(theta)];d[j]=sign*np.c_[-np.sin(theta),np.cos(theta)];q[k]=b+(s[k]-L1-L2)[:,None]*v;d[k]=v;return s,q,d,ang
# Multi-source distance transform on a rectangular graph; lower/upper Lipschitz envelopes.
# Per-edge slope limits stricter than 15/10%, preserve both endpoint profiles exactly.
def adjust(s,xy,H):
 N,M=H.shape;dz=H.copy();dist=np.linalg.norm(np.diff(xy,axis=0),axis=2)*.14;cross=np.linalg.norm(np.diff(xy,axis=1),axis=2)*.09
 def env(A):
  a=A.ravel().copy();pq=[(v,i) for i,v in enumerate(a)];heapq.heapify(pq)
  while pq:
   v,i=heapq.heappop(pq)
   if v>a[i]+1e-12:continue
   j,k=divmod(i,M)
   for ii,w in ((i-M,dist[j-1,k] if j else 0),(i+M,dist[j,k] if j<N-1 else 0),(i-1,cross[j,k-1] if k else 0),(i+1,cross[j,k] if k<M-1 else 0)):
    if w<=0:continue
    nv=v+w
    if nv<a[ii]-1e-12:a[ii]=nv;heapq.heappush(pq,(nv,ii))
  return a.reshape(N,M)
 lo=-env(-H);hi=env(H);# midpoint of upper/lower Lipschitz envelopes, minimax bound
 target=(lo+hi)/2
 # endpoints fixed through compatible constraints propagated from both endpoint rows
 inf=np.full_like(H,1e6);inf[[0,-1]]=H[[0,-1]];upper=env(inf);inf[[0,-1]]=-H[[0,-1]];lower=-env(inf);assert np.max(lower-upper)<1e-8
 target=np.clip(target,lower,upper);assert np.max(abs(target[[0,-1]]-H[[0,-1]]))<1e-8
 return target
attempts=[];best=None
for mid in [np.array([392.5,-262.5]),np.array([395.,-260.]),np.array([405.,-270.])]:
 s,c,d,ang=rounded(mid);normal=np.c_[-d[:,1],d[:,0]];off=np.linspace(-1,1,9);xy=c[:,None,:]+off[None,:,None]*normal[:,None,:];line=LineString(c);foot=line.buffer(1.001,quad_segs=16);outside=foot.difference(domain).area
 if outside>1e-9:attempts.append(dict(mid=mid.tolist(),outside=outside,status='OUTSIDE'));continue
 H=z(xy.reshape(-1,2)).reshape(xy.shape[:2]);Z=adjust(s,xy,H);delta=Z-H;lg=np.max(abs(np.diff(Z,axis=0))/np.linalg.norm(np.diff(xy,axis=0),axis=2))*100;cg=np.max(abs(np.diff(Z,axis=1))/np.linalg.norm(np.diff(xy,axis=1),axis=2))*100
 # Exact piecewise planar triangle gradients on proposed design lattice (not actual altered terrain).
 N,M=H.shape;V=np.dstack((xy,Z)).reshape(-1,3);i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();f=np.stack([np.stack([i,i+M,i+M+1],1),np.stack([i,i+M+1,i+1],1)],1).reshape(-1,3);t=V[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);g=-n[:,:2]/n[:,2,None];dirs=np.repeat(d[:-1],2*(M-1),axis=0);# directional bound over interval tangent rotation by endpoint angle delta
 lon=abs((g*dirs).sum(1));cross=abs((g*np.c_[-dirs[:,1],dirs[:,0]]).sum(1));da=np.repeat(np.arccos(np.clip(np.sum(d[:-1]*d[1:],axis=1),-1,1)),2*(M-1));bound=2*np.linalg.norm(g,axis=1)*np.sin(da/2);ml=float(100*np.max(lon+bound));mc=float(100*np.max(cross+bound));rec=dict(mid=mid.tolist(),length_m=float(s[-1]),radius_m=12,corner_angle_deg=float(np.degrees(ang)),outside_terrain_m2=outside,max_correction_m=float(np.max(abs(delta))),max_cut_m=float(max(0,-delta.min())),max_fill_m=float(max(0,delta.max())),mean_abs_correction_m=float(np.mean(abs(delta))),max_long_sampled_pct=float(lg),max_cross_sampled_pct=float(cg),max_triangle_long_bound_pct=ml,max_triangle_cross_bound_pct=mc,endpoint_residual_m=float(np.max(abs(delta[[0,-1]]))));attempts.append(rec);print(rec,flush=True)
 if ml<=15 and mc<=10 and (best is None or rec['max_correction_m']<best[0]['max_correction_m']):best=(rec,s,c,xy,H,Z,delta)
assert best is not None,'No qualified height design';rec,s,c,xy,H,Z,delta=best;assert all(sha(S/f'moss_forest_{k}.glb')==h for k,o,h in T)
np.savez_compressed(O/'forest_trail_design_v02.npz',station=s,xy=xy,source_z=H,design_z=Z);a=np.load(O/'forest_trail_design_v02.npz');assert np.array_equal(a['design_z'],Z)
q=dict(status='DESIGN_CANDIDATE_NOT_ADOPTED',source_sha256={k:h for k,o,h in T},previous_design_sha256=sha(P),checks=rec,attempts=attempts,station_count=len(s),sample_count=H.size,changed_sample_count=int(np.count_nonzero(abs(delta)>1e-6)),source_unchanged=True,limits=['Read-only proposed road height lattice, not modified native ground. No slope or continuity proof outside the 2m trail, cut/fill tie-in, collision, vegetation or actual altar.','12m radius and grade limits are provisional design choices; D4 independent review required. G1 BLOCKED; G2-G4 NOT_RUN.'])
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(15,5.5),layout='constrained')
for v,f in grids:ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=13,vmax=37,shading='gouraud')
ax.plot(*old.T,'--',c='#a35039',label='V01');ax.plot(*c.T,c='#142e23',lw=2,label='V02');ax.set(aspect='equal',title='A | Alignment comparison',xlabel='X (m)',ylabel='Y (m)');ax.legend();bx.plot(s,H[:,4],label='Measured ground');bx.plot(s,Z[:,4],'--',label='Design grade');bx.set(title='B | Centerline profile',xlabel='Station (m)',ylabel='Z (m)');bx.legend();bx.grid(alpha=.2);im=cx.pcolormesh(s,np.linspace(-1,1,9),delta.T,cmap='RdBu',shading='auto',vmin=-np.max(abs(delta)),vmax=np.max(abs(delta)));cx.set(title='C | Proposed height correction',xlabel='Station (m)',ylabel='Across trail (m)');fig.colorbar(im,ax=cx,label='Design minus source (m)');fig.suptitle('MOSS FOREST V02 | ROUNDED ALIGNMENT — DESIGN ONLY');fig.savefig(O/'forest_trail_v02.png',dpi=150);plt.close(fig);q['outputs']={p.name:sha(p) for p in [Path(__file__),O/'forest_trail_design_v02.npz',O/'forest_trail_v02.png']};(O/'forest_trail_v02.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
