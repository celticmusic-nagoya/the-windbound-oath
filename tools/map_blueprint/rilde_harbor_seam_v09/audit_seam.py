"""Measured design calibration; never overwrite recovered scene or original assets."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent
P,Q=map(Path,sys.argv[1:3])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','e9101ea9c35ac68d432a9449bba8c79b95da0456302a15d1c920e74ef2258470']
assert [sha(P),sha(Q)]==expected
scene=trimesh.load(P,force='scene',process=False);R=np.array([[1,0,0],[0,0,1],[0,-1,0]])
t,g=scene.graph['RILDE_VILLAGE'];m=scene.geometry[g];v=trimesh.transform_points(m.vertices,t)@R
xs=np.unique(v[:,0]);ys=np.unique(v[:,1]);Z=np.empty((len(ys),len(xs)));Z[np.searchsorted(ys,v[:,1]),np.searchsorted(xs,v[:,0])]=v[:,2]
assert len(v)==len(xs)*len(ys) and ys[0]==-125
# Verify actual face diagonals; interpolator is valid only for this topology.
xy=v[m.faces,:2];span=np.ptp(xy,axis=1);assert np.allclose(span,2.5)
for tri in xy:
 lo=tri.min(axis=0);hi=tri.max(axis=0);assert any(np.array_equal(p,lo) for p in tri) and any(np.array_equal(p,hi) for p in tri)
def sample(x,y):
 x,y=np.broadcast_arrays(x,y);assert np.all((x>=xs[0])&(x<=xs[-1])&(y>=ys[0])&(y<=ys[-1]))
 i=np.clip(np.searchsorted(xs,x,side='right')-1,0,len(xs)-2);j=np.clip(np.searchsorted(ys,y,side='right')-1,0,len(ys)-2);u=(x-xs[i])/2.5;w=(y-ys[j])/2.5
 a,b,c,d=Z[j,i],Z[j,i+1],Z[j+1,i],Z[j+1,i+1]
 return np.where(u>=w,a+u*(b-a)+w*(d-b),a+w*(c-a)+u*(d-c))
A=np.array(json.loads(Q.read_text())['road_cross_sections_s_offset_xyz']);s=A[:,0,0];X,Y,H=A[:,:,2],A[:,:,3],A[:,:,4].copy()
assert np.all(Y[0]==-125) and np.allclose(np.diff(X[0]),.25)
D=np.hypot(np.diff(X,axis=0),np.diff(Y,axis=0));h=sample(X[0],Y[0]);inside=sample(X[0],Y[0]+.01);target=(h-inside)/.01
# Match the actual source seam and first finite-difference slope, fade to zero in 10m.
L=10.;u=np.clip(s/L,0,1);b0=(1-u)**2*(1+2*u);b1=L*u*(1-u)**2
r=h-H[0];k=(h+target*D[0]-H[1]-b0[1]*r)/b1[1]
H2=H+b0[:,None]*r+b1[:,None]*k
assert np.array_equal(H2[s>=L],H[s>=L]);assert np.array_equal(H2[-1],H[-1])
# Exact sampled seam across union of both surface boundary breakpoints.
x=np.unique(np.r_[np.linspace(X[0,0],X[0,-1],301),X[0],xs[(xs>=X[0,0])&(xs<=X[0,-1])]])
ref=sample(x,np.full_like(x,-125));old=np.interp(x,X[0],H[0]);new=np.interp(x,X[0],H2[0]);
def metrics(z):
 return {'seam_max_m':float(np.max(abs(np.interp(x,X[0],z[0])-ref))),'entry_slope_jump_pp':float(100*np.max(abs((z[1]-z[0])/D[0]-target))),'long_grade_max_pct':float(100*np.max(abs(np.diff(z,axis=0)/D))),'cross_grade_max_pct':float(100*np.max(abs(np.diff(z,axis=1))/np.hypot(np.diff(X,axis=1),np.diff(Y,axis=1))))}
a,b=metrics(H),metrics(H2);assert b['seam_max_m']<1e-8 and b['entry_slope_jump_pp']<1e-8 and b['long_grade_max_pct']<=15 and b['cross_grade_max_pct']<=10
# Export isolated analytical ribbon, not native or collision mesh; no edits to source scene.
n,w=H.shape;idx=np.arange((n-1)*(w-1));i=(idx//(w-1))*w+idx%(w-1);F=np.stack([np.stack([i,i+w,i+w+1],1),np.stack([i,i+w+1,i+1],1)],1).reshape(-1,3);V=np.column_stack([X.ravel(),Y.ravel(),H2.ravel()]);origin=np.array([-140,-125,0]);mesh=trimesh.Trimesh((V-origin)@R.T,F,process=False);assert mesh.is_winding_consistent and (mesh.area_faces>0).all() and (mesh.face_normals[:,1]>0).all();mesh.visual.face_colors=[178,156,113,255];ribbon=O/'road_seam_diagnostic.glb';ribbon.write_bytes(mesh.export(file_type='glb'));re=trimesh.load(ribbon,force='mesh',process=False);assert np.array_equal(re.faces,F);roundtrip=float(np.max(abs(re.vertices@R+origin-V)))
fig,ax=plt.subplots(1,3,figsize=(14,4.5),layout='constrained');ax[0].plot(x,(old-ref)*1000,label='V07');ax[0].plot(x,(new-ref)*1000,label='V09');ax[0].set(title='A | Village seam residual',xlabel='East X (m)',ylabel='Height residual (mm)');ax[0].legend();ax[0].grid(alpha=.2)
for j in (0,6,12):
 ax[1].plot(s[:45],(H2-H)[:45,j]*100,label=f'offset {A[0,j,1]:+.2f} m')
ax[1].set(title='B | Local height correction',xlabel='Road station (m)',ylabel='Correction (cm)');ax[1].legend(fontsize=8);ax[1].grid(alpha=.2)
ax[2].plot(X[:,0],Y[:,0],c='#7a694e');ax[2].plot(X[:,-1],Y[:,-1],c='#7a694e');ax[2].plot(X[:,6],Y[:,6],c='#b79a68');ax[2].plot(X[0],Y[0],c='#407d69',lw=3,label='Measured 3 m seam');ax[2].set(xlim=(-180,-95),ylim=(-215,-115),aspect='equal',title='C | Road corridor (design)',xlabel='East X (m)',ylabel='North Y (m)');ax[2].legend(fontsize=8);ax[2].grid(alpha=.2)
fig.suptitle('RILDE V09 | ACTUAL RECOVERED MESH INTERFACE — DESIGN CALIBRATION');fig.savefig(O/'seam_audit.png',dpi=160);plt.close(fig)
A[:,:,4]=H2;np.save(O/'road_sections_v09.npy',A)
q=dict(status='MEASURED_DESIGN_CALIBRATION_NOT_ADOPTED',sources=expected,baseline='reconstructed V03, not original',sample_count=len(x),cross_sections=n,trace_count=w,source_faces_checked=len(m.faces),before=a,after=b,max_height_correction_m=float(np.max(abs(H2-H))),changed_sample_count=int(np.count_nonzero(abs(H2-H)>1e-10)),unchanged_after_station_m=L,mesh=dict(vertices=len(V),triangles=len(F),origin_m=origin.tolist(),roundtrip_error_m=roundtrip),outputs={p.name:sha(p) for p in [ribbon,O/'seam_audit.png',O/'road_sections_v09.npy',Path(__file__)]},gates=dict(D0='PARTIAL',D1='PARTIAL_RECOVERED',D2='PARTIAL',D3='HOLD_ORIGINAL_AND_D4',D4='NOT_RUN',G1='BLOCKED',G2='NOT_RUN',G3='PARTIAL_DIAGNOSTIC',G4='NOT_RUN'),limitations='No harbor terrain outside existing village; no road cut/fill, foundation, CG, native, or navigation QA. Slope matching is finite sampled, not continuous smoothness. Ribbon diagnostic only, not game mesh.')
assert [sha(P),sha(Q)]==expected
(O/'seam_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
