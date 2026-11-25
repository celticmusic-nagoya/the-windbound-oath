import numpy as np, trimesh, hashlib
from pathlib import Path
O=Path(__file__).parent
R=np.array([[1,0,0],[0,0,1],[0,-1,0]])
# Reconstructed from V01 source height formula and V03 recovered build_access.py; not the original unless SHA matches.
xx=np.arange(225,375.01,2.5); p=18+.006*(xx+175); t=np.clip((abs(xx-300)-5)/25,0,1); s=t*t*(3-2*t); z=(5.4*(1-s)+p*s).astype(np.float32).astype(float)
ground=lambda x:np.interp(x,xx,z)
x=np.linspace(270,330,241);deck=ground(270)+.04+(ground(330)-ground(270))*(x-270)/60
u=abs(x-300)/14;arch=6+12*np.sqrt(np.clip(1-u*u,0,1));blend=np.clip((u-1)/.35,0,1);bottom=np.where(u<=1,arch,6*(1-blend)+(ground(x)-.30)*blend);bottom=np.minimum(bottom,deck-.65)
def sweep(x,lo,hi,y0,y1):
 V=np.stack([np.column_stack([x,np.full_like(x,y0),lo]),np.column_stack([x,np.full_like(x,y1),lo]),np.column_stack([x,np.full_like(x,y1),hi]),np.column_stack([x,np.full_like(x,y0),hi])],axis=1).reshape(-1,3);F=[]
 for j in range(len(x)-1):
  for k in range(4):
   a=j*4+k;b=j*4+(k+1)%4;c=b+4;d=a+4;F.extend([[a,b,c],[a,c,d]])
 F.extend([[0,2,1],[0,3,2],[len(V)-4,len(V)-3,len(V)-2],[len(V)-4,len(V)-2,len(V)-1]])
 m=trimesh.Trimesh(V,np.array(F),process=False);m.fix_normals();assert m.is_watertight and m.is_winding_consistent and m.volume>0;return m
origin=np.array([300.,0,0]);bridge=sweep(x,bottom,deck,-2,2);bridge.visual.face_colors=[133,129,118,255];parts=[('EAST_RIVER_BRIDGE_ARCH',bridge)]
for name,lo,hi in [('NORTH_PARAPET',1.65,2),('SOUTH_PARAPET',-2,-1.65)]:
 m=sweep(x,deck,deck+.85,lo,hi);m.visual.face_colors=[148,142,128,255];parts.append((name,m))
bscene=trimesh.Scene()
for n,m in parts:
 m.vertices=(m.vertices-origin)@R.T;bscene.add_geometry(m,node_name=n,geom_name=n)
bp=O/'east_river_bridge_reconstructed.glb';bp.write_bytes(bscene.export(file_type='glb'));br=trimesh.load(bp,force='scene',process=False)
print('trimesh',trimesh.__version__,'deck',deck[[0,-1]],'sha',hashlib.sha256(bp.read_bytes()).hexdigest(),'mesh counts',[(n,len(m.vertices),len(m.faces),m.is_watertight) for n,m in br.geometry.items()])
# Evaluate contact against reconstructed 2.5m triangulated river terrain; not verified original mesh bytes.
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
expected='83a686b88b556e1f38632f381e433ea7b21b9ceaeedbc5f6e0461de9d8c4e73f'
actual=hashlib.sha256(bp.read_bytes()).hexdigest();assert actual==expected
# Match the V03 terrain interpolation convention (SW to NE diagonal).
def terrain_grid(x,y):
 center=np.interp(y,[-250,-170,0,250],[338.8235294118,320,300,315]); p=18+3*np.sin(np.pi*y/300)+.006*(x+175)+.85*np.sin((x+175)/74)*np.sin(y/85); t=np.clip((abs(x-center)-5)/25,0,1); s=t*t*(3-2*t); bed=4+.012*(y+250)-1.6; return (bed*(1-s)+p*s).astype(np.float32).astype(float)
def terrain(x,y):
 x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float)); x0=np.floor(x/2.5)*2.5;y0=np.floor(y/2.5)*2.5;u=(x-x0)/2.5;v=(y-y0)/2.5
 a=terrain_grid(x0,y0);b=terrain_grid(x0+2.5,y0);c=terrain_grid(x0,y0+2.5);d=terrain_grid(x0+2.5,y0+2.5)
 return np.where(u>=v,a+u*(b-a)+v*(d-b),a+v*(c-a)+u*(d-c))
assert np.allclose(terrain(xx,0),z,atol=1e-7,rtol=0)
# Extract vertices from the byte-identical reloaded bridge. No ground or bridge deformation.
v=br.geometry['EAST_RIVER_BRIDGE_ARCH'].vertices@R+origin
v=v.reshape(-1,4,3);assert np.allclose(v[:,0,0],x)
xb=v[:,0,0];lo=v[:,0,2];hi=v[:,2,2]
y=np.linspace(-2,2,17);X,Y=np.meshgrid(xb,y);Z=terrain(X,Y);L=np.broadcast_to(lo,X.shape);H=np.broadcast_to(hi,X.shape);W=7+.012*Y
wet=Z<=W;clear=L-W;offset=H-Z;embed=Z-L
ends={}
for i,n in [(0,'WEST'),(-1,'EAST')]:
 ends[n]={'deck_minus_ground_min_m':float(offset[:,i].min()),'deck_minus_ground_max_m':float(offset[:,i].max()),'below_ground_samples':int((offset[:,i]<0).sum()),'underside_embed_min_m':float(embed[:,i].min()),'underside_embed_max_m':float(embed[:,i].max())}
qa={'source_bridge_sha256':actual,'source_bridge_status':'BYTE_IDENTICAL_RECOVERED','terrain_status':'FORMULA_RECONSTRUCTION_NOT_VERIFIED_ORIGINAL','sample_grid':{'x_step_m':.25,'y_step_m':.25,'count':int(X.size)},'ends':ends,'clear_deck_width_m':3.3,'deck_longitudinal_grade_percent':float((hi[-1]-hi[0])/60*100),'wet_samples':int(wet.sum()),'wet_clearance_min_m':float(clear[wet].min()),'wet_clearance_max_m':float(clear[wet].max()),'wet_intersection_samples':int((wet&(clear<=0)).sum()),'gates':{'G1':'BLOCKED','G2':'NOT_RUN','G3':'PARTIAL_RECOVERED_MESH_AND_RECONSTRUCTED_TERRAIN','G4':'NOT_RUN'},'limits':'Not original terrain, no physical foundation strength, no independent art QA, no collision/navigation, no new geometry edits.'}
(O/'bridge_contact_audit.json').write_text(json.dumps(qa,indent=2)+'\n'); print(json.dumps(qa,indent=2))
fig,axs=plt.subplots(2,1,figsize=(11,7),layout='constrained');a,b=axs
for j in [0,8,16]:a.plot(xb,Z[j],label=f'ground reconstructed y={y[j]:g} m')
a.fill_between(xb,lo,hi,alpha=.35,label='recovered V03 arch solid');a.axhline(7,ls='--',label='center water');a.set(xlabel='East (provisional m)',ylabel='Elevation (m)',title='V03 bridge — longitudinal section');a.legend(ncol=2,fontsize=8);a.grid(alpha=.2)
for i,n in [(0,'West'),(-1,'East')]:b.plot(y,offset[:,i]*100,marker='.',label=n+' deck minus ground')
b.axhline(0,ls='--');b.set(xlabel='North offset (m)',ylabel='Deck minus ground (cm)',title='Full-width end contact — reconstructed terrain only');b.grid(alpha=.2);b.legend();fig.suptitle('RILDE / SHA-matched bridge recovery & contact audit (PROVISIONAL)');fig.savefig(O/'bridge_contact_audit.png',dpi=150)
