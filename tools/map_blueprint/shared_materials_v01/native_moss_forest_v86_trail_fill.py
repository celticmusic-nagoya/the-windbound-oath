"""V86 local trail-fill candidate; V85 global adjustment did not meet target.
Reuse exact V85 baseline renders and measured terrain. Add at most two fixed,
non-camera-following soft area fills. Preserve all existing geometry/materials
and lighting. No game performance claim or formal adoption.
"""
import bpy, sys, math, hashlib, json, struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from array import array
import numpy as np
src,out=map(Path,sys.argv[sys.argv.index('--')+1:][:2])
out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with open(p,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
LOCK='74211f23ab69bd8e518e1fd53c0a0a035bc20aa47126d51c6a283bacf2e5fc85'
assert sha(src)==LOCK and bpy.app.version[:3]==(5,3,0)
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene
EYE = Vector((78.17052459716797, -80.77701568603516, 29.82533073425293))
ALTAR = Vector((93.94316101074219, -93.07432556152344, 30.988130569458008))
A_, B_ = Vector((-205, 140)), Vector((90, -90))
RESERVED = [((67.536852, -72.486359), 11), ((45.876293, -75.886764), 8), ((49.408698, -58.352544), 10)]
FWD = (ALTAR - EYE).to_2d().normalized(); PERP = Vector((-FWD.y, FWD.x)); CENTER = (EYE.to_2d() + ALTAR.to_2d()) / 2
SIDE = Vector((.6148655745981655, .788631932636555))
CAM_ZONES = [EYE.to_2d(), EYE.to_2d() + SIDE * 8, EYE.to_2d() - FWD * 12, EYE.to_2d() + FWD * 10, ALTAR.to_2d() + PERP * 14]
C0 = ALTAR.to_2d(); FD = -FWD; FDP = Vector((-FD.y, FD.x))
REVIEW_EYES = [EYE.to_2d(), EYE.to_2d() + SIDE * 8, EYE.to_2d() - FWD * 12, EYE.to_2d() + FWD * 10, C0 + PERP * 14, C0 + FD * 10.5, C0 + FD * 10.5 + FDP * 3.5]
CAM_ZONES = CAM_ZONES + REVIEW_EYES[5:]
VIEW_CONES = [(e, C0) for e in REVIEW_EYES]
terrain = bpy.data.objects['A3 provisional reconstructed terrain']; ext = bpy.data.objects['V58_SCENIC_ONLY_terrain_extension']; far = bpy.data.objects['V77_SCENIC_ONLY_FAR_RELIEF']


def world_bvh(objs):
    verts = []; polys = []
    for o in objs:
        mw = o.matrix_world; base = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]; polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


GROUND = world_bvh([terrain, ext, far])


def ground(x, y):
    hit = GROUND.ray_cast(Vector((x, y, 300)), Vector((0, 0, -1)), 400)
    return hit[0].z if hit[0] else None


# ---------------------------------------------------------------- animal trail (shared by shader + placement)
U = (B_ - A_).normalized(); N_ = Vector((-U.y, U.x)); LEN = (B_ - A_).length


def meander(a):
    fade = max(0., min(1., (LEN - a) / 9.0))
    return (1.1 * math.sin(.23 * a) + .5 * math.sin(.61 * a + 1.3)) * fade


def trail_dist(p):
    w = p - A_; a = w.dot(U)
    if a > LEN:
        return (p - B_).length
    return abs(w.dot(N_) - meander(a))


def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length


def gap(p, trail_clear, tall=False):
    """Clearance from trail core, ruin, reserved circles, cameras (+ altar sight ray for tall items)."""
    g = [trail_dist(p) - trail_clear, (p - C0).length - 7.0] + [(p - Vector(c)).length - r for c, r in RESERVED]
    if tall:
        g += [(p - c).length - 3.5 for c in CAM_ZONES] + [seg_dist(p, Vector((65.4663, -80.2138)), C0) - 2.2]
        for c, t in VIEW_CONES:                                  # keep review sightlines readable (half-angle 22 deg)
            v = p - c; L_ = (t - c).length
            if 0 < v.dot((t - c).normalized()) < L_ + 2 and v.angle(t - c) < math.radians(22):
                g.append(-1.0)
    return min(g)





platform=bpy.data.objects['V82_FX_03_floor']
# Recover platform top from the actual emissive inlay, not a guessed world height.
rz=[(platform.matrix_world @ platform.data.vertices[i].co).z for p in platform.data.polygons if p.material_index==0 for i in p.vertices]
assert rz
T=sorted(rz)[len(rz)//2]-.006
def eye_at(p2, h=1.7):
    g = ground(p2.x, p2.y); return Vector((p2.x, p2.y, (g if g is not None else EYE.z - 1.7) + h))


a_tl = LEN - 9; tl = A_ + U * a_tl + N_ * meander(a_tl)
VIEWS = {
    'matched': (EYE, ALTAR, 22), 'lateral': (EYE + SIDE.to_3d() * 8, ALTAR, 22),
    'side': (eye_at(C0 + PERP * 14), ALTAR, 24),
    'player_eye': (eye_at(EYE.to_2d() - FWD * 12), eye_at(EYE.to_2d() + FWD * 14, 1.5), 28),
    'altar_approach': (eye_at(EYE.to_2d() + FWD * 10), ALTAR + Vector((0, 0, -.4)), 28),
    'altar_front': (eye_at(C0 + FD * 10.5, 1.6), Vector((C0.x, C0.y, T + 1.5)), 26),
    'altar_oblique': (Vector((*(C0 + FD * 10.5 + FDP * 3.5), T + 6.2)), Vector((C0.x, C0.y, T + .9)), 24),
    'trail_low': (eye_at(tl, 1.05), eye_at(A_ + U * (LEN - 1) + N_ * meander(LEN - 1), .6), 24),
    'look_up': (EYE, EYE + (FWD.to_3d() * .45 + Vector((0, 0, .9))), 16),
    'oblique_aerial': (CENTER.to_3d() + Vector((-48, 40, EYE.z + 52)), CENTER.to_3d() + Vector((0, 0, EYE.z - 2)), 26),
}



fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT'];assert fx.hide_render and fx.hide_viewport
def digest(mesh):
    a=array('f',[0])*(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',a)
    b=array('i',[0])*len(mesh.loops);mesh.loops.foreach_get('vertex_index',b)
    c=array('i',[0])*len(mesh.polygons);mesh.polygons.foreach_get('material_index',c)
    return hashlib.sha256(a.tobytes()+b.tobytes()+c.tobytes()).hexdigest()
def snapshot():
    cache={};result={}
    for o in scene.objects:
        if o.type!='MESH':continue
        if o.data.name not in cache:cache[o.data.name]=digest(o.data)
        result[o.name]=(cache[o.data.name],tuple(tuple(row) for row in o.matrix_world),o.hide_render,o.hide_viewport)
    return result



protected=snapshot()
slots={o.name:tuple(m.name if m else None for m in o.data.materials) for o in scene.objects if o.type=='MESH'}
bg=scene.world.node_tree.nodes['Background'];vol=scene.world.node_tree.nodes['V79_atmosphere']
strength=bg.inputs['Strength'].default_value;density=vol.inputs['Density'].default_value
assert strength>0 and density>0
exposure=scene.view_settings.exposure
fills=[bpy.data.objects[n] for n in ('V57_cool_ambient','V58_scenic_cool_fill')]
assert all(o.type=='LIGHT' for o in fills)
energies={o.name:o.data.energy for o in fills}
assert all(o.data.users==1 for o in fills)
import shutil
baseqa=json.loads((src.parent/'v85_light_qa.json').read_text())
assert baseqa['native_sha256']==LOCK and baseqa['screening']['selected'] is None
assert abs(strength-baseqa['baseline']['world_strength'])<1e-6
assert abs(density-baseqa['baseline']['density'])<1e-6
assert abs(exposure-baseqa['baseline']['exposure'])<1e-6
assert energies==baseqa['baseline']['fill_energy']
existing_lights={o.name:(o.data.energy,tuple(o.data.color),tuple(tuple(row) for row in o.matrix_world),o.hide_render,o.hide_viewport) for o in scene.objects if o.type=='LIGHT'}
qa={'candidate_only':True,'source_sha256':LOCK,'baseline_source_run':45956718656,'baseline':baseqa['baseline'],'views':{},'placements':[],'limits':['Fixed local soft fill, not camera-following light; provisional locations and powers','Scene ray hit test treats mesh cards as opaque; not a radiometric canopy transmission model','Screening thresholds provisional; visual G2 and game light budget G4 still required','Original geometry and materials unchanged']}
manifest={n.strip().removeprefix('./'):h for h,n in (line.split(None,1) for line in (src.parent/'SHA256SUMS').read_text().splitlines())}
for view in ('player_eye','altar_approach','altar_front'):
    n='v85_A_'+view+'.png'
    assert sha(src.parent/n)==manifest[n]
    shutil.copyfile(src.parent/n,out/('v86_A_'+view+'.png'))
    qa['views'][view]={'A':baseqa['views'][view]['A']}
def checkpoint():
    (out/'v86_light_qa.json').write_text(json.dumps(qa,indent=2))
    print('V86_CHECKPOINT',json.dumps(qa),flush=True)
cam=scene.camera
camera_state=(cam.matrix_world.copy(),cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end)
render_state=(scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath)
# Survey target ground between player camera and existing matching view.
# Candidate lights placed above actual terrain, not inside known solid geometry.
collection=bpy.data.collections.new('V86_TRAIL_SOFT_FILL_CANDIDATE')
scene.collection.children.link(collection)
deps=bpy.context.evaluated_depsgraph_get()
def visible_segment(start,end):
    d=end-start
    hit,loc,n,index,obj,matrix=scene.ray_cast(deps,start,d.normalized(),distance=d.length-.05)
    return (not hit, None if not hit else obj.name)
# F2: actual previous raycast hit four ferns at EYE. Do not bypass
# vegetation occlusion or lower the 3/5 threshold. Project to authored
# animal-trail centerline, search nearby longitudinal stations, permit one
# qualified fixture if a second cannot be found.
qa['placement_trials']=[]
def centerline(a):
    return A_+U*a+N_*meander(a)
def choose_fill(offset,occupied):
    nominal=EYE.to_2d()+FWD*offset
    station=(nominal-A_).dot(U)
    trials=[]
    for shift in (0,-2,2,-4,4):
        a=station+shift
        if not 0<a<LEN:continue
        target2=centerline(a)
        if any((target2-p).length<5 for p in occupied):continue
        gz=ground(target2.x,target2.y)
        if gz is None:continue
        target=Vector((target2.x,target2.y,gz+.25))
        for lateral in (-2.0,2.0,-3.5,3.5,0.0):
            for height in (4.0,5.5,3.0):
                p2=target2+N_*lateral;z=ground(p2.x,p2.y)
                if z is None:continue
                pos=Vector((p2.x,p2.y,z+height))
                checks=[]
                for advance,side in ((0,0),(-1.5,0),(1.5,0),(0,-.25),(0,.25)):
                    p=centerline(a+advance)+N_*side;g=ground(p.x,p.y)
                    if g is None:continue
                    checks.append(visible_segment(Vector((p.x,p.y,g+.35)),pos))
                if len(checks)!=5:continue
                score=sum(v[0] for v in checks)
                trials.append((score,-abs(shift),-abs(lateral),-abs(height-4),target,pos,checks,a))
    if not trials:
        qa['placement_trials'].append({'offset':offset,'status':'NO_TRIALS'});checkpoint();return None
    score,_,_,_,target,pos,checks,a=max(trials,key=lambda x:x[:4])
    qa['placement_trials'].append({'offset':offset,'station':a,'candidate_count':len(trials),'clear':score,'blocked_by':[name for clear,name in checks if not clear]})
    checkpoint()
    if score<3:return None
    return target,pos,score,checks
new=[];occupied=[]
for idx,offset in enumerate((-8.0,0.0)):
    result=choose_fill(offset,occupied)
    if result is None:continue
    target,pos,score,checks=result
    occupied.append(target.to_2d())
    light=bpy.data.lights.new('V86_trail_soft_%02d'%idx,'AREA')
    light.shape='DISK';light.size=4.5;light.color=(.86,.93,1.0);light.energy=0
    ob=bpy.data.objects.new(light.name,light);collection.objects.link(ob)
    ob.location=pos;ob.rotation_euler=(target-pos).to_track_quat('-Z','Y').to_euler()
    new.append(ob)
    qa['placements'].append({'object':ob.name,'target':list(target),'location':list(pos),'unblocked_ground_samples':score,'sample_count':len(checks),'blocked_by':[name for clear,name in checks if not clear],'size':4.5})
    checkpoint()
assert new,'no qualified trail fill; stop without lighting mutation'
qa['fixture_count']=len(new)
def setlight(power):
    for ob in new:ob.data.energy=power
    assert scene.view_settings.exposure==exposure and bg.inputs['Strength'].default_value==strength and vol.inputs['Density'].default_value==density
    assert all((o.data.energy,tuple(o.data.color),tuple(tuple(row) for row in o.matrix_world),o.hide_render,o.hide_viewport)==existing_lights[o.name] for o in scene.objects if o.name in existing_lights)
checkpoint()
def render(view,state):
    p,t,lens=VIEWS[view];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    file=out/('v86_'+state+'_'+view+'.png');scene.render.filepath=str(file.resolve());bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(str(file),check_existing=False);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im)
    y=a.reshape(-1,4)[:,:3]@np.array([.2126,.7152,.0722]);qa['views'].setdefault(view,{})[state]={'mean_luma':float(y.mean()),'p10':float(np.percentile(y,10)),'p95':float(np.percentile(y,95)),'dark_fraction_below_0_02':float((y<.02).mean())};checkpoint()
# Same cameras, sun, volumetrics, exposure, geometry and texture. Two conservative alternatives.
states={'A':0,'B':220,'C':480}
for state in ('B','C'):
    setlight(states[state])
    for view in ('player_eye','altar_approach','altar_front'):render(view,state)
def acceptable(state):
    a=qa['views']['player_eye']['A'];b=qa['views']['player_eye'][state]
    c=qa['views']['altar_front']['A'];d=qa['views']['altar_front'][state]
    return b['mean_luma']>=a['mean_luma']*1.12 and b['p10']>=a['p10'] and d['p95']<=c['p95']*1.15 and d['mean_luma']<=c['mean_luma']*1.15
winner=next((k for k in ('B','C') if acceptable(k)),None)
qa['screening']={'criteria':'player mean >=1.12x baseline, p10 nondecreasing; front mean/p95 <=1.15x baseline','selected':winner,'provisional':True}
checkpoint()
# Keep baseline if none qualifies; no unreviewed lighting candidate as default.
setlight(states[winner or 'A'])
if winner is None:
    for ob in new:
        light=ob.data;bpy.data.objects.remove(ob,do_unlink=True);bpy.data.lights.remove(light)
    bpy.data.collections.remove(collection)
qa['screening']['power_per_light']=states[winner or 'A']
assert snapshot()==protected and all(tuple(m.name if m else None for m in o.data.materials)==slots[o.name] for o in scene.objects if o.type=='MESH')
cam.matrix_world,cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end=camera_state
scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath=render_state
assert fx.hide_render and fx.hide_viewport
dest=out/'v86_trail_fill_candidate.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene
assert snapshot()==protected and bpy.data.collections['V82_RUNE_VFX_INDEPENDENT'].hide_render
assert all(tuple(m.name if m else None for m in o.data.materials)==slots[o.name] for o in scene.objects if o.type=='MESH')
qa.update({'native_sha256':sha(dest),'reopen_geometry_exact':True,'source_unchanged':sha(src)==LOCK});checkpoint()
assert qa['source_unchanged'];print('V86_LIGHT_DONE',json.dumps(qa))
