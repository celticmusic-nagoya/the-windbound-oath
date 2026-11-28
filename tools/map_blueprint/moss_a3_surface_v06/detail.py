import hashlib,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import LineString,box
from shapely.ops import unary_union
P=Path(sys.argv[1]); O=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='cfa58995b99bfb84f44a44f8268521e61a036cece630b6a4d2ff5905425ce7fa';assert sha(P)==expected
q=json.loads(P.read_text()); h=q['hero']; a=q['altar']; trunk=np.array(h['trunk_knots_xyz_radius_m']); limbs=[np.array(x) for x in h['limb_knots_xyz_radius_m']]; roots=[np.c_[np.array(x['nodes_xyz'])-np.array(h['origin_xyz']),x['radii_m']] for x in h['roots']]
# Design-only axial profiles: grooves always inward from V05 circular envelopes.
def section(r,t,phase):
    depth=min(.085,.12*r); w=.65*(.5+.5*np.cos(13*t+.65*np.sin(3*t+phase)+phase))**5+.35*(.5+.5*np.cos(7*t-phase))**3
    return r-depth*w
angles=np.linspace(0,2*np.pi,721); profiles=[]
for k,l in [('TRUNK',trunk)]+[(f'LIMB-{i+1:02}',x) for i,x in enumerate(limbs)]+[(f'ROOT-{i+1:02}',x) for i,x in enumerate(roots)]:
    for i,(x,y,z,r) in enumerate(l):
        rr=section(r,angles,z*.37+i*.13); assert np.all(rr<=r+1e-12) and np.all(rr>0)
        profiles.append(dict(id=f'{k}-K{i:02}',center_m=[x,y,z],envelope_radius_m=r,depth_limit_m=min(.085,.12*r),sampled_max_inset_m=float(r-rr.min()),sampled_min_wall_radius_m=float(rr.min()),angular_samples=len(angles)))
# Altar front: original decorative interlace-like incised paired wave, no canon rune or glyph. Front body width 2.1, height .8.
body=next(x for x in a['levels'] if x['id']=='STONE_BODY'); W=body['width_m']; low=body['z_min_m']; high=body['z_max_m']; panel=box(-.82,.36,.82,.88)
x=np.linspace(-.72,.72,361); wave=.105*np.sin(2*np.pi*(x+.72)/.48); lines=[LineString(np.c_[x,.62+wave]),LineString(np.c_[x,.62-wave])]; stroke=.018; groove=unary_union([l.buffer(stroke/2,quad_segs=16) for l in lines]); assert groove.difference(panel).area<1e-12
# Alternate strand over/under is visual draft only; union at crossings, no false interlace claim.
# Deterministic chipped-edge locations, deliberately keep within external box; dimensions are maximum insets, not executed geometry.
chips=[dict(id=f'CHIP-{i+1:02}',layer='CAPSTONE',edge=edge,along_m=s,length_m=L,inset_m=d,vertical_m=v) for i,(edge,s,L,d,v) in enumerate([('front',-.81,.13,.028,.035),('front',.57,.21,.034,.045),('back',-.22,.16,.022,.028),('left',.23,.12,.025,.032),('right',-.18,.10,.020,.026)])]
assert all(c['inset_m']<=.04 and c['vertical_m']<=.05 for c in chips)
materials=[dict(id='BARK',source='https://polyhaven.com/a/jolcham_oak_bark_01',license='CC0 per provider, bytes not acquired',maps=['basecolor','normal','roughness'],roughness_target=[.72,.94],tile_scale_m=[1.5,1.5]),dict(id='STONE',source='https://polyhaven.com/a/rock_01',license='CC0 per provider, bytes not acquired',maps=['basecolor','normal','roughness'],roughness_target=[.65,.92],tile_scale_m=[1,1]),dict(id='MOSS_STONE',source='https://polyhaven.com/a/mossy_rock',license='CC0 per provider, bytes not acquired',maps=['basecolor','normal','roughness'],roughness_target=[.76,.98],tile_scale_m=[1,1])]
# Authored material mask policy: no geometry displacement in game shader, use normal map; no reward glyph or sword reveal.
qout=dict(status='DETAIL_AUTHORING_TARGETS_NOT_D4',input_sha256=expected,frame=q['frame'],tree_profiles=profiles,tree_profile_formula='r(theta)=r-min(0.085,0.12*r)*(0.65*(0.5+0.5*cos(13*theta+0.65*sin(3*theta+phase)+phase))^5+0.35*(0.5+0.5*cos(7*theta-phase))^3)',profile_phase='0.37*local_z+0.13*knot_index',altar=dict(body_width_m=W,body_z_m=[low,high],panel_bounds_m=list(panel.bounds),groove_centerlines=[list(l.coords) for l in lines],groove_width_m=stroke,groove_depth_m=.008,groove_area_m2=groove.area,panel_area_m2=panel.area,groove_panel_clearance_m=groove.distance(panel.boundary),groove_outside_panel_m2=groove.difference(panel).area,chip_targets=chips,ornament='original paired flowing line motif, no semantic rune; crossing treatment unresolved',concealment='opaque closed body; actual sword volume unknown, no weapon geometry'),materials=materials,material_policy={'license_url':'https://polyhaven.com/license','normal_only_runtime':True,'moss':'shade-side roots and sheltered stone recesses; keep interaction top mostly bare','textures':'candidate 2K hero material sets; benchmark actual mobile compressed format before acceptance','basecolor':'neutral brown-grey bark, cool grey stone, muted olive moss; preserve readable silhouette'},qa={'section_count':len(profiles),'sampled_radius_outside_envelope':0,'min_sampled_radius_m':min(p['sampled_min_wall_radius_m'] for p in profiles),'max_sampled_inset_m':max(p['sampled_max_inset_m'] for p in profiles),'groove_outside_panel_m2':0,'source_unchanged':sha(P)==expected},limits=['Numerical section targets only, not continuous tube surface, branch union, root ground mesh or sculpture. Groove intersections not resolved into woven ornament. Material license page checked, no texture bytes or maps verified. Tile scales and roughness authored targets. Official CG unavailable; D4/G1–G4 not passed.'])
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained');ax,bx,cx,dx=axs.flat
for idx,col in [(0,'#805c3e'),(2,'#647f56'),(4,'#455f76')]:
 r=trunk[idx,3]; rr=section(r,angles,trunk[idx,2]*.37+idx*.13); ax.plot(r*np.cos(angles),r*np.sin(angles),ls='--',color=col,alpha=.5);ax.plot(rr*np.cos(angles),rr*np.sin(angles),c=col,label=f'z={trunk[idx,2]:.2f} m')
ax.set(aspect='equal',title='A | Inward-only bark section targets',xlabel='Local X (m)',ylabel='Local Y (m)');ax.legend();ax.grid(alpha=.2)
for ro in roots:
 t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(ro[:,:3],axis=0),axis=1))];bx.plot(t,ro[:,3],marker='o',lw=1.2)
bx.set(title='B | Seven root taper profiles',xlabel='Centerline distance (m)',ylabel='Envelope radius (m)');bx.grid(alpha=.2)
for i,l in enumerate(a['levels']):cx.add_patch(Rectangle((-l['width_m']/2,l['z_min_m']),l['width_m'],l['z_max_m']-l['z_min_m'],facecolor=['#7f7e72','#a9a497','#c0bcb0'][i],edgecolor='#47483e'))
cx.plot(*panel.exterior.xy,c='#4f594c',ls='--');
for g in lines:cx.plot(*g.xy,c='#454c40',lw=2)
cx.set(aspect='equal',xlim=(-1.4,1.4),ylim=(-.12,1.42),title='C | Altar front • incised ornament target',xlabel='Width (m)',ylabel='Height (m)');cx.grid(alpha=.12)
for i,(n,c) in enumerate([('BARK / shaded fissures','#65523f'),('STONE / cool grey','#96978a'),('MOSS / sheltered recesses','#67764a')]):dx.add_patch(Rectangle((.05,.73-i*.27),.25,.18,facecolor=c));dx.text(.35,.82-i*.27,n,va='center',fontsize=11)
dx.set(xlim=(0,1),ylim=(0,1),title='D | Authored palette (not source texture samples)');dx.axis('off');fig.suptitle('MOSS FOREST A3 • V06 DETAIL AUTHORING TARGETS / NOT NATIVE ASSETS',fontsize=14);fig.savefig(O/'detail_v06.png',dpi=150);plt.close(fig)
qout['outputs']={p.name:sha(p) for p in [Path(__file__),O/'detail_v06.png']};(O/'qa.json').write_text(json.dumps(qout,indent=2)+'\n');print(json.dumps(qout['qa'],indent=2)); print(qout['altar']['groove_panel_clearance_m'],qout['altar']['groove_area_m2'])
