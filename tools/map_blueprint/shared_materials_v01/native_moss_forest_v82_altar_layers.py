"""Director 2026-11-27: dormant altar and separate rune VFX assets.
Recover V82-A SHA-locked native, split the existing rune faces without redesigning
stone geometry. Base has no luminous rune faces; optional VFX shares world origin.
No new carving, shader bloom, event wiring or geometry adoption in this scope.
"""
import bpy, bmesh, sys, math, hashlib, json, struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from array import array
src,out=map(Path,sys.argv[sys.argv.index('--')+1:][:2])
out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with open(p,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
LOCK='570e20fa707a18a92256cce78832909049004f3087d1e444492f18229b6a3fb2'
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




platform=bpy.data.objects['V81_ruin_platform']
# Recover platform top from the actual emissive inlay, not a guessed world height.
rz=[(platform.matrix_world @ platform.data.vertices[i].co).z for p in platform.data.polygons if p.material_index==1 for i in p.vertices]
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
base_objects=sorted(list(ruin.objects),key=lambda o:o.name)
sources=[o for o in base_objects if o.type=='MESH' and any(m and m.name=='V81_rune_glow' for m in o.data.materials)]
assert sources
fx=bpy.data.collections.new('V82_RUNE_VFX_INDEPENDENT');scene.collection.children.link(fx)
def digest(mesh):
    a=array('f',[0])*(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',a)
    b=array('i',[0])*len(mesh.loops);mesh.loops.foreach_get('vertex_index',b)
    return hashlib.sha256(a.tobytes()+b.tobytes()).hexdigest()
def faces_signature(mesh, slots, want):
    # Ordered polygon coordinates, including winding and UVs, independent of vertex reindexing.
    uv=mesh.uv_layers.active
    result=[]
    for p in mesh.polygons:
        if (p.material_index in slots)!=want: continue
        result.append(tuple((tuple(mesh.vertices[mesh.loops[i].vertex_index].co),tuple(uv.data[i].uv) if uv else ()) for i in p.loop_indices))
    return sorted(result)
def split_mesh(mesh, slots, want, name):
    copy=mesh.copy(); copy.name=name
    bm=bmesh.new();bm.from_mesh(copy)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if (f.material_index in slots)!=want],context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bm.to_mesh(copy);bm.free();copy.update()
    return copy
qa={'candidate_only':True,'source_sha256':LOCK,'frame':'existing V82-A provisional world coordinates; base and VFX identical origin','split':{},'limits':['No engraved recess added: existing emissive ribbons separated, stone unchanged','D2 geometry drawings open; no new precision stone edit','GLB VFX is static geometry; game must animate visibility/emission','timing and bloom not canon','G2 and G4 not certified']}
protected={o.name:(digest(o.data) if o.type=='MESH' else None,tuple(tuple(row) for row in o.matrix_world),o.hide_render,o.hide_viewport) for o in scene.objects if o not in sources}
fx_objects=[]
for o in sources:
    original=o.data; slots={i for i,m in enumerate(original.materials) if m and m.name=='V81_rune_glow'}
    stone=faces_signature(original,slots,False); glow=faces_signature(original,slots,True)
    if not glow: continue
    assert stone
    body=split_mesh(original,slots,False,o.name+'_dormant')
    runes=split_mesh(original,slots,True,o.name+'_runes')
    assert faces_signature(body,slots,False)==stone and faces_signature(runes,slots,True)==glow
    # Existing stone-only faces all use the first stone material.
    assert all(p.material_index==0 for p in body.polygons)
    stone_mat=original.materials[0];body.materials.clear();body.materials.append(stone_mat)
    stage={'V81_ruin_back':'01_stele','V81_ruin_posts':'02_posts','V81_ruin_platform':'03_floor'}[o.name]
    m=bpy.data.materials['V81_rune_glow'].copy();m.name='V82_FX_'+stage
    runes.materials.clear();runes.materials.append(m)
    for poly in runes.polygons: poly.material_index=0
    o.data=body
    v=bpy.data.objects.new('V82_FX_'+stage,runes);fx.objects.link(v);v.matrix_world=o.matrix_world.copy();v['stage']=stage
    fx_objects.append(v);qa['split'][o.name]={'stone_faces':len(stone),'rune_faces':len(glow),'stone_and_rune_coordinates_uv_exact':True,'vfx_object':v.name}
assert len(fx_objects)==3
# Read-only floor height diagnostic: top ray grid within inner disc, excluding glow.
platform=bpy.data.objects['V81_ruin_platform']
verts=[platform.matrix_world@v.co for v in platform.data.vertices]
bvh=BVHTree.FromPolygons(verts,[tuple(p.vertices) for p in platform.data.polygons])
heights=[];miss=0
for i in range(-20,21):
    for j in range(-20,21):
        x,y=i*.12,j*.12
        if x*x+y*y>2.4**2:continue
        hit=bvh.ray_cast(Vector((C0.x+x,C0.y+y,T+5)),Vector((0,0,-1)),10)[0]
        if hit is None:miss+=1
        else:heights.append(hit.z-T)
assert heights
qa['floor_diagnostic']={'hits':len(heights),'misses':miss,'min_delta_from_v81_top':min(heights),'max_delta':max(heights),'below_top_by_0_05':sum(z<-.05 for z in heights),'note':'vertical top-surface samples, not topology proof'}
def export(objects,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.hide_select=False;o.select_set(True)
    dest=out/name
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_image_format='AUTO',export_apply=True,export_animations=False)
    with dest.open('rb') as f:
        magic,version,length=struct.unpack('<4sII',f.read(12));size,kind=struct.unpack('<II',f.read(8));data=json.loads(f.read(size))
    assert magic==b'glTF' and version==2 and length==dest.stat().st_size and kind==0x4e4f534a
    return data,{'sha256':sha(dest),'bytes':length,'meshes':len(data.get('meshes',[])),'materials':[m.get('name') for m in data.get('materials',[])]}
base_data,qa['base_glb']=export(base_objects,'v82_altar_dormant.glb')
fx_data,qa['vfx_glb']=export(fx_objects,'v82_altar_rune_vfx.glb')
assert not any(any(v>0 for v in m.get('emissiveFactor',[])) or 'emissiveTexture' in m for m in base_data.get('materials',[])), 'base contains emissive material'
assert all(any(v>0 for v in m.get('emissiveFactor',[])) for m in fx_data.get('materials',[])), 'VFX material not emissive'
qa['base_emissive_materials']=0
assert all((digest(bpy.data.objects[k].data) if bpy.data.objects[k].type=='MESH' else None,tuple(tuple(row) for row in bpy.data.objects[k].matrix_world),bpy.data.objects[k].hide_render,bpy.data.objects[k].hide_viewport)==val for k,val in protected.items())
assert sha(src)==LOCK
# Save combined editable native with VFX disabled in default view and render.
fx.hide_render=True;fx.hide_viewport=True
dest=out/'v82_altar_layers.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()))
scene=bpy.context.scene;cam=scene.camera;fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert fx.hide_render and fx.hide_viewport and len(fx.objects)==3
qa['native_sha256']=sha(dest);qa['default_vfx_disabled_after_reopen']=True
(out/'v82_altar_layers_qa.json').write_text(json.dumps(qa,indent=2))
def render(name,state):
    p,t,lens=VIEWS[name];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.filepath=str((out/('v82_'+state+'_'+name+'.png')).resolve());bpy.ops.render.render(write_still=True)
for state in ('dormant','stele_preview','active'):
    fx.hide_render=state=='dormant';fx.hide_viewport=state=='dormant'
    for o in fx.objects:o.hide_render=(state=='stele_preview' and not o.name.endswith('01_stele'))
    for view in (('altar_front','altar_oblique') if state!='stele_preview' else ('altar_front',)):render(view,state)
qa['source_unchanged']=sha(src)==LOCK
(out/'v82_altar_layers_qa.json').write_text(json.dumps(qa,indent=2))
print('V82_ALTAR_LAYERS_DONE',json.dumps(qa))
