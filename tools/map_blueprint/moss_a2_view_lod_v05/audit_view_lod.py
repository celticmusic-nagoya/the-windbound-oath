"""Design-stage A2 camera and tree LOD sensitivity; no runtime or native edits."""
import sys,csv,json,hashlib
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import LineString
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;P,V,T,C=map(Path,sys.argv[1:5]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc','4540ea97d6375515957883be200085025b2546f21b27eaf73454460547af4a54','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','4dd0ce597c90339e38c7589e2ab42ed9837924e6d38226c42065a89766871394'];assert [sha(p) for p in (P,V,T,C)]==expected
m=trimesh.load(P,force='mesh',process=False);v=m.vertices@np.array([[1.,0,0],[0,0,1],[0,-1,0]])+[500,-300,0];f=m.faces
A=np.load(V);B=np.load(T);rows=list(csv.DictReader(C.open()));xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in rows]);z=np.array([float(r['z_m']) for r in rows]);rad=np.array([float(r['radius_m']) for r in rows]);height=np.array([float(r['height_m']) for r in rows]);kind=np.array([r['kind'] for r in rows]);ids=np.array([r['id'] for r in rows]);assert len(rows)==451
# Ground surface query: original first, candidate channel/road/shoulder panels override inside their sampled triangle footprints.
def grid_tri(q,h):
 n,k=h.shape;i=(np.arange(n-1)[:,None]*k+np.arange(k-1)).ravel();ff=np.stack([np.stack([i,i+k,i+k+1],1),np.stack([i,i+k+1,i+1],1)],1).reshape(-1,3);return np.dstack([q,h]).reshape(-1,3)[ff]
def layer(t):
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert np.min(abs(n[:,2]))>1e-10;g=-n[:,:2]/n[:,2,None];return sh.STRtree(sh.polygons(t[:,:,:2])),np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)]
layers=[layer(v[f]),layer(np.dstack([A['xy'],A['design_z']]).reshape(-1,3)[A['faces']])]+[layer(grid_tri(B[k+'_xy'],B[k+'_design_z' if k!='road' else 'road_z'])) for k in ['left','right','road']]
def ground(q):
 out=np.full(len(q),np.nan);pts=sh.points(q)
 for tree,plane in layers:
  a,b=tree.query(pts,predicate='intersects');out[a]=(plane[b,:2]*q[a]).sum(1)+plane[b,2]
 return out
rxy=B['road_xy'][:,4];rz=B['road_z'][:,4];ii=np.flatnonzero((rxy[:,0]>=400)&(rxy[:,0]<=600)&(rxy[:,1]>=-400)&(rxy[:,1]<=-300));stations=B['station'][ii];cam=np.c_[rxy[ii],rz[ii]]
# Four waterfall slope points just above candidate water (not opaque modeled waterfall) and three hero reservation targets.
fi=np.array([47,49,51]);targets=np.c_[A['xy'][fi,20],A['water_stage_z'][fi]+.15];names=['fall_upper','fall_mid','fall_lower'];hero=np.flatnonzero(kind=='ancient_tree_reserve');targets=np.vstack([targets,np.c_[xy[hero],z[hero]+height[hero]*.65]]);names+=ids[hero].tolist();target_owner=[-1]*3+hero.tolist()
# For sightline, analytic intersection of full vertical reservation cylinders; conservative, not real crown silhouettes.
def blockers(p,q,exclude):
 d=q-p;dxy=d[:2];a=dxy@dxy;rel=p[:2]-xy;b=2*(rel@dxy);c=(rel*rel).sum(1)-rad*rad;disc=b*b-4*a*c;root=np.sqrt(np.maximum(disc,0));lo=np.maximum((-b-root)/(2*a),0);hi=np.minimum((-b+root)/(2*a),1);dz=d[2]
 if abs(dz)>1e-9:
  z0=(z-p[2])/dz;z1=(z+height-p[2])/dz;lo=np.maximum(lo,np.minimum(z0,z1));hi=np.minimum(hi,np.maximum(z0,z1))
 else:hi=np.where((p[2]>=z)&(p[2]<=z+height),hi,-1)
 hit=(disc>=0)&(lo<=hi)&(hi>1e-6)&(lo<1-1e-6)
 if exclude>=0:hit[exclude]=False
 return ids[hit].tolist()
# Approximately 5m camera spacing; additionally exact nearest V04 reserved observation point.
idx=np.unique(np.r_[np.arange(0,len(cam),20),len(cam)-1,np.argmin(np.linalg.norm(cam[:,:2]-[500.8589869572925,-342.5341254243298],axis=1))]);reserved=int(np.argmin(np.linalg.norm(cam[:,:2]-[500.8589869572925,-342.5341254243298],axis=1)));records=[]
for i in idx:
 for eye in [1.65,3.5]:
  p=cam[i]+[0,0,eye]
  for name,q,own in zip(names,targets,target_owner):
   ds=np.linalg.norm(q[:2]-p[:2]);u=np.linspace(0,1,max(2,int(np.ceil(ds/.25))+1));ray=p+(q-p)*u[:,None];gr=ground(ray[:,:2]);assert np.isfinite(gr).all();clear=ray[:,2]-gr;hits=blockers(p,q,own);gmin=float(clear.min());records.append(dict(station_m=float(stations[i]),camera_index=int(i),eye_m=eye,target=name,ground_min_clearance_m=gmin,ground_blocked=gmin<.05,envelope_blockers=hits,clear_screen=gmin>=.05 and not hits))
# Radial all-direction tree workload; no frustum/occlusion credits. Distance to XY envelope boundary.
trees=np.flatnonzero(np.isin(kind,['deciduous','forest_tall','ancient_tree_reserve']));counts=np.array([int(rows[i]['lod0_triangles']) if rows[i]['lod0_triangles'] else 20000 for i in trees]);distance=np.maximum(np.linalg.norm(cam[:,None,:2]-xy[trees][None,:,:],axis=2)-rad[trees],0)
profiles=[('A_detail',[18,40,75,120],[1,.35,.10]),('B_balanced',[12,30,60,100],[1,.25,.06]),('C_mobile',[8,22,48,90],[1,.18,.04])];lod=[];allcurves=[]
for name,dist,factors in profiles:
 tier=np.digitize(distance,dist);table=np.vstack([np.ceil(counts*x).astype(int) for x in factors]+[np.full(len(trees),12),np.zeros(len(trees),dtype=int)]);cost=table[tier,np.arange(len(trees))].sum(1);k=int(cost.argmax());allcurves.append(cost);lod.append(dict(profile=name,thresholds_m=dist,fractions=factors,impostor_triangles=12,peak_tree_triangles=int(cost[k]),p95_tree_triangles=float(np.percentile(cost,95)),mean_tree_triangles=float(cost.mean()),peak_station_m=float(stations[k]),peak_counts_by_tier=np.bincount(tier[k],minlength=5).tolist(),screen_under_150k=bool(cost.max()<=150000)))
summary=[]
for eye in [1.65,3.5]:
 for name in names:
  rr=[r for r in records if r['eye_m']==eye and r['target']==name];summary.append(dict(eye_m=eye,target=name,views=len(rr),clear=sum(r['clear_screen'] for r in rr),terrain_blocked=sum(r['ground_blocked'] for r in rr),envelope_blocked=sum(bool(r['envelope_blockers']) for r in rr)))
assert [sha(p) for p in (P,V,T,C)]==expected
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(16,6),layout='constrained');ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud',alpha=.65);ax.plot(*cam[:,:2].T,c='#745330',lw=2);ax.scatter(*xy[trees].T,s=rad[trees]**2,c='#315b3c',alpha=.6);ax.scatter(*targets[:3,:2].T,c='#176d9a',s=25);ax.scatter(*targets[3:,:2].T,c='#b98b2f',s=55,marker='*');ax.scatter(*cam[reserved,:2],c='white',edgecolors='black',s=60);rr=[r for r in records if r['eye_m']==1.65 and r['target']=='fall_mid'];ax.scatter(*cam[[r['camera_index'] for r in rr],:2].T,c=['#338556' if r['clear_screen'] else '#b8493a' for r in rr],s=16);ax.set(aspect='equal',xlim=(400,600),ylim=(-400,-300),title='A | A2 view samples (1.65m eye)',xlabel='East X (m)',ylabel='North Y (m)')
for k,eye in enumerate([1.65,3.5]):
 values=[next(s['clear'] for s in summary if s['eye_m']==eye and s['target']==name) for name in names];bx.barh(np.arange(len(names))+(k-.5)*.36,values,height=.34,label=f'{eye}m eye')
bx.set(yticks=np.arange(len(names)),yticklabels=names,xlabel=f'Clear samples (of {len(idx)})',title='B | Terrain + full cylinder screen',xlim=(0,len(idx)));bx.legend();bx.invert_yaxis()
for p,y in zip(lod,allcurves):cx.plot(stations,y/1000,label=p['profile']);cx.axhline(150,c='#a34e42',ls='--',lw=.8);cx.set(title='C | Radial tree workload only',xlabel='Trail station (m)',ylabel='Estimated triangles (thousands)');cx.legend();cx.grid(alpha=.25)
fig.suptitle('MOSS A2 V05 | CAMERA & LOD DESIGN SCREEN — NOT RUNTIME');fig.savefig(O/'a2_view_lod_v05.png',dpi=150);plt.close(fig)
with (O/'view_samples.csv').open('w',newline='') as o:
 w=csv.DictWriter(o,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
report=dict(status='DESIGN_SCREEN_ONLY',inputs_sha256=expected,source_unchanged=True,road_samples=len(cam),camera_positions=len(idx),ray_count=len(records),ray_step_max_m=.25,ground_clearance_threshold_m=.05,targets=dict(zip(names,targets.tolist())),summary=summary,reserved_observation=[r for r in records if r['camera_index']==reserved],lod=lod,lod0_all_known_trees=int(counts.sum()-60000),hero_assumed_lod0=20000,all_tree_lod0_including_hero_assumption=int(counts.sum()),provisional_tree_budget=150000,limitations=['Ground sampling only, not continuous exact ray intersection. Full opaque cylinders deliberately conservative; unknown canopy/trunk origin and shape. Eye heights and waterfall target heights provisional. No camera frustum or player movement check.','LOD triangle targets are design allocations only, no generated LOD meshes or Android test; hero 20k assumed, impostor 12 triangles assumed; excludes rocks, understory, terrain, water, shadows, texture/overdraw and draw calls. No visual quality or final D4.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'view_samples.csv',O/'a2_view_lod_v05.png']});(O/'qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['road_samples','camera_positions','ray_count','summary','reserved_observation','lod','outputs']},indent=2))
