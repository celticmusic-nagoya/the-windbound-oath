"""Recover exact V02 tiles only, no precision edits. V01 colors are unknown."""
import json,hashlib,sys
from pathlib import Path
import numpy as np,trimesh
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def plateau(x,y):return 18+3*np.sin(np.pi*y/300)+.006*(x+175)+.85*np.sin((x+175)/74)*np.sin(y/85)
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def forest(x,y):return plateau(x,y)+smooth((x-375)/45)*(5*np.sin((x-375)/39)*np.cos((y+245)/50)+9*np.exp(-((x-610)/86)**2-((y+395)/95)**2))
def fort(x,y):return plateau(x,y)+smooth((y-300)/180)*(28+3*np.cos(x/55)+2*np.sin((y-470)/60))
def river(x,y):
 c=np.interp(y,[-250,-170,0,250],[338.8235294118,320,300,315]);s=smooth((abs(x-c)-5)/25);bed=4+.012*(y+250)-1.6;return bed*(1-s)+plateau(x,y)*s
# V02 original source, exact colors, mesh generation, and individual mesh GLB exporter.
T=[('MOSS_FOREST_A1',(375,-300,500,-100),(400,-200,0),forest,[102,137,92,255],'b5e3d099fedbf694d38331bd41ff947bc38f1e48fa9b785d22839c1ff140b19d'),('MOSS_FOREST_A2',(400,-400,600,-300),(500,-300,0),forest,[89,122,79,255],'2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc'),('MOSS_FOREST_A3',(500,-500,700,-400),(600,-400,0),forest,[82,112,75,255],'e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b'),('IF07_FORT_CONNECTOR',(-25,300,25,475),(0,387.5,0),fort,[151,153,110,255],'9bfa4d2e46eab9cb1a33295a4d354ad1479db3477bc0a6208b191e93a6fdc146'),('DUNVAR_FORTRESS',(-125,475,125,725),(0,600,0),fort,[155,151,123,255],'480226276267a405666553822dc3eab289e2cafa92f21de1e0a12a835226307f')]
# V01 recorded formulas, topology and offsets; colors are provisional, not known originals.
C=[('RILDE_VILLAGE',(-150,-125,150,112.5),(0,0,0),plateau,[147,153,105,255],'26423b38a20f2729b246e257a952b3b23e2fe7c2966c5530423c23b2a0a85d9f'),('COASTAL_MEADOW',(-150,112.5,150,300),(0,200,0),plateau,[123,154,96,255],'34b0fafd089b0b1aa46eb684357aa412f1997aac0559ae0d72722940df6df01d'),('RIVER_CORRIDOR',(225,-250,375,250),(300,0,0),river,[124,146,103,255],'db4a73324ec35866795b9edbdb595855d9dd0f32746803e5b62be87679e2d6a0'),('IF01_CLIFF_CONNECTOR',(-175,37.5,-150,87.5),(-162.5,62.5,0),plateau,[142,148,112,255],'25ec87e9eccb14026e01c2d650e49fd9d55c82fec7deaadc633df8370a7b9395'),('IF03_RIVER_CONNECTOR',(150,-25,225,25),(187.5,0,0),plateau,[142,148,112,255],'201146dd8f455aed096c7be75045c10d237ca2bcc1b8a555edfcea274d51af8a')]
scene=trimesh.Scene(); records=[]; grids={}
for n,b,o,func,color,expected in T+C:
 x=np.arange(b[0],b[2]+1,2.5);y=np.arange(b[1],b[3]+1,2.5);X,Y=np.meshgrid(x,y);Z=func(X,Y);v=np.column_stack([X.ravel(),Y.ravel(),Z.ravel()]);M=len(x);N=len(y);a=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();f=np.stack([np.stack([a,a+1,a+M+1],1),np.stack([a,a+M+1,a+M],1)],1).reshape(-1,3);m=trimesh.Trimesh((v-o)@R.T,f,process=False);m.visual.face_colors=color;assert m.is_winding_consistent and (m.area_faces>0).all();p=O/(n.lower()+'.glb');p.write_bytes(m.export(file_type='glb'));actual=sha(p);loaded=trimesh.load(p,force='mesh',process=False);assert len(loaded.vertices)==len(m.vertices) and np.array_equal(loaded.faces,m.faces);grids[n]=loaded.vertices@R+o;t=np.eye(4);t[:3,3]=R@np.array(o);scene.add_geometry(loaded,node_name=n,geom_name=n,transform=t)
 records.append(dict(id=n,vertices=len(v),triangles=len(f),expected_sha256=expected,actual_sha256=actual,byte_match=actual==expected,origin_m=o,classification='EXACT_RECOVERY' if actual==expected else 'RECONSTRUCTED_NOT_ORIGINAL'))
# The exact V02 baseline north tiles remain V02, not the regraded V03 geometry.
def edge(n,axis,value,lo,hi):
 v=grids[n];other=1-axis;v=v[np.isclose(v[:,axis],value)&(v[:,other]>=lo)&(v[:,other]<=hi)];return v[np.argsort(v[:,other])]
seams=[]
for a,b,axis,k,lo,hi in [('RILDE_VILLAGE','COASTAL_MEADOW',1,112.5,-150,150),('IF01_CLIFF_CONNECTOR','RILDE_VILLAGE',0,-150,37.5,87.5),('RILDE_VILLAGE','IF03_RIVER_CONNECTOR',0,150,-25,25),('IF03_RIVER_CONNECTOR','RIVER_CORRIDOR',0,225,-25,25),('RIVER_CORRIDOR','MOSS_FOREST_A1',0,375,-250,-100),('MOSS_FOREST_A1','MOSS_FOREST_A2',1,-300,400,500),('MOSS_FOREST_A2','MOSS_FOREST_A3',1,-400,500,600),('COASTAL_MEADOW','IF07_FORT_CONNECTOR',1,300,-25,25),('IF07_FORT_CONNECTOR','DUNVAR_FORTRESS',1,475,-25,25)]:
 A,B=edge(a,axis,k,lo,hi),edge(b,axis,k,lo,hi);assert A.shape==B.shape;delta=float(np.max(np.abs(A-B)));assert delta<5e-6;seams.append(dict(a=a,b=b,samples=len(A),max_xyz_delta_m=delta))
p=O/'region_recovery_v02.glb';p.write_bytes(scene.export(file_type='glb'));s=trimesh.load(p,force='scene',process=False);assert len(s.geometry)==10
for n in scene.geometry:assert np.array_equal(s.geometry[n].vertices,scene.geometry[n].vertices) and np.array_equal(s.geometry[n].faces,scene.geometry[n].faces)
q=dict(status='RECOVERY_BASELINE_NOT_V03_NOT_ADOPTED',tiles=records,seams=seams,combined_sha256=sha(p),script_sha256=sha(Path(__file__)),limitations=['V01 color and original bytes not recovered; V02 north tiles predate V03 road regrade. No water, bridge, harbor, cliff, native or runtime integration.'],gates={'G1':'BLOCKED','G2':'NOT_RUN','G3':'PARTIAL_RECONSTRUCTION','G4':'NOT_RUN'})
(O/'recovery_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
