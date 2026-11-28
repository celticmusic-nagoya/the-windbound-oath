"""Local design overlay, not native terrain edit. Shared indices, main-road Z priority."""
import sys,hashlib,json
from pathlib import Path
import numpy as np, shapely as sh, trimesh
from shapely.geometry import Polygon
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection,PolyCollection
O=Path(__file__).resolve().parent
T,U,J=map(Path,sys.argv[1:4]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','40f8ea9359aeb3cd69c742fb366728c89b1a80670059cd7e40a263a790db9c03','c5f529f863766221d1fddc561ef2e16bed15b1d70b8aa0683bbb706465022d0f'];assert [sha(p) for p in (T,U,J)]==expected
B=np.load(T);D=np.load(U);old=np.load(J)['triangles'];s=B['station'];i0=np.searchsorted(s,145);i1=np.searchsorted(s,171)+1;grid=1e-8

def tri(q,h):
 n,k=h.shape;i=(np.arange(n-1)[:,None]*k+np.arange(k-1)).ravel();f=np.stack([np.stack([i,i+k,i+k+1],1),np.stack([i,i+k+1,i+1],1)],1).reshape(-1,3);return np.dstack([q,h]).reshape(-1,3)[f]
def plane(t):
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);g=-n[:,:2]/n[:,2,None];return np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)]
main=np.concatenate([tri(B[k+'_xy'][i0:i1],B[k+'_design_z' if k!='road' else 'road_z'][i0:i1]) for k in ['left','road','right']]);spur=tri(D['xy'],D['design_z']);mp=sh.polygons(main[:,:,:2]);sp=sh.polygons(spur[:,:,:2]);mg=plane(main);sg=plane(spur)
M=sh.union_all(mp);S=sh.union_all(sp);target=M.union(S);clip=sh.union_all(sh.polygons(old[:,:,:2]));assert S.difference(M).symmetric_difference(clip).area<1e-7
# Node all source triangle boundaries with a common precision grid. Main surface owns overlap.
lines=sh.union_all(np.concatenate([sh.boundary(mp),sh.boundary(sh.polygons(old[:,:,:2]))]),grid_size=grid);cells=sh.get_parts(sh.polygonize(sh.get_parts(lines)));mt=sh.STRtree(mp);st=sh.STRtree(sp);out=[];owners=[];parents=[];orphans=0
for p in cells:
 if p.area<=1e-16:continue
 pt=p.representative_point();mi=mt.query(pt,predicate='intersects');si=st.query(pt,predicate='intersects');
 if len(mi):owner=0;parent=int(mi[0])
 elif len(si):owner=1;parent=int(si[0])
 else:orphans+=1;continue
 for t in sh.get_parts(sh.constrained_delaunay_triangles(p)):
  q=np.asarray(t.exterior.coords)[:3];a=np.linalg.det(np.array([q[1]-q[0],q[2]-q[0]]));
  if a<0:q=q[[0,2,1]]
  if abs(a)<=1e-16:continue
  out.append(q);owners.append(owner);parents.append(parent)
xy=np.array(out);owner=np.array(owners);parent=np.array(parents);keys=np.rint(xy.reshape(-1,2)/grid).astype(np.int64);keys,ind,inv=np.unique(keys,axis=0,return_index=True,return_inverse=True);vxy=keys*grid;f=inv.reshape(-1,3);z=np.full(len(vxy),np.nan);orig=np.empty_like(xy[:,:,0]);
for i,g in enumerate([mg,sg]):
 ids=np.flatnonzero(owner==i);p=g[parent[ids]];orig[ids]=np.einsum('nki,ni->nk',xy[ids],p[:,:2])+p[:,2,None]
# Shared vertex heights from main triangles first. Within each surface same original vertex heights agree.
for i in [1,0]:
 ids=np.flatnonzero(owner==i);z[f[ids].ravel()]=orig[ids].ravel()
assert np.isfinite(z).all();v=np.c_[vxy,z];delta=np.abs(z[f]-orig);m=trimesh.Trimesh(v,f,process=False);edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);e,ei,ec=np.unique(edges,axis=0,return_inverse=True,return_counts=True);eo=np.tile(owner,3);mn=np.full(len(e),2);mx=np.full(len(e),-1);np.minimum.at(mn,ei,eo);np.maximum.at(mx,ei,eo);seam=e[(mn==0)&(mx==1)];bound=e[ec==1];bd=sh.union_all(sh.linestrings(vxy[bound]));p=sh.polygons(vxy[f]);u=sh.union_all(p);area=sh.area(p);ncomp=connected_components(coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(v),len(v))),directed=False,return_labels=False)
# Boundary vertices must have degree 2; interior edges two opposite incidences (winding).
be=np.bincount(bound.ravel(),minlength=len(v));direct=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);sign=np.where(direct[:,0]<direct[:,1],1,-1);bal=np.bincount(ei,weights=sign,minlength=len(e));a2=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])[:,2];
# Compare assigned surfaces to source planes over each new face; within each cell affine extrema at vertices.
qa=dict(status='DESIGN_TOPOLOGY_SCREEN',input_sha256=expected,grid_m=grid,main_station_range_m=[float(s[i0]),float(s[i1-1])],source_main_triangles=len(main),source_spur_triangles=len(spur),polygon_cells=len(cells),orphan_cells=orphans,vertices=len(v),faces=len(f),connected_components=int(ncomp),edges_over_two_faces=int(sum(ec>2)),interior_winding_errors=int(sum((ec==2)&(bal!=0))),boundary_degree_errors=int(sum((be!=0)&(be!=2))),nonpositive_area_faces=int(sum(a2<=0)),min_double_area_m2=float(a2.min()),area_sum_minus_union_m2=float(area.sum()-u.area),coverage_symdiff_m2=u.symmetric_difference(target).area,boundary_length_m=bd.length,boundary_outside_target_1um_m=bd.difference(target.boundary.buffer(1e-6)).length,target_boundary_missing_1um_m=target.boundary.difference(bd.buffer(1e-6)).length,shared_seam_edges=len(seam),shared_seam_vertices=len(np.unique(seam)),shared_seam_length_m=float(np.linalg.norm(vxy[seam[:,0]]-vxy[seam[:,1]],axis=1).sum()),max_main_vertex_height_change_m=float(delta[owner==0].max()),max_spur_vertex_height_change_m=float(delta[owner==1].max()),source_unchanged=[sha(p) for p in (T,U,J)]==expected,limits=['Local open surface design, not welded to full terrain or native model. Main surface retained to numerical precision; spur adjusted at junction only. Precision grid 10nm, no physical accuracy implied. No runtime collision, drainage, D4 or art acceptance.'])
np.savez_compressed(O/'junction_weld_v12.npz',vertices=v,faces=f,face_owner=owner,source_triangle=parent,seam_edges=seam);a=np.load(O/'junction_weld_v12.npz');assert np.array_equal(a['vertices'],v) and np.array_equal(a['faces'],f)
fig,(ax,bx)=plt.subplots(1,2,figsize=(12,6),layout='constrained');colors=np.where(owner==0,'#c3b29a','#739879');ax.add_collection(PolyCollection(vxy[f],facecolors=colors,edgecolors='none'));ax.add_collection(LineCollection(vxy[seam],colors='#902b29',linewidths=1.4));ax.autoscale();ax.set_aspect('equal');ax.set(title='A | Local shared-index design',xlabel='East X (m)',ylabel='North Y (m)');bx.add_collection(PolyCollection(vxy[f],facecolors=colors,edgecolors='#595d52',linewidths=.25));bx.add_collection(LineCollection(vxy[seam],colors='#b32d2d',linewidths=2));mid=vxy[seam].mean(axis=(0,1));bx.set(xlim=(mid[0]-3,mid[0]+3),ylim=(mid[1]-3,mid[1]+3),aspect='equal',title='B | Junction topology (red = shared seam)',xlabel='East X (m)',ylabel='North Y (m)');fig.suptitle('MOSS A2 V12 | CONFORMING DESIGN OVERLAY — NOT NATIVE');fig.savefig(O/'junction_v12.png',dpi=170);plt.close(fig)
qa['outputs']={p.name:sha(p) for p in [Path(__file__),O/'junction_weld_v12.npz',O/'junction_v12.png']};(O/'qa.json').write_text(json.dumps(qa,indent=2)+'\n');print(json.dumps(qa,indent=2))
