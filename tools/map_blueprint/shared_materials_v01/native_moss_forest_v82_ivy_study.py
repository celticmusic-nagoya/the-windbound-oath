"""V82-C isolated ivy form study and oak source inventory.
Preserve all stone/rune geometry; compare new individual sculpted leaf silhouettes
at actual V81 card anchor positions, not a canonical foliage redesign.
Independent V82 altar-layer input, not the concurrent stone candidate.
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



from random import Random
from collections import Counter
rng=Random(20261127082)
ruin=bpy.data.collections['V81_RUNE_SANCTUARY']
fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert fx.hide_render and fx.hide_viewport
ivy=bpy.data.objects['V81_ruin_ivy']
assert ivy.type=='MESH' and len(ivy.data.polygons)==342
stone_objects=[bpy.data.objects[n] for n in ('V81_ruin_platform','V81_ruin_back','V81_ruin_posts')]
walls=world_bvh(stone_objects)
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
qa={'candidate_only':True,'source_sha256':LOCK,'scope':'isolated ivy A/B; oak read-only material inventory','ivy':{},'oak':{},'limits':['Existing card centres are provisional anchors, not proven botanical stems','Authored leaf palette; not a new photo-texture acquisition','No new official placement, no game export or G2/G4 claim','No alteration of stone, rune, trail or forest source geometry']}
# Diagnose existing card transparency before introducing explicit silhouettes.
im=bpy.data.images['leaf_cluster_beech_basecolor']
assert im.size[0]>0 and im.size[1]>0
px=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(px)
alpha=px[3::4]
qa['ivy']['old_texture']={'name':im.name,'size':list(im.size),'alpha_below_half_fraction':float((alpha<.5).mean()),'alpha_mean':float(alpha.mean())}
# Individually shaped, folded ivy leaves. No alpha cards or emission.
palette=[(.045,.105,.025),(.072,.152,.035),(.11,.20,.050),(.16,.25,.070),(.035,.075,.022)]
materials=[]
for i,color in enumerate(palette):
    m=bpy.data.materials.new('V82C_ivy_leaf_%d'%i);m.use_nodes=True
    bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.66;bs.inputs['Subsurface Weight'].default_value=.08
    materials.append(m)
stemmat=bpy.data.materials.new('V82C_ivy_petiole');stemmat.use_nodes=True
bs=stemmat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.095,.078,.032,1);bs.inputs['Roughness'].default_value=.8
materials.append(stemmat)
vertices=[];faces=[];mi=[]
def face(ids,mat):faces.append(tuple(ids));mi.append(mat)
def leaf(anchor,normal,side,length,mat):
    # Long axis droops. Side axis is tangential, fold points outward.
    down=Vector((0,0,-1));axis=(down+side*rng.uniform(-.8,.8)+normal*rng.uniform(.15,.55)).normalized()
    across=normal.cross(axis).normalized();n=axis.cross(across).normalized()
    if n.dot(normal)<0:n=-n
    petiole=anchor+normal*.035
    root=petiole+axis*.025
    # Distinct lobed heart outline, in local axis/across coordinates.
    outline=[(0,0),(.12,-.32),(.32,-.48),(.39,-.27),(.53,-.39),(.70,-.20),(1,0),(.70,.20),(.53,.39),(.39,.27),(.32,.48),(.12,.32)]
    k=len(vertices)
    vertices.extend([root+axis*(a*length)+across*(b*length) for a,b in outline])
    vertices.append(root+axis*(.48*length)+n*(.095*length))
    for i in range(len(outline)):face((k+i,k+(i+1)%len(outline),k+len(outline)),mat)
    # Small petiole quad, connects leaf base to the anchor.
    k=len(vertices);w=across*.004
    vertices.extend([anchor-w,anchor+w,root+w,root-w]);face((k,k+1,k+2,k+3),5)
    return root
accepted=0;skipped=0;contact=[]
for poly in sorted(ivy.data.polygons,key=lambda p:p.index):
    points=[ivy.matrix_world@ivy.data.vertices[i].co for i in poly.vertices]
    c=sum(points,Vector())/len(points)
    normal=(ivy.matrix_world.to_3x3()@poly.normal).normalized()
    # Resolve outward orientation against the nearest masonry surface.
    near=walls.find_nearest(c)
    if near[0] is None or near[3]>.5:skipped+=1;continue
    surface,wn,idx,dist=near
    outward=c-surface
    if outward.length>.001:normal=outward.normalized()
    if abs(normal.z)>.94:skipped+=1;continue
    side=Vector((0,0,1)).cross(normal).normalized()
    # Reuse measured masonry anchor, limit extension and avoid dense blanket cover.
    a=surface+normal*.025
    leaf(a,normal,side,rng.uniform(.12,.19),rng.randrange(5))
    leaf(a+side*rng.uniform(-.035,.035)+Vector((0,0,-.045)),normal,-side,rng.uniform(.085,.145),rng.randrange(5))
    contact.append(float(dist));accepted+=1
assert accepted>=150,(accepted,skipped)
mesh=bpy.data.meshes.new('V82C_ivy_lobed_leaf_study')
mesh.from_pydata(vertices,[],faces);mesh.update()
for m in materials:mesh.materials.append(m)
for p,i in zip(mesh.polygons,mi):p.material_index=i;p.use_smooth=True
assert not mesh.validate(verbose=False)
mesh.calc_loop_triangles()
obj=bpy.data.objects.new('V82C_ivy_lobed_leaf_study',mesh);ruin.objects.link(obj);obj['scenic_only']=True
obj.hide_render=True;obj.hide_viewport=True
qa['ivy'].update({'source_cards':len(ivy.data.polygons),'anchors_accepted':accepted,'anchors_skipped':skipped,'individual_leaves':accepted*2,'triangles':len(mesh.loop_triangles),'anchor_to_masonry_max':max(contact),'new_geometry_sha256':digest(mesh)})
# Oak source mesh material/triangle inventory, with actual vertex-sharing across slots.
oak=bpy.data.meshes['island_trees_01_blockout_cleaned'];oak.calc_loop_triangles()
slots={}
for tri in oak.loop_triangles:
    slot=oak.polygons[tri.polygon_index].material_index
    entry=slots.setdefault(slot,{'tris':0,'verts':set()})
    entry['tris']+=1;entry['verts'].update(tri.vertices)
for slot,entry in slots.items():
    used=entry['verts']
    others=set().union(*(v['verts'] for k,v in slots.items() if k!=slot))
    qa['oak'][str(slot)]={'material':oak.materials[slot].name if oak.materials[slot] else None,'triangles':entry['tris'],'unique_vertices':len(used),'shared_with_other_slots':len(used&others)}
qa['oak_total_triangles']=len(oak.loop_triangles)
qa['oak_instances']=sum(o.type=='MESH' and o.data==oak for o in scene.objects)
# Identical-camera A/B. VFX remains disabled.
cam=scene.camera
camera_state=(cam.matrix_world.copy(),cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end)
render_state=(scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath)
def render(name,state):
    p,t,lens=VIEWS[name];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.filepath=str((out/('v82c_'+state+'_'+name+'.png')).resolve());bpy.ops.render.render(write_still=True)
# Add a matched closer crop on the rear structures without modifying game cameras.
VIEWS['ivy_detail']=(Vector((*(C0+FD*4.0+FDP*1.4),T+2.1)),Vector((*(C0-FD*5.0),T+2.0)),43)
for n in ('altar_front','altar_oblique','ivy_detail'):render(n,'A')
ivy.hide_render=True;ivy.hide_viewport=True;obj.hide_render=False;obj.hide_viewport=False
cam.matrix_world,cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end=camera_state
scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath=render_state
after=snapshot()
assert all(after[k]==v for k,v in old.items() if k!=ivy.name)
assert after[ivy.name][:2]==old[ivy.name][:2] and after[ivy.name][2:]==(True,True)
assert sha(src)==LOCK and fx.hide_render
dest=out/'v82c_ivy_candidate.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;cam=scene.camera
assert snapshot()==after and bpy.data.collections['V82_RUNE_VFX_INDEPENDENT'].hide_render
qa['native_sha256']=sha(dest);qa['reopen_protected_exact']=True
(out/'v82c_ivy_oak_qa.json').write_text(json.dumps(qa,indent=2))
for n in ('altar_front','altar_oblique','ivy_detail'):render(n,'B')
qa['source_unchanged']=sha(src)==LOCK
(out/'v82c_ivy_oak_qa.json').write_text(json.dumps(qa,indent=2))
print('V82C_IVY_DONE',json.dumps(qa))
