"""A2 dry-land ecology envelope design; not actual assets or native terrain edits."""
import sys,hashlib,json,csv
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union,nearest_points
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
O=Path(__file__).resolve().parent; P,A,B=map(Path,sys.argv[1:4]); sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc','4540ea97d6375515957883be200085025b2546f21b27eaf73454460547af4a54','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653'];assert [sha(p) for p in (P,A,B)]==expected
m=trimesh.load(P,force='mesh',process=False);v=m.vertices@np.array([[1.,0,0],[0,0,1],[0,-1,0]])+[500,-300,0];f=m.faces;t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=-n[:,:2]/n[:,2,None];b=t[:,0,2]-(g*t[:,0,:2]).sum(1);polys=sh.polygons(t[:,:,:2]);tree=sh.STRtree(polys);domain=unary_union(polys)
Q=np.load(A);T=np.load(B);q=Q['xy'];foot=Polygon(np.vstack([q[:,0],q[::-1,-1]]));road=unary_union([Polygon(np.vstack([T[k][:,0],T[k][::-1,-1]])) for k in ['road_xy','left_xy','right_xy']]);stage=float(Q['water_stage_z'][-1]+.5)
# Reserve every low patch (not just sink-connected) at sensitivity upper stage.
parts=[]
for tri in t:
 p=[]
 for a,c in zip(tri,np.roll(tri,-1,axis=0)):
  if a[2]<=stage:p.append(a[:2])
  if (a[2]<stage<c[2]) or (c[2]<stage<a[2]):p.append((a+(c-a)*(stage-a[2])/(c[2]-a[2]))[:2])
 if len(p)>=3 and Polygon(p).area>1e-10:parts.append(Polygon(p))
wet=unary_union(parts);reserve=unary_union([road.buffer(1),foot.buffer(2),wet.buffer(2)]).intersection(domain)
# Landmark view reserve is plan-only, no camera visibility claim.
fall=Point(480-12.25,-385);trail=LineString(T['road_xy'][:,4]);vp=nearest_points(trail.intersection(domain),fall)[0];view=LineString([vp,fall]).buffer(2.5).intersection(domain);tall_exclusion=unary_union([reserve,view]);rng=np.random.default_rng(20261125)
# Dimensions from ECO manifest, axis-centred reservation assumption, plus sway; no actual mesh placement.
spec={'deciduous':(7.001,7.195,6.003,.22,10647),'forest_tall':(6.454,6.286,7.908,.28,12539),'ancient_tree_reserve':(9,9,11,.4,None),'rock_reserve':(2.4,1.5,1.2,0,None),'fern_cluster':(1.4,1.4,.8,0,None),'moss_patch':(1.2,1.2,.05,0,None)}
rows=[];occupied=[];trees=[];rocks=[];ground=[]
def candidate(kind,x,y,scale):
 w,l,h,sway,tri=spec[kind];r=(np.hypot(w,l)/2+sway)*scale;pt=Point(x,y);disk=pt.buffer(r,quad_segs=64);is_tree=kind in ('deciduous','forest_tall','ancient_tree_reserve');ex=tall_exclusion if is_tree or kind=='rock_reserve' else reserve
 if not domain.covers(disk) or pt.distance(ex)<r+1e-5:return False
 if any(np.hypot(x-a,y-c)<r+rr+(.3 if is_tree else .1) for a,c,rr in occupied):return False
 idx=tree.query(disk,predicate='intersects');slope=float(np.linalg.norm(g[idx],axis=1).max());lim=.25 if is_tree else .40
 if slope>lim:return False
 ii=tree.query(pt,predicate='intersects');z=float(g[ii[0]]@[x,y]+b[ii[0]]);rid=len(rows)+1;rows.append(dict(id=f'A2-ECO-{rid:04d}',kind=kind,x_m=float(x),y_m=float(y),z_m=z,scale=float(scale),radius_m=float(r),height_m=float(h*scale),max_source_grade_pct=100*slope,exclusion_clearance_m=float(pt.distance(ex)-r),lod0_triangles=tri));occupied.append((x,y,r));(trees if is_tree else rocks if kind=='rock_reserve' else ground).append(rows[-1]);return True
# Place 3 landmark reservations first, then canopy clusters, then understory. Fixed seed; density is proposed not canonical.
for target in [(466,-366),(505,-380),(533,-321)]:
 for _ in range(300):
  x,y=np.array(target)+rng.normal(0,4,2)
  if candidate('ancient_tree_reserve',x,y,1):break
for _ in range(12000):
 if len(trees)>=115:break
 x,y=rng.uniform([405,-395],[595,-305]);d=Point(x,y).distance(trail);kind='forest_tall' if d>13 and rng.random()<.65 else 'deciduous';candidate(kind,x,y,rng.uniform(.8,1.08))
for kind,target in [('rock_reserve',24),('fern_cluster',140),('moss_patch',180)]:
 for _ in range(15000):
  if sum(a['kind']==kind for a in rows)>=target:break
  x,y=rng.uniform([402,-398],[598,-302]);pt=Point(x,y)
  if kind!='rock_reserve' and pt.distance(foot.union(wet))>18 and pt.distance(trail)>10 and rng.random()<.8:continue
  candidate(kind,x,y,rng.uniform(.7,1.15))
assert [sha(p) for p in (P,A,B)]==expected
# Independent pairwise numeric validation, analytic circles (not polygon approximation).
xy=np.array([[a['x_m'],a['y_m']] for a in rows]);rad=np.array([a['radius_m'] for a in rows]);dist=np.linalg.norm(xy[:,None]-xy[None,:],axis=2)-rad[:,None]-rad[None,:];np.fill_diagonal(dist,np.inf);assert dist.min()>0
for a in rows:
 pt=Point(a['x_m'],a['y_m']);r=a['radius_m'];assert pt.distance(reserve)>=r and pt.distance(domain.boundary)>=r
 if a['kind'] in ('deciduous','forest_tall','ancient_tree_reserve','rock_reserve'):assert pt.distance(view)>=r
with (O/'placements.csv').open('w',newline='') as out:
 wr=csv.DictWriter(out,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
fig,(ax,bx)=plt.subplots(1,2,figsize=(15,7),layout='constrained');colors={'deciduous':'#86a85c','forest_tall':'#315b3c','ancient_tree_reserve':'#bd963f','rock_reserve':'#77787d','fern_cluster':'#68a886','moss_patch':'#b7bc67'}
for a in (ax,bx):
 a.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=20,vmax=37,shading='gouraud',alpha=.65)
 for p in sh.get_parts(reserve):
  if p.geom_type=='Polygon':a.fill(*p.exterior.xy,c='#577b9e',alpha=.45)
 for p in sh.get_parts(view):
  if p.geom_type=='Polygon':a.fill(*p.exterior.xy,c='#e2be70',alpha=.55)
 a.plot(*trail.xy,c='#653c29',lw=1.1);a.plot(*foot.exterior.xy,c='#164f75',lw=1.2);a.plot(*LineString([vp,fall]).xy,c='#f5e4bd',ls='--');a.set(aspect='equal',xlabel='X (m)',ylabel='Y (m)')
 for r in rows:a.add_patch(Circle((r['x_m'],r['y_m']),r['radius_m'],facecolor=colors[r['kind']],edgecolor='#30392d',lw=.25,alpha=.85))
ax.set(xlim=(400,600),ylim=(-400,-300),title='A | A2 dry-land placement envelopes');bx.set(xlim=(425,525),ylim=(-400,-345),title='B | Valley edge and reserved landmark sightline');from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([0],[0],marker='o',color='none',markerfacecolor=c,label=k,markersize=7) for k,c in colors.items()],fontsize=7,loc='upper left');fig.suptitle('MOSS FOREST A2 | ECOLOGY PLACEMENT DESIGN — NOT NATIVE');fig.savefig(O/'a2_ecology_v04.png',dpi=160);plt.close(fig)
counts={k:sum(r['kind']==k for r in rows) for k in spec};rec=dict(status='PROVISIONAL_ENVELOPES_ONLY',inputs_sha256=expected,seed=20261125,stage_m=stage,low_ground_reserve_m2=wet.area,total_exclusion_m2=reserve.area,view_reserve_m2=view.area,view_xy=[list(vp.coords[0]),list(fall.coords[0])],counts=counts,total=len(rows),min_pair_clearance_m=float(dist.min()),min_exclusion_clearance_m=min(a['exclusion_clearance_m'] for a in rows),max_source_grade_pct=max(a['max_source_grade_pct'] for a in rows),tree_candidate_lod0_triangles=sum(a['lod0_triangles'] or 0 for a in rows),source_unchanged=True,limits=['No asset instancing or actual foliage mesh, centred envelope assumption not verified against mesh origins. Tree canopy disk and wind margin based on unapproved ECO manifest; ancient tree, rock, fern, moss dimensions authored placeholders for space reservation only.','View is plan reservation not actual 3D occlusion proof. Conservative all low-ground mask, not confirmed wet area. No actual ground-contact footprint, LOD, Android or D4.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'placements.csv',O/'a2_ecology_v04.png']});(O/'qa.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))
