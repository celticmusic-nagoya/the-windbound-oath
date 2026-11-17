"""Exact non-adjacent triangle penetration + coplanar-overlap screening."""
from pathlib import Path
import json,bpy
import numpy as np
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01'
EPS=1e-9

def pierce(p,q,t):
 d=q-p;e1=t[1]-t[0];e2=t[2]-t[0];h=np.cross(d,e2);det=np.dot(e1,h)
 if abs(det)<1e-14:return False
 s=p-t[0];u=np.dot(s,h)/det;r=np.cross(s,e1);v=np.dot(d,r)/det;z=np.dot(e2,r)/det
 return EPS<u<1-EPS and EPS<v and u+v<1-EPS and EPS<z<1-EPS

def orient(a,b,c):return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
def inside(p,t):
 vals=[orient(t[i],t[(i+1)%3],p) for i in range(3)]
 return min(vals)>EPS or max(vals)<-EPS

def coplanar_overlap(a,b):
 n=np.cross(a[1]-a[0],a[2]-a[0]);mag=np.linalg.norm(n)
 if mag<1e-13:return False
 n/=mag
 if np.max(abs((b-a[0])@n))>1e-8:return False
 k=int(np.argmax(abs(n)));aa=np.delete(a,k,axis=1);bb=np.delete(b,k,axis=1)
 if any(inside(p,bb) for p in aa) or any(inside(p,aa) for p in bb):return True
 for i in range(3):
  for j in range(3):
   p,q=aa[i],aa[(i+1)%3];r,s=bb[j],bb[(j+1)%3]
   if orient(p,q,r)*orient(p,q,s)<-EPS**2 and orient(r,s,p)*orient(r,s,q)<-EPS**2:return True
 return np.max(np.linalg.norm(np.sort(aa,axis=0)-np.sort(bb,axis=0),axis=1))<EPS

def screen(points,faces,patchids=None):
 v=np.array(points);tri=[];parents=[]
 for fi,f in enumerate(faces):
  for k in range(1,len(f)-1):tri.append([f[0],f[k],f[k+1]]);parents.append(fi)
 tree=BVHTree.FromPolygons(v.tolist(),tri,all_triangles=True,epsilon=0.0);pairs=set();cop=set();candidates=0;adjacent_pairs=set()
 for i,j in tree.overlap(tree):
  if i>=j or parents[i]==parents[j] or set(tri[i])&set(tri[j]):continue
  candidates+=1;a=v[tri[i]];b=v[tri[j]];f=tuple(sorted((parents[i],parents[j])))
  if any(pierce(a[k],a[(k+1)%3],b) or pierce(b[k],b[(k+1)%3],a) for k in range(3)):
   if set(faces[parents[i]])&set(faces[parents[j]]):adjacent_pairs.add(f)
   else:pairs.add(f)
  elif not (set(faces[parents[i]])&set(faces[parents[j]])) and coplanar_overlap(a,b):cop.add(f)
 local=pairs if patchids is None else {p for p in pairs if patchids[p[0]] or patchids[p[1]]}
 folds=[]
 for i,f in enumerate(faces):
  if len(f)!=4:continue
  p=v[f];cosines=[]
  for a,b,c,d in [(0,1,2,3),(1,2,3,0)]:
   n1=np.cross(p[b]-p[a],p[c]-p[a]);n2=np.cross(p[c]-p[a],p[d]-p[a]);den=np.linalg.norm(n1)*np.linalg.norm(n2);cosines.append(float(n1@n2/den) if den>1e-16 else -1)
  if min(cosines)<=0:folds.append({'face':i,'patch':patchids[i] if patchids else None,'both_diagonal_min_normal_cos':min(cosines)})
 return {'nonshared_vertex_BVH_triangle_candidates':candidates,'strict_non_coplanar_face_pairs':len(pairs),'strict_pairs':sorted(pairs),'adjacent_face_interior_penetration_pairs':sorted(adjacent_pairs),'adjacent_face_interior_penetration_count':len(adjacent_pairs),'coplanar_overlap_face_pairs':len(cop),'coplanar_pairs':sorted(cop),'patch_involved_strict_face_pairs':len(local),'patch_involved_strict_pairs':sorted(local),'quad_fold_flags':folds,'quad_fold_flags_count':len(folds),'scope':'Nonadjacent polygon-face pairs are primary; adjacent-face interior penetrations are recorded separately. Shared triangle-vertex contacts excluded. Strict segment-interior triangle crossings and coplanar area tests. Quads tested with both diagonals.'}

if __name__=='__main__':
 S=json.loads((Q/'source-mesh.json').read_text());C=json.loads((Q/'candidate-mesh.json').read_text());a=screen(S['world'],S['faces']);b=screen(C['world'],C['faces'],C['patch_ids'])
 (Q/'self-intersection-qa.json').write_text(json.dumps({'source':a,'candidate':b,'all_local_intersections_resolved':b['patch_involved_strict_face_pairs']==0 and not b['coplanar_overlap_face_pairs'],'G3_intersection_screen':'PASS' if b['patch_involved_strict_face_pairs']==0 and not b['coplanar_overlap_face_pairs'] else 'FAIL'},indent=2)+'\n')
 print('source strict',a['strict_non_coplanar_face_pairs'],'candidate',b['strict_non_coplanar_face_pairs'],'patch',b['patch_involved_strict_face_pairs'],'coplanar',b['coplanar_overlap_face_pairs'],'newquadfold',sum(x['patch']>0 for x in b['quad_fold_flags']))
