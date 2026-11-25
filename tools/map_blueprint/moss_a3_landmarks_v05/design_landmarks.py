"""A3 original authored landmark design targets, not surveyed dimensions or native mesh.
Run: python design_landmarks.py A3.glb shoulders.npz endpoint.npz V01.json V01.py V04_contract.json V02_staging.json
"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=list(map(Path,sys.argv[1:8])); expected=['e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','c3d6c314cc23f50012840a2b81414f46ea638ac6f7917f3ae557394e434d3f32','3ab29ffddcaabce5a997e1ce65bd6c55e0f3df2d8e73f00049fb9c6474e9f65e','b4adf3246b4f9c298f4017050966e332af859caf29038468c3e305d726ce78cf','4d2c308774f3c972c803cd8f74eb006c38dedb81ad45af34479bb612c4f07780','86a82dcda10d0fa2fd192d5690ae2d80c1696b6044a65580926e1ba89eb5e644'];assert list(map(sha,paths))==expected
# use verified terrain sampler and polygon metrics, not earlier design generation
src=paths[4].read_text(); allpaths=paths.copy(); allhashes=expected.copy();exec(src[:src.index('# Arena: circular')]);paths=allpaths;expected=allhashes;O=Path(__file__).resolve().parent
from shapely.geometry import shape
from shapely.affinity import scale, translate
from matplotlib.patches import Ellipse, Rectangle
q=json.loads(paths[3].read_text());gate=json.loads(paths[5].read_text());stage=json.loads(paths[6].read_text());hc=np.array(q['selected_hero']['center_xy']);hz=float(height(hc)[0]);ac=np.array(q['selected_arena']['center_xy']);arena=Point(ac).buffer(10,quad_segs=64);hr=Point(hc).buffer(5,quad_segs=64)
features=[(shape(x['footprint']),x['ground']['z_range_m'][1]+x['height_reserve_m']) for x in gate['features']]
# Art-directed trunk axes and taper targets. Local X/Y = world axes; Z above ground at hero origin.
trunk=np.array([[0,0,-.3,1.35],[0,0,.65,1.18],[-.25,.16,2.4,.85],[-.55,.25,4.8,.65],[-.32,.6,7.3,.46],[.3,.8,9.7,.28],[.1,1.05,12.8,.06]])
# Each main limb starts exactly on the trunk axis at an existing knot, with independent branch direction and taper.
limbs=[[[*trunk[2,:3],.40],[-1.3,-.6,3.9,.34],[-2.7,-2.0,5.9,.20],[-4.9,-2.8,8.1,.045]],[[*trunk[3,:3],.39],[.8,-.6,6.1,.30],[2.6,-2.0,8.2,.17],[4.5,-3.1,9.8,.045]],[[*trunk[3,:3],.36],[-1.4,1.5,6.5,.25],[-3.2,3.0,8.6,.14],[-4.8,3.9,10.1,.04]],[[*trunk[4,:3],.31],[1.3,1.4,8.3,.24],[3.1,3.1,10.1,.13],[4.6,4.0,11.2,.035]],[[*trunk[4,:3],.27],[-2,.1,9.2,.18],[-3.7,-.5,11.5,.09],[-4.5,-.6,12.3,.03]],[[*trunk[5,:3],.18],[.7,1.6,11.0,.14],[.8,2.5,13.1,.08],[.4,3.1,14.1,.03]]]
# Asymmetric canopy clusters, ellipsoid axis radii; reserved volume, not final foliage.
crown=np.array([[-4.9,-2.8,8.8,3.0,2.5,2.3],[4.5,-3.1,10.4,2.9,2.4,2.4],[-4.8,3.9,10.8,3.0,2.7,2.6],[4.6,4.,11.8,2.7,2.7,2.5],[-4.5,-.6,12.8,2.7,2.2,2.5],[.4,3.1,14.0,3.3,2.8,2.5],[.1,-.8,11.7,3.3,2.7,2.8]])
# roots: terrain-following centerline with tapered radius; end buried 0.15m, starts inside trunk.
roots=[];rpolys=[]
for i,(deg,L,bend) in enumerate([(13,4.15,.28),(62,3.9,-.32),(111,4.35,.24),(163,4.2,-.25),(216,4.1,.36),(265,4.45,-.28),(316,3.8,.3)]):
 a=np.radians(deg);u=np.array([np.cos(a),np.sin(a)]);w=np.array([-u[1],u[0]]);t=np.array([.15,.95,2.1,L]);xy=hc+t[:,None]*u+np.array([0,bend*.3,bend,bend*.65])[:,None]*w;rr=np.array([.57,.46,.25,.075]);base=height(xy);zz=base+np.array([.65,.23,.02,-.15]);p=sh.union_all([LineString(xy[j:j+2]).buffer(max(rr[j:j+2]),quad_segs=32) for j in range(3)]);rpolys.append(p);roots.append(dict(id=f'ROOT-{i+1:02}',nodes_xyz=np.c_[xy,zz].tolist(),radii_m=rr.tolist(),ground_z_m=base.tolist(),tip_top_below_ground_m=float(base[-1]-zz[-1]-rr[-1]),footprint_area_m2=p.area))
rootp=sh.union_all(rpolys+[Point(hc).buffer(1.35,quad_segs=64)]);cp=sh.union_all([translate(scale(Point(0,0).buffer(1,quad_segs=64),x[3],x[4]),*(hc+x[:2])) for x in crown]);protected=sh.union_all([road,pad,arena]+[x[0] for x in features]);
# altar coordinates on existing 4m x 6m flat pad: long axis d, transverse n.
flat=Polygon(np.r_[B['xy'][12:,0],B['xy'][12:,-1][::-1]]);pc=np.array(q['pad']['center_xy']);pz=q['pad']['flat_z_m'];
def rect(c,halfL,halfW):return Polygon([c+a*d+b*n for a,b in [(-halfL,-halfW),(halfL,-halfW),(halfL,halfW),(-halfL,halfW)]])
# choose altar far half, reserve 1.5m depth interaction, side bypass 1.8m on each side.
altars=[]
for off in [.8,.9,1.0,1.1]:
 for length in [1.0,1.2,1.4]:
  for width in [2.0,2.4,2.8]:
   center=pc+off*d;body=rect(center,length/2,width/2);inter=rect(center-(length/2+.85)*d,.75,1.15);gap=body.distance(inter);outside=body.union(inter).difference(flat).area;side=(6-width)/2;edge=body.distance(flat.boundary);ok=outside<1e-8 and edge>=.25-1e-8 and gap>=.10-1e-8 and side>=1.5;altars.append(dict(offset_m=off,depth_m=length,width_m=width,center_xy=center.tolist(),body_outside_flat_m2=body.difference(flat).area,interaction_outside_flat_m2=inter.difference(flat).area,body_edge_clearance_m=edge,interaction_gap_m=gap,side_width_m=side,pass_screen=bool(ok)))
valid=[a for a in altars if a['pass_screen']];assert valid;al=min(valid,key=lambda a:(abs(a['width_m']-2.4)+abs(a['depth_m']-1.2),-a['body_edge_clearance_m']));alc=np.array(al['center_xy']);body=rect(alc,al['depth_m']/2,al['width_m']/2);inter=rect(alc-(al['depth_m']/2+.85)*d,.75,1.15)
# surface layers and closed cavity reserve (not visible sword, no authored magic mechanism)
levels=[{'id':'PLINTH','z_min_m':0,'z_max_m':.22,'depth_m':al['depth_m'],'width_m':al['width_m']},{'id':'STONE_BODY','z_min_m':.22,'z_max_m':1.02,'depth_m':al['depth_m']-.18,'width_m':al['width_m']-.30},{'id':'CAPSTONE','z_min_m':1.02,'z_max_m':1.24,'depth_m':al['depth_m']-.04,'width_m':al['width_m']-.08}];
# ray screen: actual terrain plus conservative extruded gate/roots and canopy ellipsoids (0.1m samples). Do not conflate visible altar stone with concealed sword.
root_top=max(max(np.array(x['nodes_xyz'])[:,2]+np.array(x['radii_m'])) for x in roots);gate_obs=features;treeobs=gate_obs+[(rootp,root_top)];
def clear(eye,target,obs,canopy=False):
  N=max(2,int(np.ceil(np.linalg.norm(target-eye)/.1)));ts=np.linspace(0,1,N+1)[1:-1];pts=eye+(target-eye)*ts[:,None];g=height(pts[:,:2]);ground=float(np.min(pts[:,2]-g));hits=[]
  for i,(p,top) in enumerate(obs):
   if np.any(sh.intersects_xy(p,pts[:,0],pts[:,1])&(pts[:,2]<=top)):hits.append(i)
  ch=[]
  if canopy:
   loc=pts-np.r_[hc,hz];ch=[i for i,x in enumerate(crown) if np.any(np.sum(((loc-x[:3])/x[3:])**2,axis=1)<=1)]
  return dict(terrain_clearance_m=ground,obstacle_hits=hits,canopy_hits=ch,clear=bool(ground>=.1 and not hits and not ch))
views=[]
for x in stage['views']:
 eye=np.array(x['eye']); # hero target at trunk midheight, gate features only (own tree not occluder for own silhouette)
 views.append(dict(station_m=x['station_m'],hero=clear(eye,np.r_[hc,hz+4.8],gate_obs),altar=clear(eye,np.r_[alc,pz+1.12],treeobs,True)))
# battle camera sightline against the new root/canopy/gate reserves
cam=stage['selected_camera'];eye=np.array(cam['eye']);actors=np.array(stage['selected_staging']['positions']);targets=np.c_[actors,height(actors)+np.array([.9,.9,1.2])];battle=[clear(eye,x,treeobs,True) for x in targets]
# analytic footprint support and plan/section sheet
out=dict(status='AUTHORING_TARGETS_ONLY',inputs_sha256=expected,frame='world m X east Y north Z up; tree local z relative to source ground; altar local along route d / transverse n',hero=dict(origin_xyz=[*hc.tolist(),hz],trunk_knots_xyz_radius_m=trunk.tolist(),limb_knots_xyz_radius_m=limbs,crown_ellipsoids_xyz_radii_m=crown.tolist(),roots=roots,height_m=float(max(crown[:,2]+crown[:,5])),crown_xy_bounds_m=list(cp.bounds),root_outside_reserve_m2=rootp.difference(hr).area,root_protected_overlap_m2=rootp.intersection(protected).area,crown_protected_overlap_m2=cp.intersection(protected).area,crown_road_clearance_m=cp.distance(road),crown_arena_clearance_m=cp.distance(arena),root_ground=metric(rootp),root_tip_buried_count=sum(x['tip_top_below_ground_m']>=.075-1e-8 for x in roots)),altar=dict(selected=al,all_candidates=altars,pass_count=len(valid),flat_z_m=pz,flat_footprint=list(flat.exterior.coords),axis_d=d.tolist(),axis_n=n.tolist(),body_footprint=list(body.exterior.coords),interaction_footprint=list(inter.exterior.coords),body_ground=metric(body),interaction_ground=metric(inter),levels=levels,cavity='Closed opaque volume reserve only; no sword geometry or reward logic; actual cavity size pending weapon source.'),views=views,battle_camera=battle,limits=['Authored design targets, not canon dimensions or actual tree/altar meshes; official CG unavailable. Crown ellipse approximations and conservative root footprints, no branch junction mesh or wind deformation validation. Terrain/cylinder/ellipsoid sight tests sampled; no actual camera or asset visibility, no independent D4. Altar shape and materials provisional; no visible sword before event. No gameplay or source edits.'])
fig,axs=plt.subplots(2,3,figsize=(17,10),layout='constrained');ax,bx,cx,dx,ex,fx=axs.flat
# plan, three-dimensional shape orthographic construction lines, altar details
ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud');ax.plot(*r[st>=345].T,c='white',lw=2);ax.plot(*arena.exterior.xy,c='#9b573b');ax.plot(*hr.exterior.xy,c='#23583c',ls='--');ax.fill(*rootp.exterior.xy,c='#67462e',alpha=.8);ax.plot(*cp.exterior.xy,c='#265b37',lw=2);ax.fill(*body.exterior.xy,c='#b9aa91');ax.fill(*inter.exterior.xy,c='#d2c65f',alpha=.8);ax.set(xlim=(631,700),ylim=(-500,-446),aspect='equal',title='A | World placement / protection',xlabel='East (m)',ylabel='North (m)')
for a,k,label in [(bx,0,'B | Ancient tree — east elevation'),(cx,1,'C | Ancient tree — north elevation')]:
 for x in crown:a.add_patch(Ellipse((x[k],x[2]),2*x[3+k],2*x[5],facecolor='#78975e',edgecolor='#48643d',alpha=.24))
 for l in [trunk]+[np.array(l) for l in limbs]:
  for j in range(len(l)-1):a.plot(l[j:j+2,k],l[j:j+2,2],c='#61452e',lw=2+4*l[j,3],solid_capstyle='round')
 for ro in roots:
  z=np.array(ro['nodes_xyz'])-np.r_[hc,hz];a.plot(z[:,k],z[:,2],c='#856243',lw=2)
 a.axhline(0,c='grey',ls='--');a.set(xlim=(-9,9),ylim=(-.7,17.5),aspect='equal',title=label,xlabel='Local horizontal (m)',ylabel='Height (m)');a.grid(alpha=.15)
for p,col,label in [(flat,'#e4dece','Flat pad'),(body,'#777164','Altar body'),(inter,'#d2c65f','Interaction reserve')]:
 xy=np.array(p.exterior.coords)-pc;uv=np.c_[xy@d,xy@n];dx.fill(*uv.T,c=col,alpha=.8,label=label);dx.plot(*uv.T,c='#444444',lw=.8)
dx.set(aspect='equal',xlim=(-2.5,2.5),ylim=(-3.5,3.5),title='D | Altar plan — 4 × 6 m pad',xlabel='Along trail (m)',ylabel='Across trail (m)');dx.legend(fontsize=8,loc='lower left');dx.grid(alpha=.2)
for a,key,title in [(ex,'width_m','E | Altar front elevation'),(fx,'depth_m','F | Altar side elevation')]:
 for i,l in enumerate(levels):a.add_patch(Rectangle((-l[key]/2,l['z_min_m']),l[key],l['z_max_m']-l['z_min_m'],facecolor=['#8b8578','#aaa291','#c0b8a2'][i],edgecolor='#565149'))
 a.axhline(0,c='grey',ls='--');a.set(aspect='equal',xlim=(-1.65,1.65),ylim=(-.2,1.65),title=title,xlabel='Width / depth (m)',ylabel='Height (m)');a.grid(alpha=.2)
fig.suptitle('MOSS FOREST A3 | V05 • LANDMARK CONSTRUCTION TARGETS / NOT NATIVE ASSETS',fontsize=16);fig.savefig(O/'landmarks_v05.png',dpi=150);plt.close(fig)
out['inputs_unchanged']=list(map(sha,paths))==expected;assert out['inputs_unchanged'];out['outputs']={p.name:sha(p) for p in [Path(__file__),O/'landmarks_v05.png']};(O/'qa.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'hero':{k:v for k,v in out['hero'].items() if k not in ['trunk_knots_xyz_radius_m','limb_knots_xyz_radius_m','crown_ellipsoids_xyz_radii_m','roots']},'altar':{k:v for k,v in out['altar'].items() if k not in ['all_candidates','flat_footprint','body_footprint','interaction_footprint']},'views':[sum(x[k]['clear'] for x in views) for k in ['hero','altar']], 'battle':battle},indent=2))
