"""V13 sampled design boundary contract; no native production or welding."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,shapely as sh
from shapely.geometry import Polygon,LineString
from scipy.spatial.distance import cdist
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent
P,V,Q=map(Path,sys.argv[1:4]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['1a866ca1770c8a2a480b6000596b6b5f98319473b703128963238df62979b7fb','d1e76b00a3f5e09b230f39af3cfa812b55255c5e60680b6e81316da1bbcdaf1c','4103b8cd1e974677bf2c7134622542ceefda78e43852fbd27d120c9b98cc5175'];assert list(map(sha,(P,V,Q)))==expected
T=np.load(P);D=json.loads(V.read_text());G=json.loads(Q.read_text())['geometry'];A=T['road_xyz'];C0=T['fixed_constraints_xyz'];kind=T['fixed_constraints_kind'];x,y=T['x'],T['y'];Z0=T['z_design'];X,Y=np.meshgrid(x,y);mask=np.isfinite(Z0);xy=np.c_[X[mask],Y[mask]]
edge=np.vstack([A[:,0],A[-1,1:],A[-2::-1,-1],A[0,-2:0:-1],A[:1,0]]);R=sh.set_precision(Polygon(edge[:,:2]),1e-9);P0=sh.set_precision(Polygon(G['apron_polygon_xy']),1e-9);rem=Polygon(D['apron_remaining_xy']);assert rem.symmetric_difference(P0.difference(R)).area<1e-7
st=edge[:-1,:2];vv=edge[1:,:2]-st;den=(vv*vv).sum(1);sel=np.linalg.norm(st-[-170,-205],axis=1)<12;st,vv,den,z0,dz=st[sel],vv[sel],den[sel],edge[:-1,2][sel],np.diff(edge[:,2])[sel]
def height(p):
 d=np.asarray(p)[:,None,:]-st;u=np.clip((d*vv).sum(2)/den,0,1);ds=((d-u[:,:,None]*vv)**2).sum(2);i=ds.argmin(1);j=np.arange(len(i));t=np.clip(np.sqrt(ds[j,i])/.75,0,1);return 2+(z0[i]+u[j,i]*dz[i]-2)*(1-t*t*(3-2*t))
outer=sh.set_precision(LineString(G['apron_polygon_xy'][3:]),1e-9).difference(R);lines=[l for l in sh.get_parts(outer) if l.geom_type=='LineString'];assert lines
pts=[]
for l in lines:
 for a,b in zip(np.array(l.coords)[:-1],np.array(l.coords)[1:]):
  n=max(1,int(np.ceil(np.linalg.norm(b-a)/.025)));pts.extend(np.linspace(a,b,n+1))
B=np.unique(np.array(pts),axis=0);H=height(B);BC=np.c_[B,H];assert np.isfinite(H).all()
coast=LineString(G['quay_water_edge_xy']);oldwater=(kind=='apron')&(sh.distance(sh.points(C0[:,:2]),coast)<1e-7);keep=(kind!='apron')|oldwater;C=np.vstack([C0[keep],BC]);K=np.r_[kind[keep],np.repeat('apron_v12',len(BC))]
S=.5;bad=0;worst=0.
for i in range(0,len(C),256):
 a=C[i:i+256];d=cdist(a[:,:2],C[:,:2]);err=abs(a[:,2,None]-C[None,:,2])-S*d;bad+=int((err>1e-5).sum());worst=max(worst,float(err.max()))
lo=np.empty(len(xy));hi=lo.copy()
for i in range(0,len(xy),128):
 p=xy[i:i+128];d=cdist(p,C[:,:2]);lo[i:i+len(p)]=(C[:,2]-S*d).max(1);hi[i:i+len(p)]=(C[:,2]+S*d).min(1)
conf=lo>hi+1e-5;print('pair conflicts',bad,worst,'raster conflicts',conf.sum(),flush=True)
if bad or conf.any():raise RuntimeError('Incompatible fixed samples; no output accepted')
Z=Z0.copy();Z[mask]=np.clip(Z0[mask],lo,hi);L=Z.copy();L[mask]=lo
for it in range(100):
 old=Z.copy();new=Z.copy()
 for j,i in [(0,1),(1,0),(1,1),(1,-1),(0,-1),(-1,0),(-1,-1),(-1,1)]:
  a=(slice(max(0,j),len(y)+min(0,j)),slice(max(0,i),len(x)+min(0,i)));b=(slice(max(0,-j),len(y)-max(0,j)),slice(max(0,-i),len(x)-max(0,i)));new[a]=np.where(np.isfinite(old[a])&np.isfinite(old[b]),np.minimum(new[a],old[b]+S*.5*np.hypot(i,j)),new[a])
 Z=np.maximum(new,L)
 if np.nanmax(abs(Z-old))<1e-10:break
raster_excess=float(max(0,np.max(lo-Z[mask]),np.max(Z[mask]-hi)));assert raster_excess<1e-8
sl=[]
for j,i in [(0,1),(1,0),(1,1),(1,-1)]:
 a=Z[max(0,j):len(y)+min(0,j),max(0,i):len(x)+min(0,i)];b=Z[max(0,-j):len(y)-max(0,j),max(0,-i):len(x)-max(0,i)];d=abs(a-b)/(.5*np.hypot(i,j));sl.extend(d[np.isfinite(d)])
sl=np.array(sl);assert sl.max()<=S+1e-8
res=float(np.max(abs(C[-len(B):,2]-height(B))));assert res==0
out=O/'harbor_terrain_design_v13.npz';np.savez_compressed(out,x=x,y=y,z_design=Z,z_assumed_baseline=T['z_assumed_baseline'],road_xyz=A,apron_xy=T['apron_xy'],fixed_constraints_xyz=C,fixed_constraints_kind=K,landward_boundary_xyz=BC)
re=np.load(out);assert np.array_equal(re['road_xyz'],A) and np.array_equal(re['landward_boundary_xyz'],BC) and np.array_equal(re['z_design'],Z,equal_nan=True)
delta=Z-Z0
q=dict(status='SAMPLED_BOUNDARY_CONTRACT_NOT_ADOPTED',inputs_sha256=expected,checks=dict(old_fixed_count=len(C0),new_fixed_count=len(C),boundary_samples=len(B),boundary_max_spacing_m=.025,boundary_max_deviation_from_flat_m=float(max(abs(H-2))),explicit_boundary_residual_m=res,fixed_pair_conflicts=bad,max_fixed_pair_excess_m=worst,raster_conflicts=int(conf.sum()),raster_samples=int(mask.sum()),raster_envelope_max_excess_m=raster_excess,neighbor_slope_samples=len(sl),max_sampled_slope_pct=float(sl.max()*100),neighbor_slope_exceed_count=int((sl>S+1e-8).sum()),changed_raster_samples=int((abs(delta)>1e-10).sum()),max_raster_change_m=float(np.nanmax(abs(delta))),relaxation_iterations=it+1,road_exact=True,input_unchanged=list(map(sha,(P,V,Q)))==expected,npz_reopen_exact=True),method='Replace old landward apron samples with V12 heights at <=25mm spaced points; keep old water-facing apron and all non-apron constraints; clamp V11 raster and relax 8-neighbor slopes. Explicit boundary and raster are separate constraints, no claim interpolated surface/weld.',limits=['No actual terrain outside reconstructed village, no CG pixels, no independent D4.','No continuous mesh triangulation or seam interpolation validation. 50% is an assumed sampled slope limit, not geotechnical certification.','Existing cut/fill baseline remains artificial; no Blender or game integration.'],gates=dict(D0='PARTIAL',D1='PARTIAL',D2='PARTIAL',D3='HOLD_ORIGINAL_TERRAIN_AND_D4',D4='NOT_RUN',G1='BLOCKED',G2='NOT_RUN',G3='NOT_RUN_NATIVE',G4='NOT_RUN'))
fig,(a,b)=plt.subplots(1,2,figsize=(12,5),layout='constrained');im=a.pcolormesh(X,Y,Z,cmap='terrain',shading='auto');a.plot(*P0.exterior.xy,c='#554738',lw=1);a.plot(*R.exterior.xy,c='#554738',lw=.8);a.scatter(B[:,0],B[:,1],s=2,c='#12746c');a.set(aspect='equal',xlim=(-210,-90),ylim=(-240,-125),title='A | Reconciled design elevation',xlabel='X east (m)',ylabel='Y north (m)');fig.colorbar(im,ax=a,label='Z (m)',shrink=.7);b.plot(*P0.exterior.xy,c='#82725c');b.plot(*R.exterior.xy,c='#65523d');sc=b.scatter(B[:,0],B[:,1],c=(H-2)*1000,s=8,cmap='coolwarm');b.set(aspect='equal',xlim=(-191,-160),ylim=(-227,-182),title='B | Explicit landward boundary heights',xlabel='X east (m)',ylabel='Y north (m)');fig.colorbar(sc,ax=b,label='Offset from +2m (mm)',shrink=.7);fig.suptitle('RILDE HARBOUR V13 | BOUNDARY CONTRACT — DESIGN ONLY');fig.savefig(O/'harbor_boundary_v13.png',dpi=150);plt.close(fig)
q['outputs']=dict(npz_sha256=sha(out),png_sha256=sha(O/'harbor_boundary_v13.png'),script_sha256=sha(Path(__file__)));assert q['checks']['input_unchanged'];(O/'harbor_boundary_v13.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
