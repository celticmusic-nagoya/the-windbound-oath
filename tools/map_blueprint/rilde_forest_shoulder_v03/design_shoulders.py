"""Read-only sampled forest shoulder and vegetation envelope design. No native edit."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent; S=Path(sys.argv[1]); P=Path(sys.argv[2]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)=='09d94cee74a58fcc09dd0999a9b091c60f540b899ebd8ea3a7c061c658746d5d'
T=[('a1',(400,-200,0),'b5e3d099fedbf694d38331bd41ff947bc38f1e48fa9b785d22839c1ff140b19d'),('a2',(500,-300,0),'2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc'),('a3',(600,-400,0),'e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b')];R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
tris=[];planes=[];bounds=[];grids=[]
for k,o,h in T:
 p=S/f'moss_forest_{k}.glb';assert sha(p)==h;m=trimesh.load(p,force='mesh',process=False);v=m.vertices@R+o;f=m.faces;t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=-n[:,:2]/n[:,2,None];tris.extend(sh.polygons(t[:,:,:2]));planes.extend(np.column_stack([g,t[:,0,2]-np.sum(g*t[:,0,:2],axis=1)]));bounds.append(box(*np.r_[v[:,:2].min(0),v[:,:2].max(0)]));grids.append((v,f))
tris=np.array(tris,dtype=object);planes=np.array(planes);tree=sh.STRtree(tris);domain=unary_union(bounds)
def z(xy):
 a,b=tree.query(sh.points(xy),predicate='intersects');out=np.full(len(xy),np.nan);out[a]=(planes[b,:2]*xy[a]).sum(1)+planes[b,2];assert np.isfinite(out).all();return out
A=np.load(P);s=A['station'];xy=A['xy'];H=A['source_z'];Z=A['design_z'];c=xy[:,4];n=(xy[:,-1]-xy[:,0])/2;N=len(s);assert np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-9
assert np.max(abs(z(xy.reshape(-1,2)).reshape(H.shape)-H))<1e-9
attempts=[];best=None
for w in [.5,1.,1.5,2.]:
 d=np.linspace(0,w,int(w/.25)+1); taper=1-(d/w)**2*(3-2*d/w); sides=[];stats=[]
 for j,sign in [(0,-1),(-1,1)]:
  Q=xy[:,j,None,:]+sign*d[None,:,None]*n[:,None,:];B=z(Q.reshape(-1,2)).reshape(Q.shape[:2]);C=B+(Z[:,j]-H[:,j])[:,None]*taper;C[:,0]=Z[:,j];M=len(d);V=np.dstack([Q,C]).reshape(-1,3);i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();f=np.stack([np.stack([i,i+M,i+M+1],1),np.stack([i,i+M+1,i+1],1)],1).reshape(-1,3);t=V[f];normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert np.all(abs(normal[:,2])>1e-9);g=-normal[:,:2]/normal[:,2,None];grade=np.linalg.norm(g,axis=1);foot=Polygon(np.vstack([Q[:,0],Q[::-1,-1]]));assert foot.is_valid;stats.append(dict(side=sign,triangles=len(f),max_grade_pct=float(100*grade.max()),over_50_count=int(np.count_nonzero(grade>.5+1e-9)),outside_m2=foot.difference(domain).area,inner_residual_m=float(np.max(abs(C[:,0]-Z[:,j]))),outer_sample_residual_m=float(np.max(abs(C[:,-1]-B[:,-1]))),max_end_residual_m=float(np.max(abs((C-B)[[0,-1]]))),area_m2=foot.area));sides.append((Q,B,C,foot))
 rec=dict(width_each_m=w,sides=stats);attempts.append(rec)
 if all(a['over_50_count']==0 and a['outside_m2']<1e-8 and a['inner_residual_m']<1e-9 and a['outer_sample_residual_m']<1e-9 for a in stats):best=(rec,sides);break
assert best is not None;rec,sides=best
# Explicit geometric placement mask: exclude trunks/root footprints from trail + shoulders; 1 m reserve beyond earthwork.
road=Polygon(np.vstack([xy[:,0],xy[::-1,-1]]));earth=unary_union([road]+[a[3] for a in sides]);exclusion=earth.buffer(1.,quad_segs=16).intersection(domain)
# Provisional endpoint survey only; no altar geometry or flat pad assumed.
end=Point(c[-1]);clearing=end.buffer(6,quad_segs=64);ids=tree.query(clearing,predicate='intersects');areas=sh.area(sh.intersection(tris[ids],clearing));valid=ids[areas>1e-9];slope=np.linalg.norm(planes[valid,:2],axis=1);axis=np.arange(c[-1,0]-6,c[-1,0]+6.01,.25);ay=np.arange(c[-1,1]-6,c[-1,1]+6.01,.25);X,Y=np.meshgrid(axis,ay);pts=np.c_[X.ravel(),Y.ravel()];pts=pts[np.linalg.norm(pts-c[-1],axis=1)<=6];Zc=z(pts);clearing_stats=dict(center_xy=c[-1].tolist(),radius_m=6,area_m2=clearing.area,outside_terrain_m2=clearing.difference(domain).area,triangles=len(valid),samples=len(pts),height_range_m=[float(Zc.min()),float(Zc.max())],max_grade_pct=float(100*slope.max()),area_above_10_pct_m2=float(areas[np.linalg.norm(planes[ids,:2],axis=1)>.1].sum()),status='SURVEY_ONLY_NOT_ALTAR_PLACEMENT')
assert all(sha(S/f'moss_forest_{k}.glb')==h for k,o,h in T) and sha(P)=='09d94cee74a58fcc09dd0999a9b091c60f540b899ebd8ea3a7c061c658746d5d'
np.savez_compressed(O/'forest_shoulders_v03.npz',station=s,road_xy=xy,road_z=Z,left_xy=sides[0][0],left_source_z=sides[0][1],left_design_z=sides[0][2],right_xy=sides[1][0],right_source_z=sides[1][1],right_design_z=sides[1][2]);p=np.load(O/'forest_shoulders_v03.npz');assert np.array_equal(p['road_z'],Z) and np.array_equal(p['left_design_z'],sides[0][2]) and np.array_equal(p['right_design_z'],sides[1][2])
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(15,6),layout='constrained')
for v,f in grids:ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=13,vmax=37,shading='gouraud')
for poly in sh.get_parts(exclusion):ax.fill(*poly.exterior.xy,color='#d3b778',alpha=.9)
ax.plot(*c.T,color='#223c29',lw=1.5);ax.plot(*clearing.exterior.xy,color='#b24d2a',lw=2);ax.set(aspect='equal',title='A | Trail + planting exclusion',xlabel='X (m)',ylabel='Y (m)')
k=int(np.argmax(np.max(abs(Z-H),axis=1)));width=rec['width_each_m'];offset=np.r_[-1-np.linspace(width,0,sides[0][1].shape[1]),np.linspace(-1,1,9),1+np.linspace(0,width,sides[1][1].shape[1])];before=np.r_[sides[0][1][k,::-1],H[k],sides[1][1][k]];after=np.r_[sides[0][2][k,::-1],Z[k],sides[1][2][k]];bx.plot(offset,before,'--',label='Actual ground');bx.plot(offset,after,label='Design');bx.axvspan(-1,1,color='#d4b885',alpha=.25);bx.set(title=f'B | Cross section at {s[k]:.1f} m',xlabel='Cross offset (m)',ylabel='Z (m)');bx.legend();bx.grid(alpha=.25)
im=cx.scatter(pts[:,0],pts[:,1],c=Zc,cmap='terrain',s=10);cx.plot(*clearing.exterior.xy,c='#a75030');cx.set(aspect='equal',title='C | Endpoint ground survey',xlabel='X (m)',ylabel='Y (m)');fig.colorbar(im,ax=cx,label='Z (m)');fig.suptitle('MOSS FOREST V03 | SHOULDER DESIGN AND ENDPOINT SURVEY — NOT NATIVE');fig.savefig(O/'forest_shoulders_v03.png',dpi=150);plt.close(fig)
q=dict(status='DESIGN_ONLY_NOT_ADOPTED',source_sha256={k:h for k,o,h in T},v02_sha256=sha(P),attempts=attempts,selected=rec,station_count=N,road_samples=Z.size,shoulder_samples=sum(a[2].size for a in sides),earthwork_plan_area_m2=earth.area,exclusion_area_m2=exclusion.area,exclusion_geometry=sh.geometry.mapping(exclusion),root_reserve_m=1,clearing_survey=clearing_stats,inputs_unchanged=True,limits=['Outer boundary matches at sampled vertices only; no continuous conforming terrain triangulation or weld.','Planting exclusion is provisional for root footprints; canopy overhang and actual species assets not assessed.','Endpoint survey is not actual altar or foundation. 50% shoulder slope is a provisional art-design target, no geotechnical claim. D4 NOT_RUN, G1 BLOCKED, G2-G4 NOT_RUN.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'forest_shoulders_v03.npz',O/'forest_shoulders_v03.png']});(O/'forest_shoulders_v03.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k!='exclusion_geometry'},indent=2))
