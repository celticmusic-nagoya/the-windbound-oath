"""V12 design-only planar partition and sampled height contract, no native geometry."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import shapely as sh
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent
paths=list(map(Path,sys.argv[1:]))
expected=['6b937509815cd82b35ed6513ed7546c59bf13c3be97993203c52c3803c5e334e','1a866ca1770c8a2a480b6000596b6b5f98319473b703128963238df62979b7fb','4103b8cd1e974677bf2c7134622542ceefda78e43852fbd27d120c9b98cc5175','e9101ea9c35ac68d432a9449bba8c79b95da0456302a15d1c920e74ef2258470','7a6b48bdcf9ed6a116a332a5c3a4c24f825931084e2ba1f6373e2f48979fa2f4']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert list(map(sha,paths))==expected
A=np.load(paths[0])[:,:,2:];T=np.load(paths[1]);assert np.array_equal(A,T['road_xyz'])
G=json.loads(paths[2].read_text())['geometry'];B=json.loads(paths[3].read_text());Q=json.loads(paths[4].read_text())
edge=np.vstack([A[:,0],A[-1,1:],A[-2::-1,-1],A[0,-2:0:-1],A[:1,0]])
road=Polygon(edge[:,:2]);apron=Polygon(G['apron_polygon_xy']);assert road.is_valid and apron.is_valid
# Nanometre XY snap only for partition predicates, original road coordinates retained.
R=sh.set_precision(road,1e-9);P=sh.set_precision(apron,1e-9);rem=P.difference(R);over=P.intersection(R);seam=R.boundary.intersection(P)
assert rem.geom_type=='Polygon' and seam.geom_type=='LineString'
# Test exact partition against same snapped operands; no coincident face overlay.
assert rem.intersection(R).area<1e-10 and abs(rem.area+over.area-P.area)<1e-7
coords=np.asarray(seam.coords);start=edge[:-1,:2];vec=edge[1:,:2]-start;den=np.sum(vec*vec,axis=1);assert np.min(den)>0
# Restrict nearest-boundary interpolation to road segments adjacent to the apron.
sel=np.linalg.norm(start-[-170,-205],axis=1)<12
start,vec,den,z0,dz=start[sel],vec[sel],den[sel],edge[:-1,2][sel],np.diff(edge[:,2])[sel]
def road_boundary(points):
 p=np.asarray(points);delta=p[:,None,:]-start;u=np.clip(np.sum(delta*vec,axis=2)/den,0,1);ds=np.sum((delta-u[:,:,None]*vec)**2,axis=2);i=ds.argmin(axis=1);k=np.arange(len(p));return np.sqrt(ds[k,i]),z0[i]+u[k,i]*dz[i]
# The shared boundary is an exact linear interpolation of existing road edges.
# For the apron side use distance fade; 0.75m agrees with excluded V11 apron constraint zone.
W=.75
def height(points):
 dist,z=road_boundary(points);t=np.clip(dist/W,0,1);return 2+(z-2)*(1-t*t*(3-2*t))
ss=np.array([seam.interpolate(d).coords[0] for d in np.linspace(0,seam.length,491)])
d,zz=road_boundary(ss);res=np.max(abs(height(ss)-zz));assert d.max()<2e-9 and res<1e-9
zone=rem.intersection(R.buffer(W));reserve=unary_union([Polygon(x['outline_xy']) for x in B['stairs']]+[Polygon(B['top_landing_xy']),Polygon(B['clear_strip_xy']),Polygon(Q['loading_zone_xy'])]+[Point(x['xy']).buffer(x['radius_m']) for x in Q['quay_posts']]);assert zone.intersection(reserve).area<1e-9
# Sample adjacent horizontal, vertical and diagonal raster points on apron remainder.
x0,y0,x1,y1=zone.bounds;x=np.arange(x0-.1,x1+.1,.025);y=np.arange(y0-.1,y1+.1,.025);X,Y=np.meshgrid(x,y);xy=np.stack([X,Y],-1);mask=sh.covers(rem,sh.points(xy));H=np.full(X.shape,np.nan);H[mask]=height(xy[mask]);grades=[]
for i,j in [(1,0),(0,1),(1,1),(1,-1)]:
 a=H[:len(y)-i, max(0,-j):len(x)-max(j,0)];b=H[i:,max(0,j):len(x)-max(-j,0)];g=np.abs(a-b)/(.025*np.hypot(i,j))*100;grades.extend(g[np.isfinite(g)].tolist())
# Boundary of quay footprint must be reconciled to surrounding raster separately.
outer=P.boundary.intersection(zone);outer_pts=[]
for line in sh.get_parts(outer):
 if line.geom_type=='LineString':outer_pts.extend([line.interpolate(t).coords[0] for t in np.linspace(0,line.length,max(2,int(np.ceil(line.length/.025))+1))])
outer_dev=float(max(abs(height(np.asarray(outer_pts))-2))) if outer_pts else 0
q={'status':'DESIGN_PARTITION_AND_SAMPLED_TRANSITION_NOT_ADOPTED','input_sha256':expected,'coordinate_frame':'provisional metres X east Y north Z up','method':{'road_priority':True,'partition_precision_m':1e-9,'transition_width_m':W,'height_rule':'2+(z_nearest_road_boundary-2)*(1-smoothstep(clamp(distance/0.75,0,1)))','native_edit':False},'checks':{'apron_before_m2':apron.area,'overlap_before_m2':over.area,'apron_remaining_m2':rem.area,'overlap_after_m2':rem.intersection(R).area,'partition_area_error_m2':abs(rem.area+over.area-P.area),'shared_seam_length_m':seam.length,'seam_samples':len(ss),'seam_height_residual_m':float(res),'seam_xy_snap_residual_m':float(d.max()),'max_seam_deviation_from_flat_m':float(max(abs(zz-2))),'transition_area_m2':zone.area,'reserved_overlap_m2':zone.intersection(reserve).area,'apron_grid_samples':int(mask.sum()),'grade_samples':len(grades),'max_sampled_grade_pct':max(grades),'max_apron_outer_boundary_height_deviation_m':outer_dev,'source_unchanged':list(map(sha,paths))==expected},'apron_remaining_xy':list(rem.exterior.coords),'shared_seam_xyz':np.column_stack([coords,road_boundary(coords)[1]]).tolist(),'gates':{'D0':'PARTIAL','D1':'PARTIAL','D2':'PARTIAL','D3':'HOLD_OUTER_TERRAIN_AND_D4','D4':'NOT_RUN','G1':'BLOCKED','G2':'NOT_RUN','G3':'NOT_RUN_NATIVE','G4':'NOT_RUN'},'limits':['Planar partition and sampled height function only; no conforming 3D triangulation or weld. Nearest-edge height is sampled, continuous gradient not certified.','Outer terrain still needs a matching boundary, actual terrain and approved CG missing. No independent QA.']}
assert q['checks']['max_sampled_grade_pct']<15 and q['checks']['source_unchanged']
fig,(a,b)=plt.subplots(1,2,figsize=(12,6),layout='constrained');a.set_facecolor('#eaf0f1');a.fill(*P.exterior.xy,color='#d2c2a7',label='Original apron');a.fill(*R.exterior.xy,color='#b09b7c',label='Preserved road');a.fill(*zone.exterior.xy,color='#6caa99',alpha=.9,label='Transition zone');a.plot(*seam.xy,color='#254f4e',lw=2,label='Shared boundary');a.fill(*over.exterior.xy,color='#a86e55',alpha=.45,label='Old overlap (road priority)');
for poly in sh.get_parts(reserve):
 if poly.geom_type=='Polygon':a.fill(*poly.exterior.xy,color='#74726b',alpha=.5)
a.set(xlim=(-177,-166),ylim=(-212,-199),aspect='equal',title='A | Partition and protected equipment',xlabel='X east (m)',ylabel='Y north (m)');a.grid(alpha=.2);a.legend(fontsize=8,loc='upper left');im=b.pcolormesh(X,Y,(H-2)*1000,cmap='viridis',shading='auto');b.plot(*seam.xy,color='#d34d34',lw=1.5);b.set(aspect='equal',title='B | Apron transition offset from +2 m',xlabel='X east (m)',ylabel='Y north (m)');fig.colorbar(im,ax=b,label='Height offset (mm)',shrink=.65);fig.suptitle('RILDE HARBOUR V12 | ROAD–QUAY INTERFACE — DESIGN ONLY',weight='bold');fig.savefig(O/'harbor_transition_v12.png',dpi=150);plt.close(fig)
q['outputs']={'script_sha256':sha(Path(__file__)),'png_sha256':sha(O/'harbor_transition_v12.png')};(O/'harbor_transition_v12.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q['checks'],indent=2))
