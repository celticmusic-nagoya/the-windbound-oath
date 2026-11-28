"""Read-only feasibility: contour-following graded bank path; not a native edit or accepted landing."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
from scipy.interpolate import PchipInterpolator
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;P,V,A=map(Path,sys.argv[1:4]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','720f3a1598f266b2e0b4671feae76fce1b91ef852924960183c0c7b1ad246f16','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653'];assert [sha(x) for x in [P,V,A]]==expected
S=trimesh.load(P,force='scene',process=False);R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def mesh(name):
 t,g=S.graph[name];m=S.geometry[g];return trimesh.transform_points(m.vertices,t)@R,m.faces
polys=[];planes=[];grids=[]
for name in ['RIVER_CORRIDOR','MOSS_FOREST_A1']:
 v,f=mesh(name);t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=-n[:,:2]/n[:,2,None];polys.extend(sh.polygons(t[:,:,:2]));planes.extend(np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)]);grids.append((v,f))
polys=np.array(polys,dtype=object);planes=np.array(planes);tree=sh.STRtree(polys);domain=unary_union(polys);wv,wf=mesh('RIVER_WATER_CLIPPED');wet=unary_union(sh.polygons(wv[wf][:,:,:2]));B=np.load(A);end=B['road_xy'][0,4];endrow=B['road_z'][0];en=(B['road_xy'][0,-1]-B['road_xy'][0,0])/2;ed=np.array([en[1],-en[0]]);ed/=np.linalg.norm(ed)
def z(x):
 a,b=tree.query(sh.points(x),predicate='intersects');o=np.full(len(x),np.nan);o[a]=(planes[b,:2]*x[a]).sum(1)+planes[b,2];assert np.isfinite(o).all();return o
old=json.loads(V.read_text());attempts=[];best=None
# Only evaluate 3 upstream launch points from V04, each 5m inland. Construct x controls via monotonic measured cross sections following a gradual height profile.
for y0 in [-150.,-155.,-160.]:
 p=np.array([r['candidate_xy'] for r in old['landing']['all_candidates'] if r['shore_xy'][1]==y0][-1]);h0=z(p[None,:])[0];ys=np.linspace(y0,end[1]+10,16);t=(ys-y0)/(end[1]-y0);targets=h0+(endrow[4]-h0)*t;xs=[]
 for y,h in zip(ys,targets):
  xx=np.linspace(310,375,521);hh=z(np.c_[xx,np.full(len(xx),y)]);# monotonic east bank crossing nearest to required height on dry side
  waterline=LineString([(225,y),(375,y)]).intersection(wet);edge=waterline.bounds[2];ok=(xx>=edge+2.1);ii=np.where(ok)[0];xs.append(xx[ii[np.argmin(abs(hh[ii]-h))]])
 xs[0]=p[0];# final endpoint tangent dictated by V03 incoming direction
 ys=np.r_[ys,end[1]+5,end[1]];xs=np.r_[xs,end[0]+ed[0]/ed[1]*5,end[0]]
 # PCHIP interpolated plan, reparameterize by arclength. Force final exact cross-section normal.
 curve=PchipInterpolator(-ys,xs);yy=np.linspace(y0,end[1],3001);cc=np.c_[curve(-yy),yy];ss=np.r_[0,np.cumsum(np.linalg.norm(np.diff(cc,axis=0),axis=1))];s=np.linspace(0,ss[-1],int(np.ceil(ss[-1]/.25))+1);cy=np.interp(s,ss,yy);c=np.c_[curve(-cy),cy];d=np.c_[curve.derivative()(-cy),-np.ones(len(c))];d/=np.linalg.norm(d,axis=1)[:,None];d[-1]=ed;n=np.c_[-d[:,1],d[:,0]];n[-1]=en;off=np.linspace(-1,1,9);Q=c[:,None,:]+off[None,:,None]*n[:,None,:];H=z(Q.reshape(-1,2)).reshape(Q.shape[:2]);foot=Polygon(np.vstack([Q[:,0],Q[::-1,-1]]));
 if not foot.is_valid:attempts.append(dict(y0=y0,status='INVALID_PLAN'));continue
 # Ease slopes over first/last 3m, uniform height along longitudinal traces, exact endpoint profiles.
 w=np.minimum(np.minimum(s/3,(s[-1]-s)/3),1);w=np.clip(w,0,1);w=w*w*(3-2*w);inc=np.minimum(np.linalg.norm(np.diff(Q,axis=0),axis=2).min(1),np.diff(s))*(w[1:]+w[:-1])/2;u=np.r_[0,np.cumsum(inc)];u/=u[-1];base=h0+(endrow[4]-h0)*u;blend=np.clip((s-(s[-1]-3))/3,0,1);blend=blend*blend*(3-2*blend);Z=base[:,None]+blend[:,None]*(endrow-endrow[4]);Z[-1]=endrow;N,M=Z.shape;i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();f=np.stack([np.stack([i,i+M,i+M+1],1),np.stack([i,i+M+1,i+1],1)],1).reshape(-1,3);T=np.dstack([Q,Z]).reshape(-1,3)[f];nn=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);g=-nn[:,:2]/nn[:,2,None];dd=np.repeat(d[:-1],2*(M-1),axis=0);dn=np.c_[-dd[:,1],dd[:,0]];da=np.repeat(np.arccos(np.clip(np.sum(d[:-1]*d[1:],axis=1),-1,1)),2*(M-1));bound=2*np.linalg.norm(g,axis=1)*np.sin(da/2);delta=Z-H
 rec=dict(y0=y0,launch_xy=p.tolist(),length_m=float(s[-1]),rise_m=float(endrow[4]-h0),long_bound_pct=float(100*np.max(abs((g*dd).sum(1))+bound)),cross_bound_pct=float(100*np.max(abs((g*dn).sum(1))+bound)),max_cut_m=float(max(0,-delta.min())),max_fill_m=float(max(0,delta.max())),wet_overlap_m2=foot.intersection(wet).area,outside_m2=foot.difference(domain).area,entry_residual_m=float(np.max(abs(Z[-1]-endrow))),prior_trail_overlap_m2=foot.intersection(Polygon(np.vstack([B['road_xy'][:,0],B['road_xy'][::-1,-1]]))).area,triangles=len(f),samples=Z.size)
 rec['status']='PASS_PROPOSED_LATTICE' if rec['long_bound_pct']<=15 and rec['cross_bound_pct']<=10 and rec['wet_overlap_m2']<1e-8 and rec['outside_m2']<1e-8 and rec['prior_trail_overlap_m2']<1e-8 else 'REJECT';attempts.append(rec);print(rec,flush=True)
 if best is None or (rec['status']!='PASS_PROPOSED_LATTICE',max(rec['max_cut_m'],rec['max_fill_m']))<(best[0]['status']!='PASS_PROPOSED_LATTICE',max(best[0]['max_cut_m'],best[0]['max_fill_m'])):best=(rec,s,c,Q,H,Z)
assert best is not None;rec,s,c,Q,H,Z=best;assert [sha(x) for x in [P,V,A]]==expected
np.savez_compressed(O/'bank_route_v06.npz',station=s,xy=Q,source_z=H,design_z=Z);assert np.array_equal(np.load(O/'bank_route_v06.npz')['design_z'],Z)
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(15,6),layout='constrained')
for v,f in grids:ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=4,vmax=25,shading='gouraud')
for p in sh.get_parts(wet):ax.fill(*p.exterior.xy,c='#5887a5')
ax.plot(*c.T,c='#673d20',lw=2);ax.scatter(*c[[0,-1]].T,c='white',edgecolor='k');ax.set(xlim=(310,390),ylim=(-245,-140),aspect='equal',title='A | Contour-following bank path',xlabel='X (m)',ylabel='Y (m)');bx.plot(s,H[:,4],label='Existing');bx.plot(s,Z[:,4],label='Proposed');bx.set(title='B | Profile',xlabel='Station (m)',ylabel='Z (m)');bx.legend();bx.grid(alpha=.25);im=cx.pcolormesh(s,np.linspace(-1,1,9),(Z-H).T,cmap='RdBu',shading='auto');fig.colorbar(im,ax=cx,label='Height correction (m)');cx.set(title='C | Road-width correction',xlabel='Station (m)',ylabel='Offset (m)');fig.suptitle('MOSS FOREST V06 | BANK PATH FEASIBILITY — NOT NATIVE');fig.savefig(O/'bank_route_v06.png',dpi=150);plt.close(fig)
q=dict(status=rec['status'],inputs_sha256=expected,attempts=attempts,selected=rec,source_unchanged=True,limits=['Proposed triangle grade bounds only; no native edits. Starting site is an uphill dry point, not a proven water landing. Initial flat cross section would require staging pad and shoulder tie-in. River water flow, shore contact, protected water surface, canopy and runtime not verified.','No independent D4. Provisional design, not canon or adoption.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'bank_route_v06.npz',O/'bank_route_v06.png']});(O/'bank_route_v06.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
