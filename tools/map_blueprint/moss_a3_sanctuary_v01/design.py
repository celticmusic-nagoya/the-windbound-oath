"""A3 sanctuary spatial reservations; no native changes. Provisional metres X east Y north Z up."""
import sys,hashlib,json
from pathlib import Path
import numpy as np, trimesh, shapely as sh
from shapely.geometry import Point,Polygon,LineString,box
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
O=Path(__file__).resolve().parent
paths=list(map(Path,sys.argv[1:4]));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','c3d6c314cc23f50012840a2b81414f46ea638ac6f7917f3ae557394e434d3f32'];assert list(map(sha,paths))==expected
s=trimesh.load(paths[0],force='scene',process=False);m=s.to_geometry();v=m.vertices@np.array([[1.,0,0],[0,0,1],[0,-1,0]])+[600,-400,0];f=m.faces
A=np.load(paths[1]);B=np.load(paths[2]);r=A['road_xy'][:,4];st=A['station'];rz=A['road_z'][:,4];fullxy=np.concatenate([A['left_xy'][:,::-1],A['road_xy'][:,1:],A['right_xy'][:,1:]],axis=1);fullz=np.concatenate([A['left_design_z'][:,::-1],A['road_z'][:,1:],A['right_design_z'][:,1:]],axis=1)
def tri(x,z):
 v=np.dstack([x,z]).reshape(-1,3);n,m=z.shape;i=(np.arange(n-1)[:,None]*m+np.arange(m-1)).ravel();return v[np.stack([np.stack([i,i+m,i+m+1],1),np.stack([i,i+m+1,i+1],1)],1).reshape(-1,3)]
T=[v[f],tri(fullxy,fullz),tri(B['xy'],B['design_z'])];P=[sh.polygons(t[:,:,:2]) for t in T];tree=[sh.STRtree(p) for p in P];G=[];planes=[]
for t in T:
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);g=-n[:,:2]/n[:,2,None];G.append(g);planes.append(np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)])
domain=box(500,-500,700,-400);road=Polygon(np.r_[fullxy[:,0],fullxy[::-1,-1]]);pad=Polygon(np.r_[B['xy'][:,0],B['xy'][::-1,-1]]);end=B['xy'][-1,10];padcenter=B['xy'][20,10];d=(r[-1]-r[-2]);d/=np.linalg.norm(d);n=np.array([-d[1],d[0]])
def height(xy):
 xy=np.atleast_2d(xy);o=np.full(len(xy),np.nan)
 for tr,pl in zip(tree,planes):
  a,b=tr.query(sh.points(xy),predicate='intersects');o[a]=(pl[b,:2]*xy[a]).sum(1)+pl[b,2]
 assert np.isfinite(o).all();return o
def metric(p):
 # Exact intersection polygons with priority for design overlays. Conservative whole triangle slopes for all intersected visible parts.
 low=[];high=[];gr=[];area=[]
 for k in range(3):
  q=p if k==2 else p.difference(pad) if k==1 else p.difference(road.union(pad))
  if q.is_empty:continue
  ii=tree[k].query(q,predicate='intersects');cut=sh.intersection(P[k][ii],q);mask=sh.area(cut)>1e-10;ii=ii[mask];cut=cut[mask]
  if not len(ii):continue
  coords,idx=sh.get_coordinates(cut,return_index=True);z=(planes[k][ii[idx],:2]*coords).sum(1)+planes[k][ii[idx],2];low.append(z.min());high.append(z.max());gr.append(np.linalg.norm(G[k][ii],axis=1).max());area.append(float(sh.area(cut).sum()))
 return dict(grade_pct=float(max(gr)*100),z_range_m=[float(min(low)),float(max(high))],relief_m=float(max(high)-min(low)),covered_area_m2=sum(area),outside_m2=p.difference(domain).area)
# Arena: circular unobstructed reserve centred on route, compare radii 6/8/10m and stations 365–390. No grading.
arenas=[]
for ss in range(365,392,2):
 k=int(np.argmin(abs(st-ss)));c=r[k]
 for rad in [6,8,10]:
  p=Point(c).buffer(rad,quad_segs=64);q=metric(p);q.update(station_m=float(st[k]),center_xy=c.tolist(),radius_m=rad,area_m2=p.area,pad_clearance_m=p.distance(pad));q['pass_screen']=q['grade_pct']<=15 and q['relief_m']<=2 and q['outside_m2']<1e-8 and q['pad_clearance_m']>=5;arenas.append(q)
valid=[q for q in arenas if q['pass_screen']];assert valid
# Prefer largest area; then lowest relief. Barrier upstream >=12m from combat boundary.
sel=min(valid,key=lambda q:(-q['radius_m'],q['relief_m']));arena=Point(sel['center_xy']).buffer(sel['radius_m'],quad_segs=64)
barriers=[]
for ss in np.arange(330,sel['station_m']-sel['radius_m']-12,2):
 k=int(np.argmin(abs(st-ss)));p=Polygon([r[k]+a*d+b*n for a,b in [(-1,-2.5),(1,-2.5),(1,2.5),(-1,2.5)]]);q=metric(p);q.update(station_m=float(st[k]),center_xy=r[k].tolist(),arena_clearance_m=p.distance(arena));barriers.append(q)
bar=min(barriers,key=lambda q:q['grade_pct']);bp=box(-1,-1,1,1) # replace with oriented reserve
bc=np.array(bar['center_xy']);bp=Polygon([bc+a*d+b*n for a,b in [(-1,-2.5),(1,-2.5),(1,2.5),(-1,2.5)]])
# Hero tree reserve (not actual geometry), after gate and before arena, offset 8–16m, 5m radius.
trees=[]
for ss in np.arange(bar['station_m']+8,sel['station_m']-sel['radius_m']-3,2):
 k=int(np.argmin(abs(st-ss)))
 for side in [-1,1]:
  for off in [8,10,12,14,16]:
   c=r[k]+side*off*n;p=Point(c).buffer(5,quad_segs=64)
   if p.difference(domain).area>1e-8 or min(p.distance(road),p.distance(arena),p.distance(bp),p.distance(pad))<1:continue
   q=metric(p);q.update(station_m=float(st[k]),center_xy=c.tolist(),radius_m=5,root_clearance_m=p.distance(road),arena_clearance_m=p.distance(arena),offset_m=side*off,ground_z_m=float(height(c)[0]));q['pass_screen']=q['grade_pct']<=25 and q['relief_m']<=2.5;trees.append(q)
assert trees;tv=[x for x in trees if x['pass_screen']];assert tv
hero=min(tv,key=lambda q:(q['relief_m'],abs(q['offset_m'])));hc=np.array(hero['center_xy']);hp=Point(hc).buffer(5,quad_segs=64)
# Route samples into existing pad, source versus design. Verify protected files.
q=dict(status='PROVISIONAL_SPATIAL_RESERVES_ONLY',inputs_sha256=expected,criteria={'arena':'6/8/10m radius; grade<=15%, relief<=2m, >=5m from pad; provisional battle-space reservation only','barrier':'2m longitudinal x5m full shoulder width reserve; before arena, no event geometry','hero':'5m radius reserve; grade<=25%, relief<=2.5m, >=1m clearance from other reservations; unverified tree dimensions'},arena_candidates=arenas,arena_pass_count=len(valid),selected_arena=sel,barrier_candidates=barriers,selected_barrier=bar,tree_candidates=trees,tree_pass_count=len(tv),selected_hero=hero,pad={'center_xy':padcenter.tolist(),'flat_area_m2':24,'flat_z_m':float(B['design_z'][-1,10]),'footprint_m2':pad.area,'outside_m2':pad.difference(domain).area},protected_overlap_m2={'hero_road':hp.intersection(road).area,'hero_arena':hp.intersection(arena).area,'arena_pad':arena.intersection(pad).area,'barrier_arena':bp.intersection(arena).area},limits=['Reconstructed schematic GLB, not official CG or survey. Selected arena is unobstructed reservation only, not battle implementation or exact combat requirements. Road and gate deliberately intersect; battle reserve includes road; no native geometry, no independent D4. Polygonal circle approximation; thresholds and distances are provisional. Canon event order preserved, no new story actions.'],inputs_unchanged=list(map(sha,paths))==expected)
fig,(ax,bx)=plt.subplots(1,2,figsize=(12,6),layout='constrained',gridspec_kw={'width_ratios':[1.25,1]});im=ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud');fig.colorbar(im,ax=ax,label='Source Z (m)',shrink=.72);ax.plot(*r[st>=260].T,c='#e8ddbb',lw=2,label='Existing trail');
for poly,color,label in [(arena,'#b7603b','Combat reserve'),(hp,'#325b37','Ancient tree reserve'),(bp,'#7e59b5','Barrier reserve'),(pad,'#e7c278','V04 altar approach')]:
 ax.fill(*poly.exterior.xy,color=color,alpha=.75,label=label);ax.plot(*poly.exterior.xy,color=color,lw=1.2)
ax.set(xlim=(610,701),ylim=(-501,-425),aspect='equal',title='A | Sanctuary composition — reservations',xlabel='X east (m)',ylabel='Y north (m)');ax.legend(fontsize=8,loc='upper right');mask=st>=320;bx.plot(st[mask],rz[mask],c='#344d3a',label='V03 trail');bx.plot(st[-1]+B['station'],B['design_z'][:,10],c='#d09f42',label='V04 pad');bx.axvspan(bar['station_m']-1,bar['station_m']+1,color='#7e59b5',alpha=.25,label='Barrier');bx.axvspan(sel['station_m']-sel['radius_m'],sel['station_m']+sel['radius_m'],color='#b7603b',alpha=.2,label='Combat reserve');bx.axvline(hero['station_m'],color='#325b37',ls='--',label='Hero tree station');bx.set(xlabel='Trail station (m)',ylabel='Z (m)',title='B | Event sequence / measured profile');bx.grid(alpha=.2);bx.legend(fontsize=8);fig.suptitle('MOSS FOREST A3  |  V01  •  DESIGN ONLY');fig.savefig(O/'sanctuary_v01.png',dpi=160);plt.close(fig)
q['outputs']={p.name:sha(p) for p in [Path(__file__),O/'sanctuary_v01.png']};(O/'qa.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k not in ['arena_candidates','barrier_candidates','tree_candidates']},indent=2));print('candidate counts',len(arenas),len(barriers),len(trees))
