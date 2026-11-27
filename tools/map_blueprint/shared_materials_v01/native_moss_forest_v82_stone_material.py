"""V82-B: bounded material A/B on the verified dormant altar.
Reuse packed V81 rock photo maps, without new texture downloads or geometry changes.
Hypothesis: reduce excessive high-frequency normals and moss masking before any stone mesh rebuild.
A/B preview uses same camera/lighting, with rune VFX disabled. Not an art acceptance test.
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
LOCK='43cd20b42a4e4350cd00cb1dcccd08b436ecdf23bf497efb47dd0655fd9cdf27'
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



ruin=bpy.data.collections['V81_RUNE_SANCTUARY']
fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert fx.hide_render and fx.hide_viewport
platform=bpy.data.objects['V81_ruin_platform']
original=bpy.data.materials['V81_ruin_stone']
assert platform.data.materials[0]==original
def fingerprint():
    result={};cache={}
    for o in scene.objects:
        if o.type=='MESH':
            m=o.data
            if m.name not in cache:
                a=array('f',[0])*(len(m.vertices)*3);m.vertices.foreach_get('co',a)
                b=array('i',[0])*len(m.loops);m.loops.foreach_get('vertex_index',b)
                c=array('i',[0])*len(m.polygons);m.polygons.foreach_get('material_index',c)
                cache[m.name]=hashlib.sha256(a.tobytes()+b.tobytes()+c.tobytes()).hexdigest()
            result[o.name]=[cache[m.name],[list(row) for row in o.matrix_world],o.hide_render,o.hide_viewport]
    return result
protected=fingerprint()
material_slots={o.name:[m.name if m else None for m in o.data.materials] for o in scene.objects if o.type=='MESH'}
m=original.copy();m.name='V82B_pale_weathered_stone_candidate';nt=m.node_tree
def only(items,label):
    items=list(items);assert len(items)==1,(label,len(items));return items[0]
normal=only((n for n in nt.nodes if n.type=='NORMAL_MAP'),'normal')
assert abs(normal.inputs['Strength'].default_value-1.3)<.001
normal.inputs['Strength'].default_value=.55
# Identify base color mix and attenuation from actual links; preserve other paths.
bs=only((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),'principled')
mix=bs.inputs['Base Color'].links[0].from_node
assert mix.type=='MIX' and mix.data_type=='RGBA'
fac=mix.inputs['Factor'];assert len(fac.links)==1
mask=fac.links[0].from_socket
atten=nt.nodes.new('ShaderNodeMath');atten.name='V82B_moss_coverage_attenuation';atten.operation='MULTIPLY';atten.inputs[1].default_value=.45
nt.links.new(mask,atten.inputs[0]);nt.links.new(atten.outputs[0],fac)
# Share the attenuated coverage with the roughness blend; preserve microstructure map.
rough=bs.inputs['Roughness'].links[0].from_node
assert rough.type=='MIX' and rough.inputs['Factor'].links[0].from_socket==mask
nt.links.new(atten.outputs[0],rough.inputs['Factor'])
hs=only((n for n in nt.nodes if n.type=='HUE_SAT' and abs(n.inputs['Saturation'].default_value-.3)<.001),'stone saturation')
assert abs(hs.inputs['Value'].default_value-2)<.001
hs.inputs['Value'].default_value=2.35
ao=only((n for n in nt.nodes if n.type=='AMBIENT_OCCLUSION'),'AO')
ao_map=only((l.to_node for l in ao.outputs['AO'].links if l.to_node.type=='MAP_RANGE'),'AO map')
assert abs(ao_map.inputs['To Min'].default_value-.8)<.001
ao_map.inputs['To Min'].default_value=.95
# A/B only modifies the shared stone slots on four existing ruin meshes.
targets=[o for o in ruin.objects if o.type=='MESH' and any(x==original for x in o.data.materials)]
assert len(targets)==4,[o.name for o in targets]
assert all(o.data.users==1 for o in targets)
qa={'candidate_only':True,'source_sha256':LOCK,'changes':{'normal_strength':[1.3,.55],'moss_mask_multiplier':.45,'stone_hsv_value':[2,2.35],'ao_min':[.8,.95]},'target_objects':sorted(o.name for o in targets),'geometry_unchanged':None,'views':{},'limits':['Existing packed rock photo maps reused; ashlar alternative not acquired','No geometry or carved rune recess edits','Preview rendering only; material simplification on export not tested','D2 stone geometry remains open; G2/G4 not certified']}
cam=scene.camera
camera_state=(cam.matrix_world.copy(),cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end)
render_state=(scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath)
def render(name,state):
    p,t,lens=VIEWS[name];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    file=out/('v82b_'+state+'_'+name+'.png');scene.render.filepath=str(file.resolve());bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(str(file));a=np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4);bpy.data.images.remove(im)
    # Whole-frame luminance diagnostic only, not a stone-region acceptance score.
    y=a[:,:,:3]@np.array([.2126,.7152,.0722]);qa['views'].setdefault(name,{})[state]={'mean_luma':float(y.mean()),'p10_luma':float(np.percentile(y,10))}
for name in ('altar_front','altar_oblique','altar_approach'):render(name,'A')
for o in targets:
    for i,x in enumerate(o.data.materials):
        if x==original:o.data.materials[i]=m
assert fingerprint()==protected
for o in scene.objects:
    if o.type=='MESH' and o not in targets:assert [x.name if x else None for x in o.data.materials]==material_slots[o.name]
qa['geometry_unchanged']=True
cam.matrix_world,cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end=camera_state
scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath=render_state
assert sha(src)==LOCK and fx.hide_render
dest=out/'v82b_stone_candidate.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;cam=scene.camera;fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert fingerprint()==protected and fx.hide_render and fx.hide_viewport
qa['native_sha256']=sha(dest);qa['reopen_geometry_exact']=True
(out/'v82b_stone_qa.json').write_text(json.dumps(qa,indent=2))
for name in ('altar_front','altar_oblique','altar_approach'):render(name,'B')
qa['source_unchanged']=sha(src)==LOCK
(out/'v82b_stone_qa.json').write_text(json.dumps(qa,indent=2))
print('V82B_STONE_DONE',json.dumps(qa))
