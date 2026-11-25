"""Exact V02 water recipe, using reconstructed V01 river; SHA is decisive."""
import hashlib,json
from pathlib import Path
import numpy as np,trimesh
from scipy.spatial import cKDTree
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
P=O/'river_corridor.glb';assert sha(P)=='fddfee34946a9cdcb336ff3422c75b6837af78ea10e9447bed83dc1f11adda57'
m=trimesh.load(P,force='mesh',process=False);rv=m.vertices@R+[300,0,0];rf=m.faces
def water(y):return 4+.012*(np.asarray(y)+250)
diff=rv[:,2]-water(rv[:,1]);V=[];F=[];lookup={};shore_res=[];shore_points=[]
def vertex(p):
 k=tuple(np.round(p[:2],9))
 if k not in lookup:lookup[k]=len(V);V.append([p[0],p[1],float(water(p[1]))])
 return lookup[k]
for f in rf:
 if np.all(diff[f]>0):continue
 poly=[]
 for i,j in zip(f,np.roll(f,-1)):
  a,b=rv[i],rv[j];da,db=diff[i],diff[j]
  if da<=0:poly.append(a)
  if (da<0<db) or (db<0<da):
   t=da/(da-db);p=a+t*(b-a);poly.append(p);shore_res.append(abs(p[2]-water(p[1])));shore_points.append(p)
 ids=[vertex(p) for p in poly]
 for k in range(1,len(ids)-1):
  if len({ids[0],ids[k],ids[k+1]})==3:F.append([ids[0],ids[k],ids[k+1]])
V=np.asarray(V);F=np.asarray(F);W=trimesh.Trimesh((V-[300,0,0])@R.T,F,process=False);W.visual.face_colors=[61,126,160,255];assert W.is_winding_consistent and (W.area_faces>0).all()
counts=np.bincount(W.edges_unique_inverse);assert counts.max()==2
bound=W.edges_unique[counts==1];shore_edges=bound[~(np.all(np.isclose(V[bound,1],-250),axis=1)|np.all(np.isclose(V[bound,1],250),axis=1))];shore_set=np.unique(shore_edges);SP=np.asarray(shore_points);shore_gap=float(cKDTree(SP[:,:2]).query(V[shore_set,:2])[0].max());assert shore_gap<1e-7 and max(shore_res)<1e-9
p=O/'river_water_clipped.glb';p.write_bytes(W.export(file_type='glb'));re=trimesh.load(p,force='mesh',process=False);assert np.array_equal(re.faces,W.faces);err=float(np.max(np.abs(re.vertices@R+[300,0,0]-V)))
expected='4043fbc171b2b16f138a1b406c2df72846c8fb625fb05ea5ab9e28d8e6f59bcd';actual=sha(p);q=dict(source_reconstructed_river_sha256=sha(P),expected_sha256=expected,actual_sha256=actual,byte_match=actual==expected,vertices=len(V),triangles=len(F),shoreline_vertices=len(shore_set),shoreline_xy_gap_m=shore_gap,preexport_intersection_residual_m=max(shore_res),reopen_max_xyz_delta_m=err,script_sha256=sha(Path(__file__)),limitations='No verification of original river GLB; only water output SHA comparison. No mouth, no native or runtime.');(O/'water_recovery_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
