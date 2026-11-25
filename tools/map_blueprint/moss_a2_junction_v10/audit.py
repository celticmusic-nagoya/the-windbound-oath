"""Read-only junction plan partition and LOD/margin sensitivity. No native edit."""
import sys,hashlib,json,csv
from pathlib import Path
import numpy as np,shapely as sh,trimesh
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union,nearest_points
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent
P,V,T,C,U,E=map(Path,sys.argv[1:7]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc','4540ea97d6375515957883be200085025b2546f21b27eaf73454460547af4a54','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','a488d0aa7c421fde2353acdea82f9fdec5fe1f6d52a3eb3ed3d13ac4cd599265','40f8ea9359aeb3cd69c742fb366728c89b1a80670059cd7e40a263a790db9c03','4dd0ce597c90339e38c7589e2ab42ed9837924e6d38226c42065a89766871394'];assert [sha(p) for p in (P,V,T,C,U,E)]==expected
B=np.load(T);D=np.load(U);q=D['xy'];h=D['design_z'];c=D['center'];A=np.load(V)
def triangles(q,h):
 n,k=h.shape;i=(np.arange(n-1)[:,None]*k+np.arange(k-1)).ravel();ff=np.stack([np.stack([i,i+k,i+k+1],1),np.stack([i,i+k+1,i+1],1)],1).reshape(-1,3);return np.dstack([q,h]).reshape(-1,3)[ff]
def planes(t):
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert np.min(abs(n[:,2]))>1e-10;g=-n[:,:2]/n[:,2,None];return np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)]
def footprint(q):return Polygon(np.vstack([q[:,0],q[::-1,-1]]))
def zz(p,g):return p@g[:2]+g[2]
old_t=np.concatenate([triangles(B[k+'_xy'],B[k+'_design_z' if k!='road' else 'road_z']) for k in ['left','right','road']]);sp_t=triangles(q,h);sp_p=sh.polygons(sp_t[:,:,:2]);op=sh.polygons(old_t[:,:,:2]);og=planes(old_t);sg=planes(sp_t);st=sh.STRtree(op);road=unary_union([footprint(B[k+'_xy']) for k in ['left','right','road']]);spur=footprint(q);outside=spur.difference(road);overlap=spur.intersection(road)
# Exact affine residual at polygon/line intersection vertices, before clipping. Retain old panels in overlap.
a,b=st.query(sp_p,predicate='intersects');ints=sh.intersection(sp_p[a],op[b]);maxerr=0.;maxloc=None;areas=[]
for i,j,p in zip(a,b,ints):
 coords=sh.get_coordinates(p)
 if len(coords):
  err=np.abs(zz(coords,sg[i])-zz(coords,og[j]));k=int(err.argmax());
  if err[k]>maxerr:maxerr=float(err[k]);maxloc=coords[k].tolist()
 areas.append(p.area)
# Partition each spur triangle against exact protected footprint; keep the original spur plane in each remnant.
parts=sh.difference(sp_p,road);flat=[];parent=[]
for i,p in enumerate(parts):
 for poly in sh.get_parts(p):
  if poly.geom_type!='Polygon' or poly.area<=1e-12:continue
  for tri in sh.get_parts(sh.constrained_delaunay_triangles(poly)):
   if tri.area>1e-12:
    pts=np.array(tri.exterior.coords)[:3];flat.append(np.c_[pts,zz(pts,sg[i])]);parent.append(i)
flat=np.array(flat);fp=sh.polygons(flat[:,:,:2]);union=unary_union(fp);seam=road.boundary.intersection(spur);seam_a,seam_b=st.query(fp,predicate='intersects');seamerr=0.;seamloc=None;seam_pts=[]
for i,j in zip(seam_a,seam_b):
 cut=fp[i].intersection(op[j]);pts=sh.get_coordinates(cut)
 if len(pts):
  err=np.abs(zz(pts,sg[parent[i]])-zz(pts,og[j]));k=int(err.argmax());seam_pts.extend(pts.tolist());
  if err[k]>seamerr:seamerr=float(err[k]);seamloc=pts[k].tolist()
# Exact check of seam endpoints on both plane partitions, using small buffer for floating point incidence.
for i in np.flatnonzero(sh.distance(fp,road.boundary)<1e-8):
 cut=fp[i].intersection(seam.buffer(1e-8));pts=sh.get_coordinates(cut)
 for pt in pts:
  if Point(pt).distance(seam)>1.1e-8:continue
  ids=st.query(Point(pt),predicate='dwithin',distance=2e-8)
  for j in ids:
   er=float(abs(zz(pt,sg[parent[i]])-zz(pt,og[j])));seam_pts.append(pt.tolist());
   if er>seamerr:seamerr=er;seamloc=pt.tolist()
# Recomputed LOD on both layouts and both routes: all-direction estimate, no culling credits.
def read(p):return list(csv.DictReader(p.open()))
rows=read(C);old=read(E);assert len(rows)==len(old)==451 and [r['id'] for r in rows]==[r['id'] for r in old]
rxy=B['road_xy'][:,4];ii=(rxy[:,0]>=400)&(rxy[:,0]<=600)&(rxy[:,1]>=-400)&(rxy[:,1]<=-300);main=rxy[ii];station=B['station'][ii];ss=np.r_[0,np.cumsum(np.linalg.norm(np.diff(c,axis=0),axis=1))];profiles=[('detail',[18,40,75,120],[1,.35,.1]),('balanced',[12,30,60,100],[1,.25,.06]),('mobile',[8,22,48,90],[1,.18,.04])];curves={};lod=[]
for label,rs in [('V04',old),('V09',rows)]:
 tr=[r for r in rs if r['kind'] in ('ancient_tree_reserve','forest_tall','deciduous')];xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in tr]);radius=np.array([float(r['radius_m']) for r in tr]);counts=np.array([int(r['lod0_triangles']) if r['lod0_triangles'] else 20000 for r in tr]);assert len(tr)==107
 for route,cam in [('main',main),('spur',c)]:
  d=np.maximum(np.linalg.norm(cam[:,None]-xy[None],axis=2)-radius,0)
  for name,threshold,fractions in profiles:
   table=np.vstack([np.ceil(counts*x).astype(int) for x in fractions]+[np.full(len(tr),12),np.zeros(len(tr),int)]);cost=table[np.digitize(d,threshold),np.arange(len(tr))].sum(1);curves[label,route,name]=cost;lod.append(dict(layout=label,route=route,profile=name,samples=len(cam),peak=int(cost.max()),p95=float(np.percentile(cost,95)),peak_index=int(cost.argmax()),under_150k=bool(cost.max()<=150000)))
# V09 stored per-envelope clearance from exact previous exclusion function; do not pretend dimensions are verified.
margins=np.array([float(r['exclusion_clearance_m']) for r in rows]);margin_report=[dict(extra_margin_m=m,below=int(np.sum(margins<m)),tree_below=sum(float(r['exclusion_clearance_m'])<m and r['kind'] in ('ancient_tree_reserve','forest_tall','deciduous') for r in rows)) for m in [.01,.05,.10,.20,.30,.50]]
# candidate partition coordinates; not a welded mesh. No terrain mutation.
np.savez_compressed(O/'junction_partition.npz',triangles=flat,parent_spur_triangle=np.array(parent));assert np.array_equal(np.load(O/'junction_partition.npz')['triangles'],flat)
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(15,5.2),layout='constrained')
for p in sh.get_parts(road):ax.fill(*p.exterior.xy,color='#bdad94',alpha=.7)
for p in sh.get_parts(overlap):ax.fill(*p.exterior.xy,color='#b94c42',alpha=.65)
for p in sh.get_parts(outside):ax.fill(*p.exterior.xy,color='#699e76',alpha=.7)
ax.plot(*c.T,c='#6d492d',lw=1);ax.set(xlim=(c[0,0]-7,c[0,0]+7),ylim=(c[0,1]-8,c[0,1]+7),aspect='equal',title='A | Protected road / clipped spur',xlabel='East X (m)',ylabel='North Y (m)');
if seamloc:ax.scatter(*seamloc,marker='x',c='black',s=55)
for name,_,_ in profiles:bx.plot(ss,curves['V09','spur',name]/1000,label=name)
bx.axhline(150,c='#a54e40',ls='--');bx.set(title='B | V09 spur tree workload',xlabel='Spur distance (m)',ylabel='Estimated triangles (thousands)');bx.legend();bx.grid(alpha=.2)
cx.bar([str(int(m['extra_margin_m']*100)) for m in margin_report],[m['below'] for m in margin_report],color='#9c8054');cx.set(title='C | Reserves below added margin',xlabel='Additional clearance (cm)',ylabel='Reservation count');cx.grid(axis='y',alpha=.2)
fig.suptitle('MOSS A2 V10 | JUNCTION PARTITION & SENSITIVITY — DESIGN ONLY');fig.savefig(O/'junction_v10.png',dpi=160);plt.close(fig)
report=dict(status='DESIGN_PARTITION_HOLD_NATIVE',input_sha256=expected,junction=dict(original_spur_area_m2=spur.area,original_overlap_m2=overlap.area,clipped_area_m2=union.area,clipped_overlap_m2=union.intersection(road).area,coverage_symmetric_difference_m2=union.symmetric_difference(outside).area,triangle_area_sum_minus_union_m2=float(sh.area(fp).sum()-union.area),clipped_triangles=len(flat),overlap_plane_pairs=len(a),max_original_overlap_z_residual_m=maxerr,max_overlap_xy=maxloc,seam_length_m=seam.length,seam_evaluated_points=len(seam_pts),max_seam_z_residual_m=seamerr,max_seam_xy=seamloc),lod=lod,margin=margin_report,lowest_margin_ids=[dict(id=rows[i]['id'],kind=rows[i]['kind'],margin_m=margins[i]) for i in np.argsort(margins)[:10]],source_unchanged=[sha(p) for p in (P,V,T,C,U,E)]==expected,limits=['Clipped planar triangle soup, not welded conforming mesh; original road planes and spur planes are retained. Seam proximity check uses 1e-8m planar buffer; no native seam or drainage proof.','LOD assumes 20k per hero and 12 triangle impostor, no actual meshes/camera, excludes all non-tree cost. Margin sensitivity uses previously computed V09 reserve distances; no verified real asset footprints.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'junction_partition.npz',O/'junction_v10.png']});(O/'qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
