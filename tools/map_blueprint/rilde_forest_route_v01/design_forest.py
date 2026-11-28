"""Read-only forest trail design on SHA-exact V02 terrain, not final navigation."""
import hashlib,json,sys,heapq
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import LineString,Polygon,Point,box
from shapely.ops import unary_union
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent; S=Path(sys.argv[1]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
T=[('a1',(400,-200,0),'b5e3d099fedbf694d38331bd41ff947bc38f1e48fa9b785d22839c1ff140b19d'),('a2',(500,-300,0),'2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc'),('a3',(600,-400,0),'e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b')]
tris=[];slopes=[];planes=[];bounds=[];grids=[]
for k,o,h in T:
 p=S/f'moss_forest_{k}.glb';assert sha(p)==h;m=trimesh.load(p,force='mesh',process=False);v=m.vertices@R+o;f=m.faces;t=v[f];pol=sh.polygons(t[:,:,:2]);n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert np.all(n[:,2]>0);g=-n[:,:2]/n[:,2,None];tris.extend(pol);slopes.extend(np.linalg.norm(g,axis=1));planes.extend(np.column_stack([g,t[:,0,2]-np.sum(g*t[:,0,:2],axis=1)]));b=box(*np.r_[v[:,:2].min(0),v[:,:2].max(0)]);bounds.append(b);grids.append((v,f))
tris=np.array(tris,dtype=object);slopes=np.array(slopes);planes=np.array(planes);tree=sh.STRtree(tris);domain=unary_union(bounds);bad=unary_union(tris[slopes>.18+1e-10]);safe=domain.difference(bad).buffer(-1.001);start=(380.,-230.);goal=(690.,-490.)
def z(xy):
 pts=sh.points(xy);a,b=tree.query(pts,predicate='intersects');out=np.full(len(xy),np.nan);out[a]=np.sum(planes[b,:2]*xy[a],axis=1)+planes[b,2];return out
def audit(line):
 foot=line.buffer(1);ids=tree.query(foot,predicate='intersects');areas=sh.area(sh.intersection(tris[ids],foot));i=ids[areas>1e-9];return dict(length_m=line.length,area_m2=foot.area,outside_terrain_m2=foot.difference(domain).area,triangles_intersected=len(i),max_triangle_grade_pct=float(100*max(slopes[i])),over_limit_area_m2=float(areas[slopes[ids]>.18+1e-10].sum()),max_slope_threshold_pct=18)
initial=LineString([start,(445,-300),(550,-400),goal]);a0=audit(initial);print('initial',a0,'start/goal safe',safe.covers(Point(start)),safe.covers(Point(goal)),flush=True)
# A* on 2.5m lattice, restricting every segment to full-width safe terrain.
step=2.5; nodes=np.array([(x,y) for x in np.arange(375,700.01,step) for y in np.arange(-500,-99.99,step)]);mask=sh.covers(safe,sh.points(nodes));allowed={tuple(q) for q in nodes[mask]};print('allowed',len(allowed),flush=True)
assert start in allowed and goal in allowed
# Direction-dependent threshold: 15% longitudinal, 10% transverse;
# test all triangles touched by the segment's 1m-radius capsule.
from functools import lru_cache
@lru_cache(None)
def segment_ok(a,b):
 d=np.subtract(b,a);d=d/np.linalg.norm(d);n=np.array([-d[1],d[0]])
 ln=LineString([a,b]);foot=ln.buffer(1)
 if not safe.covers(ln):return False
 ids=tree.query(foot,predicate='intersects');g=planes[ids,:2]
 return bool(np.max(abs(g@d))<=.15+1e-10 and np.max(abs(g@n))<=.10+1e-10)
queue=[(0.,0.,start)];dist={start:0.};parent={};done=set()
while queue:
 _,d,u=heapq.heappop(queue)
 if u in done:continue
 done.add(u)
 if u==goal:break
 for dx,dy in [(i*step,j*step) for i,j in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1),(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(-1,2),(1,-2),(-1,-2),(3,1),(3,-1),(-3,1),(-3,-1),(1,3),(-1,3),(1,-3),(-1,-3)]]:
  v=(u[0]+dx,u[1]+dy)
  if v not in allowed or v in done:continue
  if not segment_ok(u,v):continue
  c=d+np.hypot(dx,dy)
  if c<dist.get(v,np.inf):dist[v]=c;parent[v]=u;heapq.heappush(queue,(c+np.linalg.norm(np.subtract(v,goal)),c,v))
assert goal in dist,'No safe path with fixed endpoints'
path=[goal]
while path[-1]!=start:path.append(parent[path[-1]])
path=path[::-1];# greedy line-of-sight simplification within safe corridor
out=[path[0]];i=0
while i<len(path)-1:
 j=len(path)-1
 while j>i+1 and not segment_ok(path[i],path[j]):j-=1
 out.append(path[j]);i=j
line=LineString(out);a=audit(line);
assert all(segment_ok(u,v) for u,v in zip(out,out[1:]));lng=[];cr=[]
for u,v in zip(out,out[1:]):
 d=np.subtract(v,u);d=d/np.linalg.norm(d);ids=tree.query(LineString([u,v]).buffer(1),predicate='intersects');g=planes[ids,:2];lng.append(float(100*max(abs(g@d))));cr.append(float(100*max(abs(g@np.array([-d[1],d[0]])))))
print('directional',max(lng),max(cr),flush=True)
assert max(lng)<=15+1e-8 and max(cr)<=10+1e-8
a.update(max_full_width_long_pct=max(lng),max_full_width_cross_pct=max(cr));assert a['outside_terrain_m2']<1e-8 and a['over_limit_area_m2']<1e-8 and a['max_triangle_grade_pct']<=18+1e-8
# exact height interpolation from actual triangles; include seams at vertices and station samples
stations=np.linspace(0,line.length,int(np.ceil(line.length/.25))+1);xy=np.array([line.interpolate(float(s)).coords[0] for s in stations]);zz=z(xy);assert np.isfinite(zz).all();grade=np.max(abs(np.diff(zz)/np.diff(stations)))*100
# Cross sections at straight segment interiors, not at corners. Full footprint already checked.
seam=[]
for y in [-300,-400]:
 p=line.intersection(LineString([(375,y),(700,y)]));assert p.geom_type=='Point';xy0=np.array(p.coords[0]);seam.append(dict(y_m=y,xy_m=xy0.tolist(),z_m=float(z(xy0[None,:])[0])))
assert all(sha(S/f'moss_forest_{k}.glb')==h for k,o,h in T)
q=dict(status='FOREST_TRAIL_DESIGN_CANDIDATE_NOT_ADOPTED',source_sha256={k:h for k,o,h in T},frame='provisional m X east Y north Z up',route_width_m=2,initial=a0,final=a,route_xy=out,seams=seam,profile_samples=len(stations),max_sampled_longitudinal_grade_pct=float(grade),endpoint_z_m=[float(zz[0]),float(zz[-1])],limits=['Start is inside A1, not a proven river landing; endpoint is a provisional approach near altar locator (700,-500), not altar position or foundation.','No vegetation assets or collision/navmesh/native/render QA; no terrain edits. D4 NOT_RUN, G1 BLOCKED, G2-G4 NOT_RUN.'],method='A* on 2.5m lattice with 24 directions and line-of-sight simplification, all triangles intersecting each 1m capsule checked against 15% longitudinal and 10% transverse; exact polygon intersection of 2m corridor with measured triangles; 0.25m profile')
(O/'forest_route_v01.json').write_text(json.dumps(q,indent=2)+'\n');np.savetxt(O/'forest_route_profile.csv',np.column_stack([stations,xy,zz]),delimiter=',',header='station_m,x_m,y_m,z_m',comments='')
fig,(ax,bx)=plt.subplots(1,2,figsize=(12,6),layout='constrained');
for v,f in grids:ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=13,vmax=37,shading='gouraud')
for poly in (list(bad.geoms) if bad.geom_type=='MultiPolygon' else [bad]):ax.fill(*poly.exterior.xy,color='#a83232',alpha=.32)
ax.plot(*initial.xy,'--',color='#a35539',label='Direct candidate');ax.plot(*line.xy,color='#152c25',lw=2,label='Slope-filtered trail');ax.scatter([start[0],goal[0]],[start[1],goal[1]],c='#ffefbe',edgecolors='k',zorder=5);ax.set(aspect='equal',title='A | Actual V02 terrain and 2 m trail',xlabel='East X (m)',ylabel='North Y (m)');ax.legend(fontsize=8);ax.grid(alpha=.2);bx.plot(stations,zz,color='#365e48');bx.set(title='B | Measured centerline profile',xlabel='Station (m)',ylabel='Z (m)');bx.grid(alpha=.2);fig.suptitle('MOSS FOREST | PROVISIONAL TRAIL DESIGN — NO TERRAIN EDIT',weight='bold');fig.savefig(O/'forest_route_v01.png',dpi=160);plt.close(fig);print(json.dumps(q,indent=2))
