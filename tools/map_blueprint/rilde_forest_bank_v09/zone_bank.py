"""Read-only design zoning of V08 river-bank path; not native terrain or wall design."""
import hashlib,json,sys
from pathlib import Path
import numpy as np, trimesh, shapely as sh
from shapely.geometry import Polygon
from shapely.ops import unary_union
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;P,V,A=map(Path,sys.argv[1:4]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','79a119dd6afbab374f775a47f48ad215559ea160d2f9f0527c3fee799cc4fe23','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653'];assert list(map(sha,[P,V,A]))==expected
S=trimesh.load(P,force='scene',process=False);R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def mesh(name):
 t,g=S.graph[name];m=S.geometry[g];return trimesh.transform_points(m.vertices,t)@R,m.faces
polys=[];planes=[]
for name in ['RIVER_CORRIDOR','MOSS_FOREST_A1']:
 v,f=mesh(name);t=v[f];nn=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (nn[:,2]>0).all();g=-nn[:,:2]/nn[:,2,None];polys.extend(sh.polygons(t[:,:,:2]));planes.extend(np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)])
polys=np.array(polys,dtype=object);planes=np.array(planes);tree=sh.STRtree(polys);domain=unary_union(polys);wv,wf=mesh('RIVER_WATER_CLIPPED');wet=unary_union(sh.polygons(wv[wf][:,:,:2]));B=np.load(V);C=np.load(A);s=B['station'];Q=B['xy'];H=B['source_z'];Z=B['design_z'];n=(Q[:,-1]-Q[:,0])/2;N=len(s);ds=np.diff(s)
road=Polygon(np.vstack([Q[:,0],Q[::-1,-1]]));forest=Polygon(np.vstack([C['left_xy'][:,-1],C['right_xy'][::-1,-1]]));assert road.is_valid and forest.is_valid
assert np.max(abs(Q[-1]-C['road_xy'][0]))<1e-8

def z(x):
 shape=x.shape[:-1];x=x.reshape(-1,2);a,b=tree.query(sh.points(x),predicate='intersects');o=np.full(len(x),np.nan);o[a]=(planes[b,:2]*x[a]).sum(1)+planes[b,2];return o.reshape(shape)
assert np.max(abs(z(Q)-H))<1e-8

def examine(sign,w,taper_end=True,wall=False):
 j=0 if sign==-1 else -1;edge=Q[:,j];width=np.full(N,w,dtype=float)
 if taper_end: width+=(1.5-w)*np.clip((s-s[-1]+8)/8,0,1)
 M=int(np.ceil(max(width)/.25))+1;u=np.linspace(0,1,M);xy=edge[:,None,:]+sign*width[:,None,None]*u[None,:,None]*n[:,None,:];base=z(xy);zz=base+(Z[:,j]-H[:,j])[:,None]*(1-u*u*(3-2*u));zz[:,0]=Z[:,j]
 # Both triangles per cell; preserve outward orientation (sign).
 v=np.dstack([xy,zz]);a=v[:-1,:-1];b=v[1:,:-1];c=v[1:,1:];d=v[:-1,1:];normal=np.stack([np.cross(b-a,c-a),np.cross(c-a,d-a)],axis=2);signed=normal[...,2]*sign
 with np.errstate(divide='ignore',invalid='ignore'):grade=np.linalg.norm(normal[...,:2]/normal[...,2,None],axis=-1)
 grades=np.max(np.where(np.isfinite(grade),grade,np.inf),axis=(1,2));folds=(signed<=1e-10).sum(axis=(1,2));finite=np.isfinite(base[:-1]).all(1)&np.isfinite(base[1:]).all(1)
 footprint=sh.polygons(np.stack([xy[:-1,0],xy[1:,0],xy[1:,-1],xy[:-1,-1]],axis=1));valid=sh.is_valid(footprint);inter=np.full((N-1,4),np.inf);ix=np.where(valid)[0];f=footprint[ix];inter[ix,0]=sh.area(sh.intersection(f,wet));inter[ix,1]=sh.area(sh.intersection(f,road));inter[ix,2]=sh.area(sh.intersection(f,forest));inter[ix,3]=sh.area(sh.difference(f,domain));geom=finite&valid&(folds==0)&(inter.max(1)<1e-8);good=geom&(grades<=.5+1e-10)
 # For retaining reservations only geometry is checked; no wall slope or structure claim.
 return dict(width=w,xy=xy,base=base,design=zz,footprint=footprint,good=good,geom=geom,grade=grades,folds=folds,overlap=inter,finite=finite)

widths=np.arange(.5,4.01,.25);results=[];plot=[];arrays={'station':s,'road_xy':Q,'road_z':Z}
for sign in [-1,1]:
 tests=[examine(sign,float(w)) for w in widths];G=np.array([a['good'] for a in tests]);any_good=G.any(0);best=max(tests,key=lambda a:(ds@a['good'],-a['width']));good=best['good'].copy()
 # Avoid isolated natural patches <2m: reserve them for transition design, not structural approval.
 def runs(mask):
  cuts=np.r_[0,np.flatnonzero(mask[1:]!=mask[:-1])+1,len(mask)];return [(int(a),int(b),bool(mask[a])) for a,b in zip(cuts[:-1],cuts[1:])]
 for a,b,k in runs(good):
  if k and s[b]-s[a]<2:good[a:b]=False
 # .4m strip on rejected segments is only a spatial reservation for possible retaining treatment.
 wall=examine(sign,.4,taper_end=False,wall=True);wall_ok=(~good)&wall['geom'];blocked=(~good)&(~wall['geom']);zone=np.where(good,1,np.where(wall_ok,2,3))
 fp=np.where(good,best['footprint'],wall['footprint']);ix=zone!=3;union=unary_union(fp[ix]);sumarea=float(sh.area(fp[ix]).sum());overlap=max(0.,sumarea-union.area);j=0 if sign==-1 else -1
 selected_grade=float(best['grade'][good].max()*100) if good.any() else None
 # Exposed height difference at road edge to existing ground and reserve outer edge, not foundation depth.
 height=np.maximum(abs(Z[:,j]-H[:,j]),abs(Z[:,j]-wall['base'][:,-1]));wall_height=np.maximum(height[:-1],height[1:]);selected_wall_height=float(wall_height[wall_ok].max()) if wall_ok.any() else None
 rec=dict(side=sign,side_label='river-facing at launch' if sign==-1 else 'hill-facing at launch',width_candidates_m=widths.tolist(),width_checks=len(tests)*(N-1),any_natural_width_length_m=float(ds@any_good),no_tested_natural_width_length_m=float(ds@(~any_good)),selected_nominal_shoulder_width_m=best['width'],natural_length_m=float(ds@good),retaining_reserve_length_m=float(ds@wall_ok),unresolved_length_m=float(ds@blocked),natural_max_grade_pct=selected_grade,reserve_max_measured_height_difference_m=selected_wall_height,selected_plan_area_m2=union.area,selected_plan_self_overlap_m2=overlap,selected_wet_overlap_m2=union.intersection(wet).area,selected_road_overlap_m2=union.intersection(road).area,selected_forest_overlap_m2=union.intersection(forest).area,selected_outside_m2=union.difference(domain).area,transition_count=int(np.count_nonzero(zone[1:]!=zone[:-1])),end_zone=int(zone[-1]),end_width_m=float(np.linalg.norm(best['xy'][-1,-1]-best['xy'][-1,0])),runs=[{'station_start_m':float(s[a]),'station_end_m':float(s[b]),'zone':int(zone[a])} for a,b in zip(np.r_[0,np.flatnonzero(zone[1:]!=zone[:-1])+1],np.r_[np.flatnonzero(zone[1:]!=zone[:-1])+1,len(zone)])],width_summary=[{'nominal_width_m':x['width'],'passing_length_m':float(ds@x['good']),'geometry_passing_length_m':float(ds@x['geom']),'folded_triangles':int(x['folds'].sum())} for x in tests]);results.append(rec);plot.append((sign,best,wall,zone,union,any_good));arrays.update({f'side_{sign}_zone':zone,f'side_{sign}_natural_xy':best['xy'],f'side_{sign}_natural_z':best['design'],f'side_{sign}_reserve_xy':wall['xy']});print(json.dumps({k:v for k,v in rec.items() if k not in ['runs','width_summary']},indent=2),flush=True)
assert list(map(sha,[P,V,A]))==expected
cross_overlap=plot[0][4].intersection(plot[1][4]).area
np.savez_compressed(O/'bank_zones_v09.npz',**arrays);a=np.load(O/'bank_zones_v09.npz');assert all(np.array_equal(a[k],v,equal_nan=True) for k,v in arrays.items())
from matplotlib.collections import PolyCollection
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(15,6),layout='constrained');colors={1:'#58956c',2:'#c69b51',3:'#b94c44'}
for p in sh.get_parts(wet):ax.fill(*p.exterior.xy,c='#648bac',alpha=.65)
ax.fill(*road.exterior.xy,c='#3c3933');ax.plot(*forest.exterior.xy,c='#658b68',lw=.8)
for sign,best,wall,zone,union,any_good in plot:
 for k in [1,2,3]:
  f=(best if k==1 else wall)['footprint'][zone==k];verts=[np.array(p.exterior.coords) for p in f if p.is_valid];ax.add_collection(PolyCollection(verts,facecolors=colors[k],edgecolors='none'))
 for k in [1,2,3]:
  ix=np.where(zone==k)[0];bx.barh(np.full(len(ix),sign),ds[ix],left=s[ix],height=.5,color=colors[k],align='center')
 cx.plot(s,Z[:,0 if sign==-1 else -1]-H[:,0 if sign==-1 else -1],label=f'Side {sign:+d}')
ax.set(xlim=(320,388),ylim=(-235,-145),aspect='equal',title='A | Plan: treatment reservation',xlabel='X (m)',ylabel='Y (m)');bx.set(title='B | Treatment by station',xlabel='Station (m)',yticks=[-1,1],yticklabels=['River side at launch','Hill side at launch']);from matplotlib.patches import Patch
bx.legend(handles=[Patch(color=colors[k],label=l) for k,l in [(1,'Natural shoulder'),(2,'Retaining reserve only'),(3,'Unresolved')]],fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.16));cx.axhline(0,color='gray',lw=.8);cx.set(title='C | Road-edge height difference',xlabel='Station (m)',ylabel='Design minus ground (m)');cx.legend();cx.grid(alpha=.2);fig.suptitle('MOSS FOREST V09 | HYBRID BANK TREATMENT ZONING — DESIGN ONLY');fig.savefig(O/'bank_zones_v09.png',dpi=150);plt.close(fig)
q=dict(status='HYBRID_TREATMENT_RESERVATION_NOT_ADOPTED',inputs_sha256=expected,station_intervals=N-1,length_m=float(s[-1]),sides=results,cross_side_plan_overlap_m2=cross_overlap,source_unchanged=True,npz_reopen_exact=True,zone_legend={'1':'sampled natural shoulder candidate','2':'dry spatial reservation for retaining treatment ONLY','3':'unresolved'},limits=['Natural grade checked on proposed triangles in individual station cells, not native terrain; width taper and whole candidate union checked, but mixed-width transitions and continuous mesh not designed.','Retaining reserve 0.4m is a spatial allowance, not a verified wall thickness, foundation or structure; no retaining geometry created.','50% slope limit and 2m minimum natural run are provisional artistic design choices. Tested widths do not exhaust possible solutions. No water-contact landing, independent D4, actual CG, Blender or runtime QA.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'bank_zones_v09.npz',O/'bank_zones_v09.png']});(O/'bank_zones_v09.json').write_text(json.dumps(q,indent=2)+'\n');print('cross overlap',cross_overlap)
