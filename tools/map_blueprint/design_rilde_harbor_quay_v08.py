import hashlib,json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent
P=Path(sys.argv[1]); Q=Path(sys.argv[2])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['4103b8cd1e974677bf2c7134622542ceefda78e43852fbd27d120c9b98cc5175','e9101ea9c35ac68d432a9449bba8c79b95da0456302a15d1c920e74ef2258470']
assert [sha(P),sha(Q)]==expected
G=json.loads(P.read_text())['geometry']; A=json.loads(Q.read_text())
apron=Polygon(G['apron_polygon_xy']); edge=np.array(G['quay_water_edge_xy']); quay=LineString(edge)
stairs=unary_union([Polygon(x['outline_xy']) for x in A['stairs']]); top=Polygon(A['top_landing_xy']); strip=Polygon(A['clear_strip_xy'])
road=np.array(A['road_cross_sections_s_offset_xyz'])[:,:,2:]; entry=road[-1,6,:2]
# Quay stations, local cross-shore offset into land. Exact along-face frame.
def local(i,s,d):
 a,b=edge[i:i+2];u=(b-a)/np.linalg.norm(b-a);n=np.array([u[1],-u[0]])
 if not apron.buffer(1e-8).covers(Point(a+.5*u+n)):n=-n
 return a+s*u+d*n

def rect(i,s0,s1,d0,d1):return Polygon([local(i,s0,d0),local(i,s1,d0),local(i,s1,d1),local(i,s0,d1)])
# Space for fish sorting/temporary crates; no enclosed warehouse or permanent blockage.
load=rect(0,8,16,2.8,4.8)
# Shore-side posts, keep stair opening and landing clear. No ropes deployed across navigation.
posts=[Point(local(0,s,.45)) for s in [3,19]]+[Point(local(2,s,.45)) for s in [3,13]]
post_shapes=[p.buffer(.15) for p in posts]
# Route from road to top landing, and along quay to northern handling area.
# Use interior of apron, avoid physical obstacles (stairs, posts, loaded zone).
free=apron.difference(unary_union([stairs,load,*post_shapes])); safe=free.buffer(-.6)
print('entry',entry,'top',top.centroid.coords[:], 'load',load.centroid.coords[:], 'safe',safe.geom_type)
for s in [1,3,5,8,12,16,19,21]:print('local',s,local(0,s,1.5),local(0,s,5.3))
print('entry safe',safe.covers(Point(entry)), 'top safe',safe.covers(top.centroid))
# Landing point is offset away from the stair lip; approach from the landward side.
a,b=edge[1:3];u=(b-a)/np.linalg.norm(b-a);target=np.array(top.centroid.coords[0])-.15*u
for name,points in [('stairs',[entry,local(1,1.5,3.7),target]),('handling',[entry,local(0,21,3),local(0,18,1.4),local(0,12,1.4)])]:
 l=LineString(points);print(name,points,'outside',l.buffer(.6,cap_style=1).difference(free).area,'length',l.length)
print('load outside',load.difference(apron).area, 'load road',load.intersection(Polygon(np.vstack([road[:,0,:2],road[::-1,-1,:2]]))).area,'load stairs',load.intersection(stairs.union(top).union(strip)).area)
paths={'STAIR_ACCESS':LineString([entry,local(1,1.5,3.7),target]),'HANDLING_ACCESS':LineString([entry,local(0,21,3),local(0,18,1.4),local(0,12,1.4)])}
roadfoot=Polygon(np.vstack([road[:,0,:2],road[::-1,-1,:2]]))
checks={'load_area_m2':load.area,'load_outside_apron_m2':load.difference(apron).area,'load_reserved_overlap_m2':load.intersection(stairs.union(top).union(strip).union(roadfoot)).area,'post_count':len(posts),'post_outside_apron_m2':sum(p.difference(apron).area for p in post_shapes),'post_reserved_overlap_m2':sum(p.intersection(stairs.union(top).union(strip).union(roadfoot).union(load)).area for p in post_shapes),'paths':{k:{'length_m':v.length,'outside_free_area_m2':v.buffer(.6).difference(free).area,'min_clearance_m':v.distance(free.boundary)} for k,v in paths.items()}}
assert checks['load_outside_apron_m2']<1e-8 and checks['load_reserved_overlap_m2']<1e-8 and checks['post_outside_apron_m2']<1e-8 and checks['post_reserved_overlap_m2']<1e-8
assert all(v['outside_free_area_m2']<1e-8 and v['min_clearance_m']>=.6-1e-8 for v in checks['paths'].values())
q={'status':'DESIGN_CANDIDATE_NOT_ADOPTED','source_sha256':expected,'frame':'provisional m; X east Y north Z up','loading_zone_xy':list(load.exterior.coords),'quay_posts':[{'id':f'MP-{i+1:02d}','xy':list(p.coords[0]),'radius_m':.15,'height_m':.8,'base_z_m':2} for i,p in enumerate(posts)],'walkway_width_m':1.2,'walkways':{k:list(v.coords) for k,v in paths.items()},'quay_section':{'apron_z_m':2,'toe_z_m':-2.2,'retained_height_m':4.2,'foundation_bottom_z_m':None,'foundation_width_m':None,'reason':'original ground and bearing not verified; no structural sizing'},'checks':checks,'limits':['Proposed game layout only; posts are reservation footprints, not verified mooring capacity. No mooring lines or actual berth anchors designed.','No actual ground, foundations, stair railing, hull boarding or collision proof.','D0-D3 partial, D4 NOT_RUN; G1 BLOCKED, G2-G4 NOT_RUN.']}
(O/'harbor_quay_v08.json').write_text(json.dumps(q,indent=2)+'\n')
fig,(ax,bx)=plt.subplots(1,2,figsize=(12,7),gridspec_kw={'width_ratios':[1.4,1]},layout='constrained')
def fill(ax,p,c,label):
 x,y=p.exterior.xy;ax.fill(x,y,color=c,edgecolor='#514c42',linewidth=.7,label=label)
ax.set_facecolor('#c6dbe3');coast=np.array([[-200,-165],[-170,-215],[-250,-265],[800,-265],[800,-165]]);fill(ax,Polygon(coast),'#e3e6d3','Land (schematic)');fill(ax,apron,'#d8c8ae','Quay apron');fill(ax,roadfoot,'#b6ab92','Village road');fill(ax,stairs,'#998a77','Stairs');fill(ax,top,'#b7a585','Top landing');fill(ax,strip,'#9bbaa8','Clear strip');fill(ax,load,'#ba8b51','Fish handling / crates')
for i,p in enumerate(post_shapes):fill(ax,p,'#333c40','Mooring post reserve' if i==0 else None)
for i,(k,v) in enumerate(paths.items()):
 fill(ax,v.buffer(.6),'#b1d5c4','1.2 m pedestrian route' if i==0 else None);ax.plot(*v.xy,c='#36735c',lw=1.2,ls='--')
for i,p in enumerate(posts):ax.annotate(f'MP-{i+1:02d}',p.coords[0],xytext=(-8,7),textcoords='offset points',fontsize=8)
ax.set(xlim=(-193,-160),ylim=(-230,-179),aspect='equal',title='A | Quay circulation and working area',xlabel='East X (m)',ylabel='North Y (m)');ax.legend(fontsize=7,loc='upper left',bbox_to_anchor=(0,-.15),ncol=2,frameon=False);ax.grid(alpha=.15)
bx.axhspan(-.8,.8,color='#a5c8d6',alpha=.6,label='Assumed tidal range');bx.plot([-7,0,0],[2,2,-2.2],c='#514c42',lw=3,label='Quay face design');bx.plot([0,6],[-2.2,-2.2],c='#997654',lw=2,label='Proposed bed');bx.axhspan(-4,-2.2,color='#ccc6bc',alpha=.3,hatch='//');bx.text(2,-3.15,'Foundation HOLD\nDepth / width unknown',ha='center',fontsize=10);bx.annotate('',xy=(-1,2),xytext=(-1,-2.2),arrowprops={'arrowstyle':'<->'});bx.text(-1.3,-.1,'4.2 m',ha='right');bx.set(xlim=(-7,7),ylim=(-4,3),title='B | Quay section: interface only',xlabel='Waterward offset (m)',ylabel='Z (m)');bx.legend(fontsize=8,loc='upper right');bx.grid(alpha=.18)
fig.suptitle('RILDE HARBOUR V08 | QUAY WORKING AREA — PROVISIONAL DESIGN',weight='bold');fig.savefig(O/'harbor_quay_v08.png',dpi=160);plt.close(fig)
assert [sha(P),sha(Q)]==expected
print(json.dumps(checks,indent=2))
