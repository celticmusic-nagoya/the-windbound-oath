"""Design-only natural landing shelf comparison, SHA-pinned reconstructed terrain. No mesh edit."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import LineString,Polygon
from shapely.ops import unary_union
from scipy.spatial.distance import cdist
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent; P,A=map(Path,sys.argv[1:3]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653'];assert [sha(P),sha(A)]==expected
S=trimesh.load(P,force='scene',process=False);R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def mesh(name):
 t,g=S.graph[name];m=S.geometry[g];return trimesh.transform_points(m.vertices,t)@R,m.faces
v,f=mesh('RIVER_CORRIDOR');t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=-n[:,:2]/n[:,2,None];tri=sh.polygons(t[:,:,:2]);planes=np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)];tree=sh.STRtree(tri);domain=unary_union(tri);wv,wf=mesh('RIVER_WATER_CLIPPED');wet=unary_union(sh.polygons(wv[wf][:,:,:2]));B=np.load(A);goal=B['road_xy'][0,4];goalz=B['road_z'][0,4]
def z(x):
 x=np.asarray(x);a,b=tree.query(sh.points(x),predicate='intersects');out=np.full(len(x),np.nan);out[a]=(planes[b,:2]*x[a]).sum(1)+planes[b,2];assert np.isfinite(out).all();return out
# Exact water polygon vertices along east boundary are included in y rows (piecewise-linear edge).
# Sample 18 stations and 3 envelope grades. Landing strip is 4m along y and 4m inland, shore-to-pad grade 8%.
# The outer taper does not claim a general <=50% bank: existing natural slopes are intentionally retained.
def shore(y):
 s=LineString([(225,float(y)),(375,float(y))]).intersection(wet);assert not s.is_empty;return s.bounds[2]
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
records=[];best=None;step=.25
for y0 in np.arange(-240,-154.99,5.):
 for blend in [.65,.8,.95]:
  yy=np.unique(np.r_[np.arange(y0-9,y0+9.001,step),wv[:,1][(wv[:,1]>y0-9)&(wv[:,1]<y0+9)]])
  # prevent near-duplicate rows from imported float coordinates
  yy=np.array([yy[0]]+[x for i,x in enumerate(yy[1:],1) if x-yy[i-1]>1e-6]);d=np.arange(0,23.001,step);edge=np.array([shore(y) for y in yy]);Q=np.stack(np.broadcast_arrays(edge[:,None]+d[None,:],yy[:,None]),axis=-1);H=z(Q.reshape(-1,2)).reshape(Q.shape[:2]);water=4+.012*(yy+250);target=water[:,None]+.08*d[None,:];corev=(abs(yy-y0)<=2+1e-9)[:,None]&(d<=4+1e-9)[None,:];T0=np.broadcast_to(target,H.shape).copy();T0[:,0]=H[:,0];fixed=Q[corev];fixed_z=T0[corev];upper=np.empty(H.size);flat=Q.reshape(-1,2)
  for k0 in range(0,len(flat),512):upper[k0:k0+512]=np.min(fixed_z[None,:]+blend*cdist(flat[k0:k0+512],fixed),axis=1)
  Z=np.minimum(H,upper.reshape(H.shape));Z[corev]=T0[corev];Z[:,0]=H[:,0];delta=Z-H
  N,M=Z.shape;i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();ff=np.stack([np.stack([i,i+1,i+M+1],1),np.stack([i,i+M+1,i+M],1)],1).reshape(-1,3);V=np.dstack([Q,Z]).reshape(-1,3);T=V[ff];nn=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);assert (nn[:,2]>0).all();grad=-nn[:,:2]/nn[:,2,None];sl=np.linalg.norm(grad,axis=1);G=V[ff].mean(1);# classify via lattice cells, not approximate centers
  core=np.repeat(((abs(yy[:-1]-y0)<=2+1e-8)&(abs(yy[1:]-y0)<=2+1e-8))[:,None]&((d[1:]<=4+1e-8)[None,:]),2,axis=1).ravel();assert core.any();baseT=np.dstack([Q,H]).reshape(-1,3)[ff];baseN=np.cross(baseT[:,1]-baseT[:,0],baseT[:,2]-baseT[:,0]);baseSl=np.linalg.norm(baseN[:,:2]/baseN[:,2,None],axis=1)
  foot=Polygon(np.vstack([Q[:,0],Q[::-1,-1]]));assert foot.is_valid;wet_overlap=foot.intersection(wet).area;outside=foot.difference(domain).area;cut_vol=float(np.sum(nn[:,2]/2*(-delta.ravel()[ff]).mean(1)));pos=np.array([shore(y0)+4,y0]);pz=float(4+.012*(y0+250)+.32);rise=float(goalz-pz);minimum=rise/.15;straight=float(np.linalg.norm(goal-pos));core_max=float(100*sl[core].max());max_bank=float(100*sl[~core].max());base_bank=float(100*baseSl[~core].max());rec=dict(y_m=float(y0),envelope_slope=blend,core_grade_pct=core_max,outer_max_grade_pct=max_bank,outer_source_grade_pct=base_bank,cut_max_m=float(-delta.min()),cut_volume_m3=cut_vol,footprint_m2=foot.area,wet_overlap_m2=wet_overlap,outside_m2=outside,shore_residual_m=float(abs(delta[:,0]).max()),outer_residual_m=float(max(abs(delta[[0,-1]]).max(),abs(delta[:,-1]).max())),min_signed_double_area_m2=float(nn[:,2].min()),triangles=len(ff),core_triangles=int(core.sum()),shelf_exit_xy=pos.tolist(),shelf_exit_z_m=pz,trail_entry_rise_m=rise,minimum_path_at_15pct_m=minimum,straight_distance_m=straight,shortest_straight_grade_pct=100*rise/straight)
  rec['local_pass']=bool(core_max<=15 and wet_overlap<1e-5 and outside<1e-6 and rec['shore_residual_m']<1e-8 and rec['outer_residual_m']<1e-8 and max_bank<=max(100,base_bank+10));records.append(rec)
  if best is None or (not rec['local_pass'],rec['outer_residual_m']>1e-8,rec['outer_max_grade_pct'] if not rec['local_pass'] else rec['cut_volume_m3'],rec['cut_max_m'])<(not best[0]['local_pass'],best[0]['outer_residual_m']>1e-8,best[0]['outer_max_grade_pct'] if not best[0]['local_pass'] else best[0]['cut_volume_m3'],best[0]['cut_max_m']):best=(rec,Q,H,Z,yy,d,core,sl,foot)
print('range', {k:(min(r[k] for r in records),max(r[k] for r in records)) for k in ['core_grade_pct','outer_max_grade_pct','outer_source_grade_pct','wet_overlap_m2','shore_residual_m','outer_residual_m','outside_m2','cut_volume_m3']},flush=True); print('best grade',min(records,key=lambda r:r['core_grade_pct']),flush=True)
assert best is not None, 'No local candidate meets provisional criteria'
rec,Q,H,Z,yy,d,core,sl,foot=best;assert [sha(P),sha(A)]==expected
np.savez_compressed(O/'landing_design_v11.npz',xy=Q,source_z=H,design_z=Z,y=yy,east_offset=d);assert np.array_equal(np.load(O/'landing_design_v11.npz')['design_z'],Z)
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(14,5.5),layout='constrained');ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=4,vmax=25,shading='gouraud');
for p in sh.get_parts(wet):ax.fill(*p.exterior.xy,c='#5c8ca7')
for rr in records:
 if rr['envelope_slope']==.65:ax.scatter(*rr['shelf_exit_xy'],s=14,c='#f1d29b',edgecolor='k',lw=.25)
ax.fill(*foot.exterior.xy,c='#c78a45',alpha=.9,label='Rejected shelf diagnostic');ax.scatter(*goal,c='white',edgecolor='k',label='V03 trail start');ax.set(xlim=(310,387),ylim=(-250,-145),aspect='equal',title='A | Alternative landing sites',xlabel='East X (m)',ylabel='North Y (m)');ax.legend(fontsize=7)
k=np.argmin(abs(yy-rec['y_m']));bx.plot(d,H[k],'--',label='Existing terrain');bx.plot(d,Z[k],label='Proposed');bx.axvspan(0,4,color='#d3b778',alpha=.3,label='Landing strip');bx.set(title='B | Shore-to-bank section',xlabel='East of water edge (m)',ylabel='Z (m)');bx.grid(alpha=.2);bx.legend(fontsize=8)
passr=[r for r in records if r['local_pass']];cx.scatter([r['cut_volume_m3'] for r in records],[r['outer_max_grade_pct'] for r in records],s=14,c='#9d6050',label='All tested');cx.scatter([r['cut_volume_m3'] for r in passr],[r['outer_max_grade_pct'] for r in passr],s=16,c='#557c58',label='Local pass');cx.scatter(rec['cut_volume_m3'],rec['outer_max_grade_pct'],s=65,c='#f4d17d',edgecolor='k',label='Best rejected');cx.set(title='C | Cut vs outer bank slope',xlabel='Proposed cut volume (m³)',ylabel='Maximum outer grade (%)');cx.legend(fontsize=7);cx.grid(alpha=.2);fig.suptitle('MOSS FOREST V11 | NATURAL LANDING SHELF — LOCAL DESIGN ONLY');fig.savefig(O/'landing_v11.png',dpi=150);plt.close(fig)
q=dict(status='LOCAL_SHELF_CANDIDATE_CONTINUOUS_ROUTE_HOLD' if rec['local_pass'] else 'NO_LOCAL_PASS',inputs_sha256=expected,criteria={'core_grade_limit_pct':15,'outer_grade_limit':'max(100%, measured outer source maximum +10 percentage points); natural bank only, not walkable slope','core_width_along_river_m':4,'core_depth_east_m':4,'envelope_slope_options':[.65,.8,.95], 'region_half_length_m':9,'region_depth_m':23,'source_water_protected':True,'tolerances':'wet overlap <1e-5m²; outside <1e-6m²; boundary sample residual <1e-8m'},attempts=records,selected=rec,local_pass_count=len(passr),input_unchanged=True,limitations=['New local design shelf only, not a proven continuous route. Lower bound to existing trail is rise/0.15, not a path. Wet footprint measured from recovered authored GLB, no hydrology or actual terrain.','Outside the shelf, natural bank may remain steep (not walking area). Only proposed triangles and sampled seams tested, no continuous conforming terrain, physics, collision or water-flow QA. No local pass: least outer grade among tested rejected candidates satisfying sampled outer boundary; diagnostic only, not art approval.','No official CG comparison, independent D4 or native mesh. No canon adoption.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'landing_design_v11.npz',O/'landing_v11.png']});(O/'landing_v11.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k!='attempts'},indent=2))
