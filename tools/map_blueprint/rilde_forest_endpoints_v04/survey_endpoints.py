"""Read-only endpoint survey and provisional altar approach surface design; no native edits."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import LineString,Polygon,Point,box
from shapely.ops import unary_union
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;P,V=map(Path,sys.argv[1:3]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653'];assert list(map(sha,[P,V]))==expected
S=trimesh.load(P,force='scene',process=False);R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def mesh(name):
 t,g=S.graph[name];m=S.geometry[g];return trimesh.transform_points(m.vertices,t)@R,m.faces
names=['RIVER_CORRIDOR','MOSS_FOREST_A1','MOSS_FOREST_A2','MOSS_FOREST_A3'];tris=[];planes=[];grids=[];bounds=[]
for name in names:
 v,f=mesh(name);t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=-n[:,:2]/n[:,2,None];tris.extend(sh.polygons(t[:,:,:2]));planes.extend(np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)]);grids.append((v,f));bounds.append(box(*np.r_[v[:,:2].min(0),v[:,:2].max(0)]))
tris=np.array(tris,dtype=object);planes=np.array(planes);tree=sh.STRtree(tris);domain=unary_union(bounds)
def z(xy):
 xy=np.asarray(xy);a,b=tree.query(sh.points(xy),predicate='intersects');o=np.full(len(xy),np.nan);o[a]=(planes[b,:2]*xy[a]).sum(1)+planes[b,2];assert np.isfinite(o).all();return o
wv,wf=mesh('RIVER_WATER_CLIPPED');water=unary_union(sh.polygons(wv[wf][:,:,:2]));A=np.load(V);road=A['road_xy'];start=road[0,4];end=road[-1,4]
# Screen actual east shore, 1 m-radius dry-ground staging reserve, no canon position assertion.
landings=[]
for y in np.arange(-245,-149.99,2.5):
 waterline=LineString([(225,y),(375,y)]).intersection(water);assert not waterline.is_empty
 shore=np.array([waterline.bounds[2],y]);wet_z=4+.012*(y+250)
 for dx in [2,3,4,5]:
  p=shore+[dx,0];disk=Point(p).buffer(1,quad_segs=32);ids=tree.query(disk,predicate='intersects');g=planes[ids,:2];dry=water.intersection(disk).area<1e-9
  line=LineString([p,start]);foot=line.buffer(1,quad_segs=32);ii=tree.query(foot,predicate='intersects');d=(start-p)/np.linalg.norm(start-p);n=np.array([-d[1],d[0]]);zz=z([p,start]);landings.append(dict(shore_xy=shore.tolist(),candidate_xy=p.tolist(),water_z_m=wet_z,ground_z_m=float(zz[0]),dry=dry,staging_max_grade_pct=float(100*np.max(np.linalg.norm(g,axis=1))),route_length_m=line.length,rise_m=float(zz[1]-zz[0]),max_full_width_long_pct=float(100*np.max(abs(planes[ii,:2]@d))),max_full_width_cross_pct=float(100*np.max(abs(planes[ii,:2]@n))),wet_overlap_m2=foot.intersection(water).area,outside_terrain_m2=foot.difference(domain).area))
eligible=[a for a in landings if a['dry'] and a['wet_overlap_m2']<1e-9 and a['outside_terrain_m2']<1e-9];direct_pass=[a for a in eligible if a['max_full_width_long_pct']<=15 and a['max_full_width_cross_pct']<=10 and a['staging_max_grade_pct']<=10];best=min(eligible,key=lambda a:max(a['max_full_width_long_pct']/15,a['max_full_width_cross_pct']/10,a['staging_max_grade_pct']/10));assert not direct_pass
# Compare the best direct candidate with a representative near-start downstream shore; neither is a certified landing.
near=min(eligible,key=lambda a:np.linalg.norm(np.asarray(a['candidate_xy'])-start));near['min_length_at_15_pct_m']=near['rise_m']/.15
# End clearing: use exact V03 end profile including both shoulder end rows, widen to 6m; grade to flat pad.
normal=(road[-1,-1]-road[-1,0])/2;d=(road[-1,4]-road[-2,4]);d/=np.linalg.norm(d);assert abs(normal@d)<1e-8
old_xy=np.vstack([A['left_xy'][-1,::-1],road[-1,1:],A['right_xy'][-1,1:]]) # correct order reconstructed below
old_xy=np.vstack([A['left_xy'][-1,::-1],road[-1,1:],A['right_xy'][-1,1:]])
old_z=np.r_[A['left_design_z'][-1,::-1],A['road_z'][-1,1:],A['right_design_z'][-1,1:]];off=(old_xy-end)@normal;assert np.all(np.diff(off)>0) and abs(off[0]+2.5)<1e-8 and abs(off[-1]-2.5)<1e-8
st=np.linspace(0,7,29);unit=np.linspace(-1,1,21);half=2.5+.5*np.clip(st/3,0,1);Q=end+st[:,None,None]*d+half[:,None,None]*unit[None,:,None]*normal;H=z(Q.reshape(-1,2)).reshape(Q.shape[:2]);assert np.max(abs(H[0]-old_z))<1e-8
# Fixed seam and horizontal 4 x 6 m area from station 3 to 7. Choose median of measured underlying pad.
flat=float(np.median(H[st>=3]));t=np.clip(st/3,0,1);a=t*t*(3-2*t);Z=H*(1-a[:,None])+flat*a[:,None];Z[0]=old_z
N,M=Z.shape;i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();f=np.stack([np.stack([i,i+M,i+M+1],1),np.stack([i,i+M+1,i+1],1)],1).reshape(-1,3);T=np.dstack([Q,Z]).reshape(-1,3)[f];n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);assert np.all(abs(n[:,2])>1e-9);g=-n[:,:2]/n[:,2,None]
foot=Polygon(np.vstack([Q[:,0],Q[::-1,-1]]));prev=Polygon(np.vstack([A['left_xy'][:, -1],A['right_xy'][::-1,-1]]));delta=Z-H;pad=Polygon([Q[12,0],Q[12,-1],Q[-1,-1],Q[-1,0]]);outer=foot.buffer(1);check=dict(approach_length_m=3,flat_pad_length_m=4,flat_pad_width_m=6,flat_pad_area_m2=pad.area,flat_z_m=flat,entry_width_m=5,entry_residual_m=float(np.max(abs(Z[0]-old_z))),flatness_m=float(np.ptp(Z[st>=3])),max_triangle_long_pct=float(100*np.max(abs(g@d))),max_triangle_cross_pct=float(100*np.max(abs(g@normal))),max_abs_height_change_m=float(np.max(abs(delta))),max_cut_m=float(max(0,-delta.min())),max_fill_m=float(max(0,delta.max())),outside_terrain_m2=foot.difference(domain).area,prior_trail_overlap_m2=foot.intersection(prev).area,root_reserve_outside_terrain_m2=outer.difference(domain).area,triangles=len(f),samples=Z.size,center_xy=(end+5*d).tolist())
assert check['entry_residual_m']<1e-8 and check['flatness_m']<1e-8 and check['outside_terrain_m2']<1e-8 and check['prior_trail_overlap_m2']<1e-8 and check['max_triangle_long_pct']<=15 and check['max_triangle_cross_pct']<=10
np.savez_compressed(O/'forest_endpoint_design_v04.npz',station=st,xy=Q,source_z=H,design_z=Z,landing_survey=np.array([[*a['candidate_xy'],a['ground_z_m'],a['max_full_width_long_pct'],a['max_full_width_cross_pct'],a['staging_max_grade_pct']] for a in landings]));assert np.array_equal(np.load(O/'forest_endpoint_design_v04.npz')['design_z'],Z);assert list(map(sha,[P,V]))==expected
# Draw measured shoreline and rejected direct route, plus plan/profile of provisional pad.
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(15,5.4),layout='constrained');v,f=grids[0];ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=4,vmax=25,shading='gouraud');v,f=grids[1];ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=4,vmax=25,shading='gouraud');
for p in sh.get_parts(water):ax.fill(*p.exterior.xy,c='#5288a8')
ax.scatter(*np.array([a['candidate_xy'] for a in eligible]).T,s=4,c='#eab879');ax.plot(*np.array([near['candidate_xy'],start]).T,'--',c='#9d302d',label='Direct route rejected');ax.scatter(*start,c='white',edgecolor='k');ax.set(xlim=(325,390),ylim=(-250,-147),aspect='equal',title='A | East-bank survey',xlabel='X (m)',ylabel='Y (m)');ax.legend(fontsize=8)
v,f=grids[3];bx.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=26,vmax=30,shading='gouraud');bx.fill(*foot.exterior.xy,c='#d4b986',alpha=.8);bx.fill(*pad.exterior.xy,c='#d9d4c4',label='Flat area (not altar)');bx.plot(*outer.exterior.xy,'--',c='#725d42',label='1 m reserve');bx.plot(*road[-40:,4].T,c='#203c2e',lw=2,label='V03 trail');bx.set(xlim=(680,701),ylim=(-501,-480),aspect='equal',title='B | Endpoint design candidate',xlabel='X (m)',ylabel='Y (m)');bx.legend(fontsize=7)
cx.plot(st,H[:,10],'--',label='Measured terrain');cx.plot(st,Z[:,10],label='Design');cx.fill_between(st,Z.min(1),Z.max(1),alpha=.2);cx.axvspan(3,7,color='#c7c3b5',alpha=.25);cx.set(title='C | Entrance and flat area',xlabel='Station (m)',ylabel='Z (m)');cx.legend(fontsize=8);cx.grid(alpha=.2);fig.suptitle('MOSS FOREST V04 | ENDPOINT SURVEY — DESIGN ONLY');fig.savefig(O/'forest_endpoints_v04.png',dpi=150);plt.close(fig)
q=dict(status='DIRECT_LANDING_HOLD_PAD_DESIGN_CANDIDATE',inputs_sha256=expected,landing=dict(survey_count=len(landings),dry_full_width_count=len(eligible),direct_pass_count=len(direct_pass),best_normalized_direct=best,near_start=near,criteria='1m radius dry staging <=10%; full-width 2m direct route long<=15%, cross<=10%; finite survey only',all_candidates=landings),pad=check,limits=['No surveyed original terrain: river V01 reconstructed, forest V02 exact individual tiles. Water level is authored; no flow/swimming/landing dynamics. Direct failures do not prove absence of alternative routes.','Pad is 4x6m provisional flat area, not altar design or placement approval. Outer side tie-ins, drainage, collision and canopy unresolved. No new native geometry, CG comparison or independent D4.'],inputs_unchanged=True,outputs={p.name:sha(p) for p in [Path(__file__),O/'forest_endpoint_design_v04.npz',O/'forest_endpoints_v04.png']});(O/'forest_endpoints_v04.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k!='landing'},indent=2));print('landing', {k:v for k,v in q['landing'].items() if k!='all_candidates'})
