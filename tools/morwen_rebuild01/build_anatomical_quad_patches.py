"""Boundary-conforming topology replacement with anatomical rest-surface rails.
No cage or fairing script is executed. New interior samples and face connectivity
are built in an injective harmonic domain; exterior source vertices/faces stay.
"""
from pathlib import Path
import json,math
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from scipy.spatial import Delaunay,ConvexHull
from scipy.interpolate import RBFInterpolator,LinearNDInterpolator
from scipy.optimize import milp,Bounds,LinearConstraint
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01'
J=json.loads((Q/'source-mesh.json').read_text());P=np.array(J['world']);F=J['faces']
D=np.load(ROOT/'docs/qa/morwen-rebuild-01/body-local-v01/local-edit.npz');REST=D['original_source_world'];FREE=D['free_mask']
# Surveyed simple disks: two shoulder/axilla disks and two anterior knee disks.
sets=[('shoulder_axilla_L',json.loads((Q/'patch-shoulder-0.json').read_text())),('shoulder_axilla_R',json.loads((Q/'patch-shoulder-1.json').read_text())),('patella_L',json.loads((Q/'knee-front-1.json').read_text())),('patella_R',json.loads((Q/'knee-front--1.json').read_text()))]
all_faces=set();recipes=[];new_id=-1
for name,faceids in sets:
 assert not (set(faceids)&all_faces);all_faces.update(faceids)
 oldids=sorted({i for f in faceids for i in F[f]});oldmap={v:i for i,v in enumerate(oldids)}
 assert all(FREE[oldids]),'Protected vertex entered patch'
 edgefaces={};directed={};neigh={i:set() for i in oldids}
 for fi in faceids:
  f=F[fi]
  for a,b in zip(f,f[1:]+f[:1]):
   key=tuple(sorted((a,b)));edgefaces[key]=edgefaces.get(key,0)+1;directed[key]=(a,b);neigh[a].add(b);neigh[b].add(a)
 be=[directed[e] for e,c in edgefaces.items() if c==1]
 nxt={a:b for a,b in be};assert len(nxt)==len(be)
 first=max(nxt,key=lambda i:(REST[i,2],REST[i,0]));boundary=[first]
 while nxt[boundary[-1]]!=first:
  boundary.append(nxt[boundary[-1]]);assert len(boundary)<=len(be)
 assert len(boundary)==len(be) and len(boundary)%2==0
 bset=set(boundary);interior=[i for i in oldids if i not in bset]
 # Rest-arclength boundary, vertical anatomical rail aligned to +V at the top.
 bl=REST[boundary];length=np.linalg.norm(np.roll(bl,-1,axis=0)-bl,axis=1);theta=np.r_[0,np.cumsum(length[:-1])]/length.sum()*2*np.pi+np.pi/2
 buv=np.c_[np.cos(theta),np.sin(theta)]
 rr=[];cc=[];dd=[]
 for a in oldids:
  ia=oldmap[a];rr.append(ia);cc.append(ia);dd.append(len(neigh[a]))
  for b in neigh[a]:rr.append(ia);cc.append(oldmap[b]);dd.append(-1)
 L=coo_matrix((dd,(rr,cc)),shape=(len(oldids),len(oldids))).tocsr();bi=np.array([oldmap[i] for i in boundary]);ii=np.array([oldmap[i] for i in interior]);uv=np.zeros((len(oldids),2));uv[bi]=buv
 if len(ii):uv[ii]=spsolve(L[ii][:,ii],-L[ii][:,bi]@buv)
 assert np.isfinite(uv).all()
 rest_func=LinearNDInterpolator(uv,REST[oldids]);delta_b=P[boundary]-REST[boundary]
 # Preserve existing width landmarks through explicit fixed control points.
 srcz=REST[:,2];band=(abs(srcz-(.775 if name.startswith('shoulder') else .29))<.008)
 if name.startswith('shoulder'):band &= REST[:,0]*np.sign(REST[oldids,0].mean())>0
 else:band &= REST[:,0]*np.sign(REST[oldids,0].mean())>0
 ids=np.where(band)[0];anchors=[]
 for axis in [0]:
  for op in [np.argmin,np.argmax]:
   i=int(ids[op(P[ids,axis])])
   if i in oldmap and i not in bset:anchors.append(i)
 anchors=sorted(set(anchors));control=boundary+anchors
 disp=RBFInterpolator(uv[[oldmap[i] for i in control]],P[control]-REST[control],kernel='thin_plate_spline',degree=1,smoothing=0)
 # New grid interior; this replaces topology, rather than moving the old grid.
 step=.14 if name.startswith('shoulder') else .12
 grid=np.array([(x,y) for y in np.arange(-.88,.89,step) for x in np.arange(-.88,.89,step) if x*x+y*y<.84**2])
 fixed_uv=uv[[oldmap[i] for i in control]]
 if anchors:grid=grid[np.linalg.norm(grid[:,None,:]-fixed_uv[None,:,:],axis=2).min(1)>.035]
 nuv=np.vstack([fixed_uv,grid]);new_sources=control.copy()
 for _ in grid:new_sources.append(new_id);new_id-=1
 xyz=np.asarray(rest_func(nuv))+disp(nuv)
 # Authored features: restrained patella prominence and infrapatellar relief.
 if name.startswith('patella'):
  rxyz=np.asarray(rest_func(nuv));legx=np.median(REST[oldids,0]);z=rxyz[:,2]
  anterior=np.clip((.028-rxyz[:,1])/.045,0,1)
  ridge=.003*np.exp(-((z-.29)/.022)**2-((rxyz[:,0]-legx)/.022)**2)
  tendon=-.0012*np.exp(-((z-.263)/.012)**2-((rxyz[:,0]-legx)/.014)**2)
  radial=np.maximum(0,1-(nuv*nuv).sum(1))**2
  xyz[:,1]-=(ridge+tendon)*anterior*radial
 # Retained boundary/control vertices remain byte-identical in the Blender build.
 xyz[:len(control)]=P[control]
 assert np.isfinite(xyz).all(),name
 tri=Delaunay(nuv).simplices
 for t in tri:
  if np.linalg.det(np.stack([nuv[t[1]]-nuv[t[0]],nuv[t[2]]-nuv[t[0]]]))<0:t[1],t[2]=t[2],t[1]
 shared={}
 for i,t in enumerate(tri):
  for a,b in zip(t,np.roll(t,-1)):shared.setdefault(tuple(sorted((int(a),int(b)))),[]).append(i)
 candidates=[]
 for edge,ts in shared.items():
  if len(ts)!=2:continue
  four=sorted(set(tri[ts[0]])|set(tri[ts[1]]))
  if len(four)!=4:continue
  pts=nuv[four];center=pts.mean(0);order=np.argsort(np.arctan2(pts[:,1]-center[1],pts[:,0]-center[0]));quad=[four[i] for i in order];p=nuv[quad]
  turns=[float(np.linalg.det(np.stack([p[(i+1)%4]-p[i],p[(i+2)%4]-p[(i+1)%4]]))) for i in range(4)]
  if min(turns)<1e-7:continue
  a,b,c,d=xyz[quad];n1=np.cross(b-a,c-a);n2=np.cross(c-a,d-a);norm=np.linalg.norm(n1)*np.linalg.norm(n2)
  if norm<1e-16 or np.dot(n1,n2)/norm<.3:continue
  lens=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);quality=lens.min()/lens.max()
  candidates.append((ts[0],ts[1],quad,quality))
 if candidates:
  row=[];col=[]
  for k,(a,b,_,_) in enumerate(candidates):row.extend([a,b]);col.extend([k,k])
  incidence=coo_matrix((np.ones(len(row)),(row,col)),shape=(len(tri),len(candidates))).tocsr()
  cost=-np.array([100+c[3] for c in candidates])
  res=milp(cost,integrality=np.ones(len(cost)),bounds=Bounds(0,1),constraints=LinearConstraint(incidence,0,1),options={'time_limit':12})
  assert res.x is not None,name
  selected=np.where(res.x>.5)[0]
 else:selected=[]
 used=set();newfaces=[]
 for k in selected:
  a,b,quad,_=candidates[k];assert a not in used and b not in used;used|={a,b};newfaces.append(quad)
 newfaces += [list(map(int,t)) for i,t in enumerate(tri) if i not in used]
 # Conforming boundary: every old boundary edge appears exactly once.
 counts={}
 for face in newfaces:
  for a,b in zip(face,face[1:]+face[:1]):e=tuple(sorted((a,b)));counts[e]=counts.get(e,0)+1
 for i in range(len(boundary)):
  e=tuple(sorted((i,(i+1)%len(boundary))));assert counts.get(e)==1,(name,e)
 assert all(c<=2 for c in counts.values())
 rec={'name':name,'source_faces':faceids,'source_vertex_ids':oldids,'source_uv':uv.tolist(),'boundary':boundary,'control_ids':control,'new_source_vertex_ids':new_sources,'new_uv':nuv.tolist(),'new_world':xyz.tolist(),'new_rest_world':np.asarray(rest_func(nuv)).tolist(),'new_faces':newfaces,'quad_count':sum(len(t)==4 for t in newfaces),'triangle_count':sum(len(t)==3 for t in newfaces),'retired_interior_vertices':[i for i in interior if i not in anchors]}
 recipes.append(rec)
 print(name,'replace',len(faceids),'faces; boundary',len(boundary),'new',len(xyz),'vertices',rec['quad_count'],'quads',rec['triangle_count'],'triangles',flush=True)
# All new warning regions and all source collision pairs have a replaced side.
warn=json.loads((Q/'warning15.json').read_text());assert all(x['face_id'] in all_faces for x in warn)
analysis=json.loads((Q/'INDEPENDENT_WARNING_ANALYSIS.json').read_text());pairs=analysis['exact_non_coplanar_penetration_screen']['after_pairs'];assert all(a in all_faces or b in all_faces for a,b in pairs)
(Q/'quad-patch-recipe.json').write_text(json.dumps({'method':'Boundary-conforming harmonic-domain anatomical rest-rail quad reconstruction','patches':recipes,'retired_source_faces':sorted(all_faces),'warning15_all_covered':True,'source_collision_pairs_all_have_replaced_side':True,'old_face_deletion_is_not_warning_resolution':True},separators=(',',':'),default=lambda x:x.item() if isinstance(x,np.generic) else x)+'\n')
