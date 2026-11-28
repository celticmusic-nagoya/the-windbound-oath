"""V83 sanctuary integration candidate: F3 floor + E stone + C ivy.
Append only verified ivy object from exact source. Refine stone and leaf color.
Maintain default-off VFX and existing provisional placement; no game integration.
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
LOCK='d764cf090d789616762c77ea47f4b706df1cdf3012b83ec02c08c7935ec8ac94'
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
ivy=bpy.data.objects['V81_ruin_ivy']
assert fx.hide_render and fx.hide_viewport and len(fx.objects)==3
assert len(ivy.data.polygons)==342
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

old=snapshot()
slots={o.name:tuple(m.name if m else None for m in o.data.materials) for o in scene.objects if o.type=='MESH'}
source_ivy=out.parent/'v83-ivy'/'v82c_ivy_candidate.blend'
assert sha(source_ivy)=='82b5373f041082b7a8473b602432cf510b449723b93e02b149e98d8594577ba6'
# Capture before edits, then append only the validated candidate object.
cam=scene.camera
camera_state=(cam.matrix_world.copy(),cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end)
render_state=(scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath)
VIEWS['ivy_detail']=(Vector((*(C0+FD*4.0+FDP*1.4),T+2.1)),Vector((*(C0-FD*5.0),T+2.0)),43)
qa={'candidate_only':True,'source_sha256':LOCK,'ivy_source_sha256':sha(source_ivy),'views':{},'limits':['Provisional artistic tuning, not a G2 PASS','Nearest-face signed distance is a penetration screening heuristic, not solid containment proof','No official placement, no collision/traversal/device test','Native layered stone shader may simplify in GLB; export visual parity unverified']}
def checkpoint():
    (out/'v83_qa.json').write_text(json.dumps(qa,indent=2))
def render(name,state):
    p,t,lens=VIEWS[name];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    file=out/('v83_'+state+'_'+name+'.png');scene.render.filepath=str(file.resolve());bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(str(file),check_existing=False);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im)
    y=a.reshape(-1,4)[:,:3]@np.array([.2126,.7152,.0722]);qa['views'].setdefault(name,{})[state]={'mean_luma':float(y.mean())};checkpoint()
for view in ('altar_front','altar_oblique','ivy_detail'):render(view,'A')
with bpy.data.libraries.load(str(source_ivy.resolve()),link=False) as (data_from,data_to):
    assert 'V82C_ivy_lobed_leaf_study' in data_from.objects
    data_to.objects=['V82C_ivy_lobed_leaf_study']
obj=data_to.objects[0];assert obj is not None and obj.type=='MESH'
ruin.objects.link(obj)
assert digest(obj.data)=='6aa6d715cd775cc7a43faf63c054e4251d2b2e3f7d2518c28112611a91ac2ce8'
obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)==8428
assert len(obj.data.materials)==6
# Preserve C geometry; adjust only the five per-leaf materials.
leaf_colors=[]
for i in range(5):
    mt=obj.data.materials[i];assert mt.name.startswith('V82C_ivy_leaf_')
    bs=mt.node_tree.nodes['Principled BSDF'];a=list(bs.inputs['Base Color'].default_value)
    b=[a[0]*.60,a[1]*.65,a[2]*.66,1.0];bs.inputs['Base Color'].default_value=b
    bs.inputs['Subsurface Weight'].default_value=.045
    leaf_colors.append({'slot':i,'before':a,'after':b})
# Measure possible contact issues, do not silently reposition leaves.
stones=[bpy.data.objects[n] for n in ('V81_ruin_platform','V81_ruin_back','V81_ruin_posts')]
wall=world_bvh(stones);distances=[]
for v in obj.data.vertices:
    p=obj.matrix_world@v.co;hit,n,idx,d=wall.find_nearest(p)
    if hit is not None:distances.append(float((p-hit).dot(n)))
qa['ivy']={'geometry_exact':True,'triangles':8428,'leaf_colors':leaf_colors,'signed_nearest_face_samples':len(distances),'potential_inside_below_minus_0_005':sum(d<-.005 for d in distances),'min_signed_distance':min(distances) if distances else None}
# Reduce the overly bright stone and excessive normal micro-joint contrast.
original=bpy.data.materials['V82E_tileable_stone_candidate']
targets=[o for o in ruin.objects if o.type=='MESH' and original in list(o.data.materials)]
assert len(targets)==4 and all(o.data.users==1 for o in targets)
stone=original.copy();stone.name='V83_weathered_stone_candidate'
nt=stone.node_tree
normal=[n for n in nt.nodes if n.type=='NORMAL_MAP'];assert len(normal)==1 and abs(normal[0].inputs['Strength'].default_value-.55)<.001
normal[0].inputs['Strength'].default_value=.30
hs=[n for n in nt.nodes if n.type=='HUE_SAT' and abs(n.inputs['Saturation'].default_value-.3)<.001];assert len(hs)==1 and abs(hs[0].inputs['Value'].default_value-2.35)<.001
hs[0].inputs['Value'].default_value=1.72
for o in targets:
    for i,m in enumerate(o.data.materials):
        if m==original:o.data.materials[i]=stone
qa['stone']={'normal_strength':[.55,.30],'stone_hsv_value':[2.35,1.72],'targets':[o.name for o in targets]}
ivy.hide_render=True;ivy.hide_viewport=True;obj.hide_render=False;obj.hide_viewport=False
bpy.context.view_layer.update()
after=snapshot()
assert all(after[k]==v for k,v in old.items() if k!=ivy.name)
assert after[ivy.name][:2]==old[ivy.name][:2] and after[ivy.name][2:]==(True,True)
assert after[obj.name][0]=='6aa6d715cd775cc7a43faf63c054e4251d2b2e3f7d2518c28112611a91ac2ce8'
for o in scene.objects:
    if o.type=='MESH' and o.name in slots and o not in targets:assert tuple(m.name if m else None for m in o.data.materials)==slots[o.name]
checkpoint()
# Save editable native default-off BEFORE active render.
cam.matrix_world,cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end=camera_state
scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath=render_state
dest=out/'v83_sanctuary_candidate.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;cam=scene.camera
fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT'];ruin=bpy.data.collections['V81_RUNE_SANCTUARY']
assert snapshot()==after and fx.hide_render and fx.hide_viewport
qa['native_sha256']=sha(dest);qa['reopen_protected_exact']=True
checkpoint()
for view in ('altar_front','altar_oblique','ivy_detail','player_eye'):render(view,'B_dormant')
# Demonstrate same native with independent rune VFX active, not runtime animation.
fx.hide_render=False;fx.hide_viewport=False
for o in fx.objects:o.hide_render=False
render('altar_front','B_active')
fx.hide_render=True;fx.hide_viewport=True
# Export only the visible ruin candidate; keep default-off VFX separate.
base_objects=sorted([o for o in ruin.objects if o.type=='MESH' and not o.hide_render and not o.hide_viewport],key=lambda o:o.name)
assert len(base_objects)==6,[o.name for o in base_objects]
bpy.ops.object.select_all(action='DESELECT')
for o in base_objects:o.hide_select=False;o.select_set(True)
bpy.context.view_layer.objects.active=base_objects[0]
glb=out/'v83_sanctuary_dormant.glb'
bpy.ops.export_scene.gltf(filepath=str(glb.resolve()),export_format='GLB',use_selection=True,export_image_format='AUTO',export_apply=True,export_animations=False)
with glb.open('rb') as f:
    magic,version,length=struct.unpack('<4sII',f.read(12));size,kind=struct.unpack('<II',f.read(8));data=json.loads(f.read(size))
assert magic==b'glTF' and version==2 and length==glb.stat().st_size and kind==0x4e4f534a
assert not any(any(v>0 for v in m.get('emissiveFactor',[])) or 'emissiveTexture' in m for m in data.get('materials',[]))
qa['base_glb']={'sha256':sha(glb),'meshes':len(data.get('meshes',[])),'materials':[m.get('name') for m in data.get('materials',[])],'emissive_materials':0}
qa['source_unchanged']=sha(src)==LOCK
assert qa['source_unchanged']
checkpoint();print('V83_SANCTUARY_DONE',json.dumps(qa))
