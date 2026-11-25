import hashlib, json, sys
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent
P=Path(sys.argv[1]) if len(sys.argv)>1 else O.parent/'r ilde_recovery/east_river_bridge_reconstructed.glb'.replace(' ','')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='83a686b88b556e1f38632f381e433ea7b21b9ceaeedbc5f6e0461de9d8c4e73f'
assert sha(P)==expected
R=np.array([[1,0,0],[0,0,1],[0,-1,0]])
origin=np.array([300,0,0]); source=trimesh.load(P,force='scene',process=False)
v=(source.geometry['EAST_RIVER_BRIDGE_ARCH'].vertices@R+origin).reshape(-1,4,3)
ends=v[[0,-1],2,2]; step=.25

def terrain_grid(x,y):
    center=np.interp(y,[-250,-170,0,250],[338.8235294118,320,300,315]); p=18+3*np.sin(np.pi*y/300)+.006*(x+175)+.85*np.sin((x+175)/74)*np.sin(y/85); t=np.clip((abs(x-center)-5)/25,0,1); s=t*t*(3-2*t); bed=4+.012*(y+250)-1.6
    return (bed*(1-s)+p*s).astype(np.float32).astype(float)
def terrain(x,y):
    x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float)); x0=np.floor(x/2.5)*2.5;y0=np.floor(y/2.5)*2.5;u=(x-x0)/2.5;w=(y-y0)/2.5
    a=terrain_grid(x0,y0);b=terrain_grid(x0+2.5,y0);c=terrain_grid(x0,y0+2.5);d=terrain_grid(x0+2.5,y0+2.5)
    return np.where(u>=w,a+u*(b-a)+w*(d-b),a+w*(c-a)+u*(d-c))
def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)
def correction(x,y,edge,deck):
    # Joint plane fixed to recovered deck across total 4m. Smoothly fade to zero at 5m longitudinal and transverse bounds.
    return (deck-terrain(edge,y))*(1-smooth(abs(x-edge)/5))*(1-smooth((abs(y)-2)/3))
def make_mesh(X,Y,Z):
    n,m=X.shape;i=np.arange((n-1)*(m-1)).reshape(n-1,m-1);a=(i//(m-1))*m+i%(m-1);b=a+1;c=a+m;d=c+1
    f=np.stack([np.stack([a,b,d],-1),np.stack([a,d,c],-1)],-2).reshape(-1,3)
    mesh=trimesh.Trimesh((np.column_stack([X.ravel(),Y.ravel(),Z.ravel()])-origin)@R.T,f,process=False)
    mesh.visual.face_colors=[112,143,101,255];assert mesh.is_winding_consistent and np.min(mesh.area_faces)>0
    return mesh
scene=source.copy();records=[];grids=[]
for name,edge,deck,sign in [('WEST',270,ends[0],-1),('EAST',330,ends[1],1)]:
    x=np.arange(edge-5,edge+5+step/2,step);y=np.arange(-5,5+step/2,step);X,Y=np.meshgrid(x,y);old=terrain(X,Y);delta=correction(X,Y,edge,deck);new=old+delta
    mesh=make_mesh(X,Y,new);scene.add_geometry(mesh,node_name=name+'_BANK_TEST',geom_name=name+'_BANK_TEST')
    grids.append((name,edge,deck,sign,X,Y,old,new))
    # Test bounds, wet exclusion, gradient and bridge deck intrusion on isolated surface.
    joint=(X==edge)&(abs(Y)<=2);border=(abs(X-edge)==5)|(abs(Y)==5);corridor=(abs(Y)<=1.5);water=7+.012*Y
    assert not np.any((abs(delta)>1e-9)&(old<=water));assert np.max(abs(delta[border]))<1e-10
    records.append(dict(side=name,edge_x_m=edge,deck_z_m=float(deck),samples=int(joint.sum()),before_max_abs_joint_m=float(np.max(abs(old[joint]-deck))),max_cut_m=float(max(0,-delta.min())),max_fill_m=float(max(0,delta.max())),border_samples=int(border.sum()),triangles=len(mesh.faces),vertices=len(mesh.vertices)))
out=O/'bridge_bank_calibration_v04.glb';out.write_bytes(scene.export(file_type='glb'));re=trimesh.load(out,force='scene',process=False)
for n in source.geometry:
    assert np.array_equal(source.geometry[n].vertices,re.geometry[n].vertices) and np.array_equal(source.geometry[n].faces,re.geometry[n].faces)
for record,(name,edge,deck,sign,X,Y,old,new) in zip(records,grids):
    m=re.geometry[name+'_BANK_TEST'];z=(m.vertices@R+origin)[:,2].reshape(X.shape)
    joint=(X==edge)&(abs(Y)<=2);border=(abs(X-edge)==5)|(abs(Y)==5)
    exterior=(sign*(X-edge)>=0);inner=(sign*(X-edge)<=0)&(abs(Y)<=2)
    longitudinal=np.abs(np.diff(z,axis=1))/step*100;transverse=np.abs(np.diff(z,axis=0))/step*100
    longmask=exterior[:,1:]&exterior[:,:-1]&(abs(Y[:,1:])<=1.5);crossmask=exterior[1:,:]&(abs(Y[1:,:])<=1.5)&(abs(Y[:-1,:])<=1.5)
    deckline=np.interp(X,v[:,0,0],v[:,2,2]); intrusion=np.maximum(z-deckline,0)
    record.update(after_max_abs_joint_m=float(np.max(abs(z[joint]-deck))),max_border_residual_m=float(np.max(abs(z[border]-old[border]))),longitudinal_grade_max_percent=float(longitudinal[longmask].max()),cross_grade_max_percent=float(transverse[crossmask].max()),max_bridge_intrusion_m=float(intrusion[inner].max()),roundtrip_max_error_m=float(np.max(abs(z-new))))
    assert record['after_max_abs_joint_m']<=.005 and record['max_border_residual_m']<=.00001 and record['longitudinal_grade_max_percent']<=15 and record['cross_grade_max_percent']<=10 and record['max_bridge_intrusion_m']<=.005
assert sha(P)==expected
fig,ax=plt.subplots(2,2,figsize=(12,7),layout='constrained')
for i,(name,edge,deck,sign,X,Y,old,new) in enumerate(grids):
    a,b=ax[i];j=X.shape[0]//2
    for k,l in [(j-8,'south'),(j,'center'),(j+8,'north')]:
        a.plot(X[k],(old[k]-deck)*100,ls='--',alpha=.65,label='before '+l);a.plot(X[k],(new[k]-deck)*100,label='after '+l)
    a.axvline(edge,color='black',lw=.7);a.axhline(0,color='gray',lw=.7);a.set(title=name+' approach / longitudinal profiles',xlabel='East (m)',ylabel='Relative to joint deck (cm)');a.legend(ncol=2,fontsize=7);a.grid(alpha=.2)
    c=b.pcolormesh(X,Y,(new-old)*100,cmap='RdBu_r',shading='auto',vmin=-12,vmax=12);b.axvline(edge,color='black',lw=.7);b.axhline(2,color='gray',ls=':');b.axhline(-2,color='gray',ls=':');b.set(title=name+' cut / fill (cm)',xlabel='East (m)',ylabel='North (m)',aspect='equal');fig.colorbar(c,ax=b)
fig.suptitle('V04 BANK TRANSITION CALIBRATION / RECONSTRUCTED GROUND ONLY');fig.savefig(O/'bank_transition_v04.png',dpi=150)
qa=dict(status='CALIBRATION_ONLY_NOT_PRODUCTION',source_bridge_sha256=expected,source_terrain='V01 formula reconstruction; original V03 combined GLB not available',frame='bridge local, X east/Y up/Z south in GLB, provisional metre',patches=records,protected_bridge_meshes=3,geometry_count=len(re.geometry),sample_step_m=step,criteria={'joint_max_m':.005,'border_max_m':.00001,'grade_long_percent':15,'grade_cross_percent':10,'intrusion_max_m':.005},method='Cubic smoothstep full-width terrain cut/fill, 5m fade in longitudinal and transverse directions; no bridge mutation',outputs={'glb_sha256':sha(out),'preview_sha256':sha(O/'bank_transition_v04.png'),'script_sha256':sha(Path(__file__))},design={'D0':'PARTIAL','D1':'PARTIAL','D2':'PARTIAL_CALIBRATION','D3':'BLOCKED_ORIGINAL_TERRAIN','D4':'NOT_RUN'},gates={'G1':'BLOCKED','G2':'NOT_RUN','G3':'PARTIAL_CALIBRATION','G4':'NOT_RUN'},limitations='Open patch surfaces are isolated replacement samples, not overlays to add to terrain; no actual V03 region integration, foundation strength, masonry, Blender or independent QA.')
(O/'bank_transition_qa.json').write_text(json.dumps(qa,indent=2)+'\n');print(json.dumps(qa,indent=2))
