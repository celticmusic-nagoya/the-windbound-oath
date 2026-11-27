"""V82-F: local native central substrate topology repair.
Exact V82-B input. Identify component with degenerate triangles, weld only
coincident vertices in that component, require unchanged other face/UV signatures
and sampled top surface. No blanket merge, no material edit, no new dimensions.
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
LOCK='6061d7233cf32b2b1b1e37bfae28a6d15f43eda88c6fd6cf00807eda0c7962a5'
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



import bmesh
from collections import Counter,defaultdict
platform=bpy.data.objects['V81_ruin_platform']
fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert fx.hide_render and fx.hide_viewport and platform.data.users==1
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
oldmesh=platform.data
oldmesh.calc_loop_triangles()
EPS=1e-10
def triangle_area(m,t):
    a,b,c=(m.vertices[i].co for i in t.vertices)
    return (b-a).cross(c-a).length*.5
bad=[t.polygon_index for t in oldmesh.loop_triangles if triangle_area(oldmesh,t)<=EPS]
assert bad,'No degenerate native loop triangles, inspect exporter rather than mutate'
# Identify only vertex-connected component(s) of the observed zero-area triangles.
bm=bmesh.new();bm.from_mesh(oldmesh);bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
seed=set(bm.faces[i] for i in set(bad));seen=set();groups=[]
for f in sorted(seed,key=lambda x:x.index):
    if f in seen:continue
    component={f};todo=[f];seen.add(f)
    while todo:
        for v in todo.pop().verts:
            for g in v.link_faces:
                if g not in seen:seen.add(g);component.add(g);todo.append(g)
    groups.append(component)
assert len(groups)==1,('unexpected defect components',len(groups))
target=groups[0];indices={f.index for f in target};verts={v for f in target for v in f.verts}
# Spatial preflight: central substrate should span the disc and include exact centre.
center_vertices=[v for v in verts if (platform.matrix_world@v.co).to_2d().__sub__(C0).length<.001]
assert len(center_vertices)>=2 and max(((platform.matrix_world@v.co).to_2d()-C0).length for v in verts)<4.4
def sig_mesh(m,exclude=set()):
    uv=m.uv_layers.active
    return Counter((p.material_index,tuple((tuple(m.vertices[m.loops[i].vertex_index].co),tuple(uv.data[i].uv) if uv else ()) for i in p.loop_indices)) for p in m.polygons if p.index not in exclude)
untouched=sig_mesh(oldmesh,indices)
# Preserve an exact signature for the existing non-defect component faces, independently
# of polygon index changes in BMesh.
layer=bm.faces.layers.int.new('V82F_repair_component')
for f in target:f[layer]=1
qa={'candidate_only':True,'source_sha256':LOCK,'threshold_area':EPS,'before':{'loop_triangles':len(oldmesh.loop_triangles),'zero_area_triangles':len(bad),'defect_component_faces':len(target),'defect_component_vertices':len(verts),'centre_vertices':len(center_vertices)},'limits':['Central substrate only; no stone appearance or rune change','Finite grid surface diagnostic, not traversal certification','No adopted geometry, no G2/G4']}
def topo(faces):
    ee={e for f in faces for e in f.edges}
    return {'boundary_edges':sum(len(e.link_faces)==1 for e in ee),'nonmanifold_edges':sum(len(e.link_faces)>2 for e in ee),'zero_area_faces':sum(f.calc_area()<=EPS for f in faces)}
qa['before'].update(topo(target))
# Weld only coincident vertices of this one component, never between masonry blocks.
# Use a small tolerance, substantially below existing geometric detail.
bm.normal_update()
bmesh.ops.remove_doubles(bm,verts=list(verts),dist=1e-6)
bm.normal_update()
new_target=[f for f in bm.faces if f[layer]==1]
assert new_target
# Degenerate residuals (if any) are diagnosed and rejected, not silently deleted.
qa['after_component']=topo(new_target)
assert qa['after_component']['zero_area_faces']==0 and qa['after_component']['nonmanifold_edges']==0 and qa['after_component']['boundary_edges']==0,qa['after_component']
mesh=oldmesh.copy();mesh.name='V82F_platform_center_repaired';bm.to_mesh(mesh);bm.free();mesh.update()
attr=mesh.attributes['V82F_repair_component'];new_indices={i for i,v in enumerate(attr.data) if v.value==1}
assert sig_mesh(mesh,new_indices)==untouched,'non-target faces or UVs changed'
mesh.attributes.remove(attr);mesh.calc_loop_triangles()
zeros=sum(triangle_area(mesh,t)<=EPS for t in mesh.loop_triangles)
assert zeros==0,('remaining zero-area triangles',zeros)
qa['after']={'loop_triangles':len(mesh.loop_triangles),'zero_area_triangles':zeros,'untouched_face_signatures_exact':True}
# Compare actual top surface on a 0.1 unit grid over the inner disc.
def bvh(m):
    return BVHTree.FromPolygons([platform.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
before,after=bvh(oldmesh),bvh(mesh)
delta=[];missing=0
for ix in range(-40,41):
    for iy in range(-40,41):
        if ix*ix+iy*iy>40*40:continue
        origin=Vector((C0.x+.1*ix,C0.y+.1*iy,T+10))
        a=before.ray_cast(origin,Vector((0,0,-1)),20)[0];b=after.ray_cast(origin,Vector((0,0,-1)),20)[0]
        if a is None or b is None:missing+=1;continue
        delta.append(abs(a.z-b.z))
qa['surface_grid']={'paired_hits':len(delta),'missing':missing,'max_delta_local':max(delta) if delta else None,'tolerance_local':.0001}
assert len(delta)>0 and missing==0 and max(delta)<=.0001
platform.data=mesh
newfp=fingerprint()
assert all(newfp[k]==v for k,v in protected.items() if k!=platform.name)
assert newfp[platform.name][1:]==protected[platform.name][1:]
assert fx.hide_render and sha(src)==LOCK
dest=out/'v82f_floor_native_repair.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;platform=bpy.data.objects['V81_ruin_platform']
assert fingerprint()==newfp and bpy.data.collections['V82_RUNE_VFX_INDEPENDENT'].hide_render
platform.data.calc_loop_triangles();assert sum(triangle_area(platform.data,t)<=EPS for t in platform.data.loop_triangles)==0
qa.update({'native_sha256':sha(dest),'source_unchanged':sha(src)==LOCK,'reopen_exact':True,'other_objects_exact':True})
(out/'v82f_floor_qa.json').write_text(json.dumps(qa,indent=2));print('V82F_FLOOR_DONE',json.dumps(qa))
