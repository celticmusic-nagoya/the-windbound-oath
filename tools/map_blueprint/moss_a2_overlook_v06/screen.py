import sys,csv,json,hashlib
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import Point,Polygon,LineString
from shapely.ops import unary_union
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;P,V,T,C=map(Path,sys.argv[1:5]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc','4540ea97d6375515957883be200085025b2546f21b27eaf73454460547af4a54','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','4dd0ce597c90339e38c7589e2ab42ed9837924e6d38226c42065a89766871394'];assert [sha(p) for p in (P,V,T,C)]==expected
m=trimesh.load(P,force='mesh',process=False);v=m.vertices@np.array([[1.,0,0],[0,0,1],[0,-1,0]])+[500,-300,0];f=m.faces;t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);g=-n[:,:2]/n[:,2,None];poly=sh.polygons(t[:,:,:2]);tree=sh.STRtree(poly);domain=unary_union(poly);A=np.load(V);B=np.load(T);rows=list(csv.DictReader(C.open()));xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in rows]);z=np.array([float(r['z_m']) for r in rows]);rad=np.array([float(r['radius_m']) for r in rows]);height=np.array([float(r['height_m']) for r in rows]);ids=np.array([r['id'] for r in rows]);kind=np.array([r['kind'] for r in rows]);
def grid_tri(q,h):
 n,k=h.shape;i=(np.arange(n-1)[:,None]*k+np.arange(k-1)).ravel();ff=np.stack([np.stack([i,i+k,i+k+1],1),np.stack([i,i+k+1,i+1],1)],1).reshape(-1,3);return np.dstack([q,h]).reshape(-1,3)[ff]
def layer(t):
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert np.min(abs(n[:,2]))>1e-10;g=-n[:,:2]/n[:,2,None];return sh.STRtree(sh.polygons(t[:,:,:2])),np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)]
layers=[layer(t),layer(np.dstack([A['xy'],A['design_z']]).reshape(-1,3)[A['faces']])]+[layer(grid_tri(B[k+'_xy'],B[k+'_design_z' if k!='road' else 'road_z'])) for k in ['left','right','road']]
def ground(q):
 out=np.full(len(q),np.nan);pts=sh.points(q)
 for tr,pl in layers:
  a,b=tr.query(pts,predicate='intersects');out[a]=(pl[b,:2]*q[a]).sum(1)+pl[b,2]
 return out
# V04 exclusion reconstructed exactly, no hydrology assumptions beyond conservative low-ground reserve.
q=A['xy'];foot=Polygon(np.vstack([q[:,0],q[::-1,-1]]));road=unary_union([Polygon(np.vstack([B[k][:,0],B[k][::-1,-1]])) for k in ['road_xy','left_xy','right_xy']]);stage=float(A['water_stage_z'][-1]+.5);parts=[]
for tri in t:
 p=[]
 for a,c in zip(tri,np.roll(tri,-1,axis=0)):
  if a[2]<=stage:p.append(a[:2])
  if (a[2]<stage<c[2]) or (c[2]<stage<a[2]):p.append((a+(c-a)*(stage-a[2])/(c[2]-a[2]))[:2])
 if len(p)>=3 and Polygon(p).area>1e-10:parts.append(Polygon(p))
wet=unary_union(parts);water_reserve=unary_union([foot.buffer(2),wet.buffer(2)]);reserved=water_reserve.union(road.buffer(1));fi=np.array([47,49,51]);targets=np.c_[A['xy'][fi,20],A['water_stage_z'][fi]+.15]
def blockers(p,q,exclude=-1):
 d=q-p;dxy=d[:2];a=dxy@dxy;rel=p[:2]-xy;b=2*(rel@dxy);c=(rel*rel).sum(1)-rad*rad;disc=b*b-4*a*c;root=np.sqrt(np.maximum(disc,0));lo=np.maximum((-b-root)/(2*a),0);hi=np.minimum((-b+root)/(2*a),1);dz=d[2]
 if abs(dz)>1e-9:
  z0=(z-p[2])/dz;z1=(z+height-p[2])/dz;lo=np.maximum(lo,np.minimum(z0,z1));hi=np.minimum(hi,np.maximum(z0,z1))
 else:hi=np.where((p[2]>=z)&(p[2]<=z+height),hi,-1)
 hit=(disc>=0)&(lo<=hi)&(hi>1e-6)&(lo<1-1e-6)
 if exclude>=0:hit[exclude]=False
 return np.flatnonzero(hit)
def sight(p,q):
 u=np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(q[:2]-p[:2])/.25))+1));ray=p+(q-p)*u[:,None];gr=ground(ray[:,:2]);return float(np.min(ray[:,2]-gr)),blockers(p,q)
# 2m radius viewing pad, 10% isotropic ground slope, 65m maximum target range. All three target samples must clear terrain.
records=[];fall=targets[1,:2]
for x in np.arange(402.5,600,2.5):
 for y in np.arange(-397.5,-300,2.5):
  p=Point(x,y);disk=p.buffer(2,quad_segs=32)
  if p.distance(Point(fall))>65 or not domain.covers(disk) or p.distance(reserved)<2+1e-6:continue
  ix=tree.query(disk,predicate='intersects');grade=float(np.linalg.norm(g[ix],axis=1).max())
  if grade>.10:continue
  pos=np.r_[x,y,ground(np.array([[x,y]]))[0]+1.65];s=[sight(pos,a) for a in targets];clear=[a[0]>=.05 for a in s];hit=set(np.flatnonzero(np.linalg.norm(xy-[x,y],axis=1)<rad+2));hit.update(i for a in s for i in a[1]);records.append(dict(x=x,y=y,z=pos[2]-1.65,grade_pct=100*grade,terrain_clear=int(sum(clear)),min_clearance_m=float(min(a[0] for a in s)),conflicts=sorted(hit)))
print('view records',len(records),'terrain all',sum(r['terrain_clear']==3 for r in records),'zero blockers',sum(r['terrain_clear']==3 and not r['conflicts'] for r in records),flush=True)
print(sorted([r for r in records if r['terrain_clear']==3],key=lambda r:(len(r['conflicts']),np.linalg.norm(np.array([r['x'],r['y']])-fall)))[:10],flush=True)
# 2m-wide rounded footprints, exact gradient of every source/design triangle intersected (conservative where layers overlap).
# Existing route intersection permitted for entry edges only; geometry unchanged.
coords=[];keys={}
for x in np.arange(402.5,600,2.5):
 for y in np.arange(-397.5,-300,2.5):
  p=Point(x,y)
  if p.distance(water_reserve)<1.00001 or p.distance(road)<1.00001 or p.distance(domain.boundary)<1.00001:continue
  keys[(x,y)]=len(coords);coords.append([x,y])
N=len(coords);coords=np.array(coords);edge_list=[];weights=[];costs={};gchecks={}
def check(a,b,entry=False):
 d=b-a;l=np.linalg.norm(d);d/=l;nn=np.array([-d[1],d[0]]);line=LineString([a,b]);disk=line.buffer(1,quad_segs=16)
 if not domain.covers(disk) or disk.intersects(water_reserve) or (not entry and disk.intersects(road)):return None
 # Ignore layers spatially absent; conservative including underlying source triangles where overlay present.
 long=cross=0.
 for tr,pl in layers:
  ix=tr.query(disk,predicate='intersects');gg=pl[ix,:2]
  if len(gg):long=max(long,float(np.max(abs(gg@d))));cross=max(cross,float(np.max(abs(gg@nn))))
 if long>.15+1e-10 or cross>.10+1e-10:return None
 q=np.clip(((xy-a)@d)/l,0,1);dist=np.linalg.norm(xy-(a+q[:,None]*(b-a)),axis=1);hit=np.flatnonzero(dist<rad+1+1e-6)
 return (l,long,cross,hit)
def add(i,j,c):
 edge_list.extend([(i,j),(j,i)]);weights.extend([c[0]+2*len(c[3])]*2);costs[(i,j)]=costs[(j,i)]=c
for (x,y),i in keys.items():
 for dx,dy in [(2.5,0),(0,2.5),(2.5,2.5),(2.5,-2.5)]:
  j=keys.get((x+dx,y+dy))
  if j is not None:
   c=check(coords[i],coords[j]);
   if c is not None:add(i,j,c)
# Attach source node to every eligible sampled road entry. Entry uses original and design gradients, no source terrain edits.
rr=B['road_xy'][:,4];idx=np.flatnonzero((rr[:,0]>402)&(rr[:,0]<598)&(rr[:,1]>-398)&(rr[:,1]<-302))[::8];entries=rr[idx];allxy=np.vstack([coords,entries]);source=len(allxy);kdt=cKDTree(coords);entry_count=0
for k,p in enumerate(entries):
 i=N+k;good=0
 for j in kdt.query_ball_point(p,7.5):
  c=check(p,coords[j],True)
  if c is not None:add(i,j,c);good+=1
 if good:edge_list.append((source,i));weights.append(1e-6);entry_count+=1
ar=np.array(edge_list);mat=coo_matrix((weights,(ar[:,0],ar[:,1])),shape=(source+1,source+1)).tocsr();dist,pred=dijkstra(mat,indices=source,directed=True,return_predecessors=True);results=[]
for r in records:
 if r['terrain_clear']!=3:continue
 i=keys.get((r['x'],r['y']));
 if i is None or not np.isfinite(dist[i]):continue
 path=[i];k=i
 while pred[k]!=source:
  k=int(pred[k]);assert k>=0;path.append(k)
 path=path[::-1];cc=[costs[(i,j)] for i,j in zip(path,path[1:])];hit=set(r['conflicts']);hit.update(int(i) for c in cc for i in c[3]);length=sum(c[0] for c in cc);results.append(dict(view=r,route_xy=allxy[path].tolist(),length_m=float(length),long_pct=100*max(c[1] for c in cc),cross_pct=100*max(c[2] for c in cc),conflict_ids=ids[sorted(hit)].tolist(),conflict_kinds=kind[sorted(hit)].tolist(),entry_station_m=float(B['station'][idx[path[0]-N]]),weighted_cost=float(dist[i])))
print('nodes',N,'edges',len(edge_list),'entry',entry_count,'reached',len(results),flush=True)
results.sort(key=lambda a:(sum(k=='ancient_tree_reserve' for k in a['conflict_kinds']),len(a['conflict_ids']),a['length_m']));print(json.dumps(results[:3],default=lambda x:x.item(),indent=2),flush=True)
# Save only tested candidates, not changed placements. Show shortest conflict-minimized screened route and comparison.
# Keep least-disruption route as alternative; compare short-distance landmark composition separately.
far=results[0] if results else None
near=next((r for r in sorted(results,key=lambda a:(-a['view']['min_clearance_m'],len(a['conflict_ids']),a['length_m'])) if np.linalg.norm(np.array([r['view']['x'],r['view']['y']])-fall)<=20),None)
selected=near or far
for r in results:
 pos=np.r_[r['view']['x'],r['view']['y'],r['view']['z']+1.65];d=targets-pos;unit=d/np.linalg.norm(d,axis=1)[:,None];r['target_range_m']=float(np.linalg.norm(d[1]));r['angular_span_deg']=float(np.degrees(np.arccos(np.clip(unit[0]@unit[2],-1,1))))

fig,(ax,bx)=plt.subplots(1,2,figsize=(13,7),layout='constrained')
for a in [ax,bx]:
 a.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud',alpha=.6);a.plot(*rr.T,c='#795333',lw=2);a.plot(*foot.exterior.xy,c='#175d89',lw=1.5)
 for p in sh.get_parts(water_reserve.intersection(domain)):
  if p.geom_type=='Polygon':a.fill(*p.exterior.xy,c='#7ca8bd',alpha=.4)
 a.scatter(*np.array([[r['x'],r['y']] for r in records]).T,s=7,c='#909594',alpha=.8);good=[r for r in records if r['terrain_clear']==3];a.scatter(*np.array([[r['x'],r['y']] for r in good]).T,s=35,c='#229447',edgecolors='white',lw=.5,label='3 terrain-clear targets');a.scatter(*targets[:,:2].T,c='#00639b',marker='*',s=100);a.set(aspect='equal',xlabel='X (m)',ylabel='Y (m)')
 if selected:
  from matplotlib.patches import Circle
  route=np.array(selected['route_xy']);a.plot(*route.T,c='#a35321',lw=2.2,label='Screened spur');p=selected['view'];a.scatter(p['x'],p['y'],s=100,c='#fbd577',edgecolor='k',zorder=6);a.add_patch(Circle((p['x'],p['y']),2,fill=False,ec='#523b27',lw=1.5));a.plot([p['x'],fall[0]],[p['y'],fall[1]],c='#8b4727',ls='--');
  for i in range(len(xy)):
   if ids[i] in selected['conflict_ids']:a.add_patch(Circle(xy[i],rad[i],color='#b24436',alpha=.45));
ax.set(xlim=(400,600),ylim=(-400,-300),title='A | Full A2 dry-site screen');ax.legend(fontsize=8);bx.set(xlim=(405,525),ylim=(-398,-295),title='B | Near candidate spur and conflicts');fig.suptitle('MOSS A2 V06 | OVERLOOK SCREEN — NOT NATIVE OR ADOPTED');fig.savefig(O/'overlook_v06.png',dpi=150);plt.close(fig)
assert [sha(p) for p in (P,V,T,C)]==expected
report=dict(status='SCREEN_ONLY',input_sha256=expected,view_candidates=len(records),terrain_all_three=sum(r['terrain_clear']==3 for r in records),all_three_no_conflicts=sum(r['terrain_clear']==3 and not r['conflicts'] for r in records),graph_nodes=N,graph_directed_edges=len(edge_list),entry_points=entry_count,reachable_viewpoints=len(results),selected=selected,least_hero_disruption=far,all_terrain_clear_routes=results,limits=['2.5m discrete graph; route not final alignment, curves/turning and continuous seam heights not verified. Exact triangle gradient screen conservative using all overlapping layers, not continuous terrain conformity. Footprint uses polygonal round buffers. Sight samples at 0.25m, vertical cylinders conservative. Relocation conflicts only; no actual relocation, asset geometry, official camera, hydrology, D4 or native work. Candidate thresholds authored, not canon.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'overlook_v06.png']});(O/'qa.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item())+'\n')
