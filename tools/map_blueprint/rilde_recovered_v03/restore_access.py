"""Recovery only: replay recorded V03 north regrade on SHA-pinned reconstructed V02 assembly."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh
O=Path(__file__).resolve().parent
P=Path(sys.argv[1]) if len(sys.argv)>1 else O.parent/'r ilde_terrain_recovery/region_recovery_inspection.glb'.replace(' ','')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='884a4a5f3370eeb9aa972e25835b78b51b4e8b4c671e088effc613524ee663d2'
assert sha(P)==expected
s=trimesh.load(P,force='scene',process=False); R=np.array([[1,0,0],[0,0,1],[0,-1,0]])
def world(n,scene):
 t,g=scene.graph[n];return trimesh.transform_points(scene.geometry[g].vertices,t)@R
def plateau(x,y):return 18+3*np.sin(np.pi*y/300)+.006*(x+175)+.85*np.sin((x+175)/74)*np.sin(y/85)
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def fort(x,y):return plateau(x,y)+smooth((y-300)/180)*(28+3*np.cos(x/55)+2*np.sin((y-470)/60))
def grade(x,y):
 f=np.clip((y-300)/275,0,1);return np.where(y<=575,plateau(x,300)*(1-f)+fort(x,575)*f,fort(x,y))
scene=trimesh.Scene();changed=[];targets={'DUNVAR_FORTRESS':(4040,7.3142897538754),'IF07_FORT_CONNECTOR':(1470,7.525036180030106)}
for n in sorted(s.graph.nodes_geometry):
 t,g=s.graph[n];m=s.geometry[g].copy()
 if n in targets:
  v=world(n,s);z0=v[:,2].copy();v[:,2]=grade(v[:,0],v[:,1]);m.vertices=trimesh.transform_points(v@R.T,np.linalg.inv(t));c=int(np.count_nonzero(abs(v[:,2]-z0)>1e-5));d=float(max(abs(v[:,2]-z0)));assert c==targets[n][0] and abs(d-targets[n][1])<1e-8;changed.append(dict(id=n,changed_vertices=c,max_abs_delta_m=d))
 scene.add_geometry(m,node_name=n,geom_name=g,transform=t)
out=O/'rilde_recovered_access_v03.glb';out.write_bytes(scene.export(file_type='glb'));new=trimesh.load(out,force='scene',process=False)
protected=[]
for n in s.graph.nodes_geometry:
 t,g=s.graph[n];t2,g2=new.graph[n];assert np.array_equal(t,t2) and np.array_equal(s.geometry[g].faces,new.geometry[g2].faces)
 if n not in targets:
  assert np.array_equal(s.geometry[g].vertices,new.geometry[g2].vertices);protected.append(n)
def edge(scene,n,y):
 v=world(n,scene);v=v[np.isclose(v[:,1],y)&(v[:,0]>=-25)&(v[:,0]<=25)];return v[np.argsort(v[:,0])]
seams=[]
for a,b,y in [('COASTAL_MEADOW','IF07_FORT_CONNECTOR',300),('IF07_FORT_CONNECTOR','DUNVAR_FORTRESS',475)]:
 A,B=edge(new,a,y),edge(new,b,y);gap=float(np.max(abs(A-B)));assert A.shape==B.shape and gap<3e-6;seams.append(dict(a=a,b=b,vertices=len(A),max_delta_m=gap))
def sampler(n):
 v=world(n,new);xs=np.unique(v[:,0]);ys=np.unique(v[:,1]);Z=np.empty((len(ys),len(xs)));Z[np.searchsorted(ys,v[:,1]),np.searchsorted(xs,v[:,0])]=v[:,2]
 def f(x,y):
  x=np.asarray(x);y=np.asarray(y);i=np.clip(np.searchsorted(xs,x,side='right')-1,0,len(xs)-2);j=np.clip(np.searchsorted(ys,y,side='right')-1,0,len(ys)-2);u=(x-xs[i])/(xs[i+1]-xs[i]);w=(y-ys[j])/(ys[j+1]-ys[j]);return np.where(u>=w,Z[j,i]+u*(Z[j,i+1]-Z[j,i])+w*(Z[j+1,i+1]-Z[j,i+1]),Z[j,i]+w*(Z[j+1,i]-Z[j,i])+u*(Z[j+1,i+1]-Z[j+1,i]))
 return f
fc=sampler('IF07_FORT_CONNECTOR');ff=sampler('DUNVAR_FORTRESS');y=np.arange(300,600.01,.25);zz=np.array([np.where(y<=475,fc(np.full_like(y,x),y),ff(np.full_like(y,x),y)) for x in [-1,0,1]])
maxgrade=float(np.max(abs(np.diff(zz,axis=1))/.25)*100);cross=float(np.max(abs(zz[2]-zz[0])/2)*100);assert maxgrade<=15 and cross<=10
assert sha(P)==expected
q=dict(status='RECONSTRUCTED_V03_NOT_BYTE_IDENTICAL_NOT_ADOPTED',source_sha256=expected,output_sha256=sha(out),script_sha256=sha(Path(__file__)),original_v03_expected_sha256='6f24df182e23ddd2bcbe784e13715c10c4b10042409d534ba6c11ca02fe7c77f',changed=changed,protected=protected,seams=seams,grade_percent=maxgrade,cross_grade_percent=cross,grade_samples=int(zz.size),geometries=len(new.geometry),vertices=sum(len(m.vertices) for m in new.geometry.values()),triangles=sum(len(m.faces) for m in new.geometry.values()),gates=dict(G1='BLOCKED',G2='NOT_RUN',G3='PARTIAL_RECOVERY',G4='NOT_RUN'))
(O/'recovery_v03_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
