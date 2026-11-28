"""Read-only east-bank reachability upper bound on exact recovered geometry; no terrain edit."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent; P,V=map(Path,sys.argv[1:3]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','720f3a1598f266b2e0b4671feae76fce1b91ef852924960183c0c7b1ad246f16'];assert [sha(P),sha(V)]==expected
S=trimesh.load(P,force='scene',process=False);R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
def mesh(name):
 t,g=S.graph[name];m=S.geometry[g];return trimesh.transform_points(m.vertices,t)@R,m.faces
# Entire river tile and A1 (not an arbitrary cropped bank window).
polys=[];bad=[];grids=[];bound=np.hypot(.15,.10)
for name in ['RIVER_CORRIDOR','MOSS_FOREST_A1']:
 v,f=mesh(name);t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=np.linalg.norm(n[:,:2]/n[:,2,None],axis=1);q=sh.polygons(t[:,:,:2]);polys.extend(q);bad.extend(q[g>bound+1e-10]);grids.append((v,f))
land=unary_union(polys);steep=unary_union(bad);wv,wf=mesh('RIVER_WATER_CLIPPED');wet=unary_union(sh.polygons(wv[wf][:,:,:2]));dry=land.difference(wet);safe=dry.difference(steep);start=Point(380,-230)
# Necessary upper bound: every feasible 2m wide route must lie inside safe buffered inward by 1m. No direction restriction here, so this is optimistic.
results=[];v04=json.loads(V.read_text());pts=sh.points([x['candidate_xy'] for x in v04['landing']['all_candidates']]);assert len(pts)==156
for width in [0,2]:
 space=safe if width==0 else safe.buffer(-width/2,quad_segs=32);parts=[p for p in sh.get_parts(space) if p.geom_type=='Polygon'];hits=[p for p in parts if p.covers(start)];assert len(hits)==1;reachable=hits[0];inside=sh.covers(reachable,pts);results.append(dict(width_m=width,components=len(parts),reachable_area_m2=reachable.area,reachable_candidates=int(inside.sum()),min_candidate_distance_m=float(sh.distance(reachable,pts).min()),water_distance_m=reachable.distance(wet)))
# A candidate near the water must be re-designed; independent check of staging slopes across all existing V04 samples.
assert results[0]['reachable_candidates']==0 and results[1]['reachable_candidates']==0
assert [sha(P),sha(V)]==expected
q=dict(status='EXISTING_BANK_CONTINUOUS_ROUTE_REJECTED_WITHIN_TEST_DOMAIN',inputs_sha256=expected,domain_meshes=['RIVER_CORRIDOR','MOSS_FOREST_A1'],long_limit_pct=15,cross_limit_pct=10,necessary_scalar_grade_limit_pct=100*bound,source_triangle_count=len(polys),too_steep_triangle_count=len(bad),wet_area_m2=wet.area,results=results,staging_min_max_grade_pct=min(x['staging_max_grade_pct'] for x in v04['landing']['all_candidates']),candidate_count=len(pts),source_unchanged=True,limits=['Optimistic geometric connectivity, not directional navigation proof. Width=0 is an upper-bound diagnostic; routes outside the two-tile domain are not tested. River water is authored, not hydrological measurement.','No actual terrain change; original bank landing, story transition, new geometry and D4 unresolved.'])
fig,ax=plt.subplots(figsize=(8.5,9),layout='constrained');
for v,f in grids:ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',vmin=3,vmax=25,shading='gouraud',alpha=.75)
for p in sh.get_parts(steep):
 if p.geom_type=='Polygon':ax.fill(*p.exterior.xy,c='#a23e32',alpha=.8)
for p in sh.get_parts(wet):
 if p.geom_type=='Polygon':ax.fill(*p.exterior.xy,c='#5682a3')
for p in sh.get_parts(reachable):ax.plot(*p.exterior.xy,c='#124b32',lw=2)
ax.scatter(sh.get_x(pts),sh.get_y(pts),s=6,c='#ffd36c',edgecolors='none',label='156 V04 landing candidates');ax.scatter(*start.coords[0],c='white',edgecolor='k',s=60,label='V03 trail entrance');ax.set(xlim=(290,415),ylim=(-252,-98),aspect='equal',xlabel='East X (m)',ylabel='North Y (m)',title='MOSS FOREST V05 | Bank reachability upper bound\nRed: grade > 18.03% / Green: reachable 2m center domain');ax.legend(loc='upper right',fontsize=8);fig.savefig(O/'bank_reachability_v05.png',dpi=150);plt.close(fig)
q['outputs']={p.name:sha(p) for p in [Path(__file__),O/'bank_reachability_v05.png']};(O/'bank_reachability_v05.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
