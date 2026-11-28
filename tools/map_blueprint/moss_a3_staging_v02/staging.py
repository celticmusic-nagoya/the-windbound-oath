"""A3 spatial staging / camera design only. Run with 3 geometry files, V01 JSON and V01 script."""
import sys,hashlib,json
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
PTH=list(map(Path,sys.argv[1:6])); hashes=list(map(sha,PTH))
assert hashes==['e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','c3d6c314cc23f50012840a2b81414f46ea638ac6f7917f3ae557394e434d3f32','3ab29ffddcaabce5a997e1ce65bd6c55e0f3df2d8e73f00049fb9c6474e9f65e','b4adf3246b4f9c298f4017050966e332af859caf29038468c3e305d726ce78cf']
# reuse verified source terrain functions, not prior candidate-generation code
src=PTH[4].read_text();exec(src[:src.index('# Arena: circular')]);O=Path(__file__).resolve().parent
q=json.loads(PTH[3].read_text());a=q['selected_arena'];c=np.array(a['center_xy']);hero=np.array(q['selected_hero']['center_xy']);altar=np.array(q['pad']['center_xy']);rad=a['radius_m'];arena=Point(c).buffer(rad,quad_segs=64);root=Point(hero).buffer(5,quad_segs=64)
# stage only, no battle mechanics: conservative 0.65m capsules, 1.8/2.4m heights; Lou is not a combatant.
# 24 rotations, 3 actor spacings. Straight path swept footprints between initial and alternate position.
choices=[]
for deg in range(0,360,15):
 theta=np.radians(deg);u=np.array([np.cos(theta),np.sin(theta)]);w=np.array([-u[1],u[0]])
 for gap in [2.,3.,4.]:
  pts=np.array([c-2*u,c-2*u+gap*w,c+2*u]);go=np.array([pts[0]+1.5*u,pts[1]+1.5*w,pts[2]+1.5*u]);polys=[LineString([p,g]).buffer(.65,quad_segs=32) for p,g in zip(pts,go)];m=[metric(p) for p in polys];clear=min(polys[i].distance(polys[j]) for i in range(3) for j in range(i));outside=sum(p.difference(arena).area for p in polys);gmax=max(x['grade_pct'] for x in m);rel=max(x['relief_m'] for x in m);ok=outside<1e-8 and clear>=.5 and gmax<=15 and rel<=.5
  choices.append(dict(angle=deg,spacing=gap,positions=pts.tolist(),end_positions=go.tolist(),minimum_swept_clearance_m=clear,outside_m2=outside,max_grade_pct=gmax,max_relief_m=rel,pass_screen=bool(ok)))
valid=[x for x in choices if x['pass_screen']];assert valid
sel=min(valid,key=lambda x:(x['max_relief_m'],-x['minimum_swept_clearance_m']));pts=np.array(sel['positions']);pz=height(pts);actor_heights=np.array([1.8,1.8,2.4]);target=np.c_[pts,pz+actor_heights*.5];look=np.mean(target,axis=0)
# Camera screen with 16:9 and 60deg vertical FOV. Terrain samples <=0.2m; no asset occlusion except root cylinder reserve, height assumed 12m.
def ray(eye,t):
 L=np.linalg.norm(t[:2]-eye[:2]);ss=np.linspace(0,1,max(2,int(np.ceil(L/.2))+1))[1:-1];xyz=eye+(t-eye)*ss[:,None];z=height(xyz[:,:2]);return float(np.min(xyz[:,2]-z)) if len(ss) else 1e6
# framing tests bounding boxes around each proxy. orthonormal view basis and padded image box (90% of screen)
def frame(eye,aim,points):
 fwd=aim-eye;fwd/=np.linalg.norm(fwd);right=np.cross(fwd,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,fwd);d=points-eye;dep=d@fwd
 if min(dep)<=0:return 1e6,1e6
 t=np.tan(np.radians(30));return float(np.max(abs(d@right/dep/(t*16/9)))),float(np.max(abs(d@up/dep/t)))
proxies=np.array([np.r_[p+[dx,dy],z+dz] for p,z,h in zip(pts,pz,actor_heights) for dx in [-.65,.65] for dy in [-.65,.65] for dz in [0,h]])
cams=[]
for deg in range(0,360,15):
 u=np.array([np.cos(np.radians(deg)),np.sin(np.radians(deg))]);
 for dist in [8,12,16]:
  xy=c+dist*u
  if not domain.contains(Point(xy)) or root.buffer(.5).contains(Point(xy)):continue
  for h in [1.65,3.,5.]:
   eye=np.r_[xy,height(xy)[0]+h];xx,yy=frame(eye,look,proxies);rays=[ray(eye,t) for t in target];root_hits=sum(LineString([eye[:2],t[:2]]).intersects(root) for t in target);ok=xx<=.9 and yy<=.9 and min(rays)>=.1 and root_hits==0
   cams.append(dict(angle=deg,range_m=dist,height_m=h,eye=eye.tolist(),aim=look.tolist(),frame_x=xx,frame_y=yy,min_ray_clearance_m=min(rays),root_hits=root_hits,pass_screen=bool(ok)))
vc=[x for x in cams if x['pass_screen']];assert vc
cam=min(vc,key=lambda x:(abs(x['frame_y']-.65),abs(x['height_m']-3)))
# Travel viewpoints from barrier to trail end; hero root trunk point at 1/6/12m, altar placeholder 1.5m above reserved flat pad (not asset dimensions)
route_idx=np.where((st>=q['selected_barrier']['station_m']-5)&(st<=st[-1]))[0][::8];views=[]
for k in route_idx:
 eye=np.r_[r[k],rz[k]+1.65];ht=np.r_[hero,height(hero)[0]];at=np.r_[altar,q['pad']['flat_z_m']];rv=[ray(eye,ht+[0,0,h]) for h in [1,6,12]];av=ray(eye,at+[0,0,1.5]);views.append(dict(station_m=float(st[k]),eye=eye.tolist(),hero_clearance_m=rv,altar_clearance_m=av,hero_visible=[x>=.1 for x in rv],altar_visible=bool(av>=.1)))
# barrier bypass: source terrain around gate. 2m cross-section only 5m gate reserve, sample continuous transverse ground outside gate to +/-15m. Not nav proof.
bc=np.array(q['selected_barrier']['center_xy']);off=np.arange(-15,15.01,.25);bxy=bc+off[:,None]*n;zz=height(bxy);sl=abs(np.diff(zz)/.25)*100
# plot plan plus selected camera frame, two sightlines and barrier cross-section.
fig,axs=plt.subplots(2,2,figsize=(13,10),layout='constrained');ax,bx,cx,dx=axs.flat
im=ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud');ax.plot(*r[st>=340].T,c='white',lw=1.6);ax.fill(*arena.exterior.xy,color='#b76b40',alpha=.25);ax.fill(*root.exterior.xy,color='#386940',alpha=.5);ax.scatter(*altar,c='#e3bd47',marker='D',label='Altar approach');eye=np.array(cam['eye']);ax.scatter(*eye[:2],marker='^',c='black',label='Camera');
for i,(p,g) in enumerate(zip(pts,sel['end_positions'])):
 ax.scatter(*p,label=['Aidan','Fiona','Raider'][i],s=40);ax.plot(*np.array([p,g]).T,c='black');ax.plot(*np.array([eye[:2],p]).T,ls=':',c='black')
ax.set(xlim=(632,700),ylim=(-500,-444),aspect='equal',title='A | Arena staging and camera',xlabel='X east (m)',ylabel='Y north (m)');ax.legend(fontsize=8);fig.colorbar(im,ax=ax,shrink=.7,label='Z (m)')
# projected camera proxy bounds
fw=look-eye;fw/=np.linalg.norm(fw);right=np.cross(fw,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,fw);t=np.tan(np.radians(30));
for i,pr in enumerate(np.split(proxies,3)):
 d0=pr-eye;xx=d0@right/(d0@fw)/(t*16/9);yy=d0@up/(d0@fw)/t;bx.add_patch(plt.Rectangle((xx.min(),yy.min()),xx.ptp() if hasattr(xx,'ptp') and False else np.ptp(xx),np.ptp(yy),fill=False,lw=2));bx.text(xx.mean(),yy.mean(),['Aidan','Fiona','Raider'][i],ha='center',fontsize=9)
bx.set(xlim=(-1,1),ylim=(-1,1),aspect=9/16,title='B | Camera projection (proxy bounds only)',xlabel='Normalized screen X',ylabel='Normalized screen Y');bx.grid(alpha=.2)
for i,h in enumerate([1,6,12]):cx.plot([x['station_m'] for x in views],[x['hero_clearance_m'][i] for x in views],label=f'Tree +{h}m');cx.plot([x['station_m'] for x in views],[x['altar_clearance_m'] for x in views],label='Altar +1.5m') if i==0 else None
cx.axhline(.1,c='black',ls=':');cx.set(title='C | Terrain-only line-of-sight clearance',xlabel='Trail station (m)',ylabel='Min clearance (m)');cx.legend(fontsize=8);cx.grid(alpha=.2)
dx.plot(off,zz,c='#405c42');dx.axvspan(-2.5,2.5,color='#7e59b5',alpha=.25,label='5m gate reservation');dx.set(title='D | Barrier transverse profile — bypass risk',xlabel='Offset (m)',ylabel='Z (m)');dx.grid(alpha=.2);dx.legend(fontsize=8);fig.suptitle('MOSS FOREST A3  |  V02  •  STAGING DESIGN / NOT GAME IMPLEMENTATION');fig.savefig(O/'staging_v02.png',dpi=150);plt.close(fig)
# record all candidates, explicit assumptions and limitations
out=dict(status='STAGING_SCREEN_ONLY',inputs_sha256=hashes,assumptions=dict(actor_radius_m=.65,actor_heights_m=actor_heights.tolist(),swept_distance_m=1.5,vertical_fov_deg=60,aspect='16:9',image_margin_fraction=.1,ray_step_max_m=.2,ray_clearance_min_m=.1,tree_target_heights_m=[1,6,12],altar_target_height_m=1.5),staging_count=len(choices),staging_pass=len(valid),selected_staging=sel,camera_count=len(cams),camera_pass=len(vc),selected_camera=cam,travel_view_count=len(views),hero_visible_counts=[sum(x['hero_visible'][i] for x in views) for i in range(3)],altar_visible_count=sum(x['altar_visible'] for x in views),barrier_cross_section=dict(offset_m=off.tolist(),z_m=zz.tolist(),outside_gate_max_sampled_grade_pct=float(max(sl[(abs(off[:-1])>=2.5)&(abs(off[1:])>=2.5)])),note='single transverse sample only; no navigation proof or barrier bypass prevention'),choices=choices,cameras=cams,views=views,inputs_unchanged=list(map(sha,PTH))==hashes,limits=['All actor, camera and landmark dimensions assumed; no actual assets, gameplay movement or animation tests. No actual battle or event implementation. Ray checks sampled against reconstructed terrain, no continuous visibility or full scene occlusion. Hero root reserve used as conservative planar exclusion for battle cameras only. Altar visibility before acquisition is not a narrative authorization. No D4 or native production.'])
(O/'qa.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['choices','cameras','views','barrier_cross_section']},indent=2))
