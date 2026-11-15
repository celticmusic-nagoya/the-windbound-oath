"""Bounded anterior correction on the disposable preview's opaque card samples."""
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from qa_contact_cage_08 import mesh_snapshot
from verify_delivery_08 import inside_closed_shell


def clear_preview_cards(preview,cages,metadata):
    snapshots={s:mesh_snapshot(ob) for s,ob in cages.items()};front={}
    for side,ob in cages.items():
        vertices,_,_,_=snapshots[side];ob.data.calc_loop_triangles()
        tris=[t.vertices[:] for t in ob.data.loop_triangles if metadata[side]['face_roles'][t.polygon_index]=='front']
        front[side]=BVHTree.FromPolygons([Vector(p) for p in vertices],tris,all_triangles=True)
    me=preview.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;cache={};constraints=[];card_ids=set()
    for tri in me.loop_triangles:
        mat=me.materials[tri.material_index]
        if not any(x in mat.name for x in ('Eyeline','Eyelash','EyeExtra')):continue
        image=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat.use_nodes else None
        if image is None:continue
        if image.name not in cache:
            w,h=image.size;cache[image.name]=(np.array(image.pixels[:]).reshape(h,w,4),w,h)
        pixels,w,h=cache[image.name];ids=list(tri.vertices);card_ids.update(ids)
        world=np.array([tuple(preview.matrix_world@me.vertices[v].co) for v in ids]);tex=np.array([uv[l].uv[:] for l in tri.loops])
        for i in range(5):
            for j in range(5-i):
                weights=np.array([i/4,j/4,1-(i+j)/4]);t=weights@tex
                if pixels[min(h-1,max(0,int(t[1]*h))),min(w-1,max(0,int(t[0]*w))),3]<.5:continue
                point=weights@world;side='R' if point[0]>.00026 else 'L'
                if not inside_closed_shell(point,snapshots[side]):continue
                hit=front[side].ray_cast(Vector(point)+Vector((0,.1,0)),Vector((0,-1,0)))[0]
                if hit is None:raise ValueError('Opaque card inside shell without anterior exit')
                need=hit.y+.0001-point[1]
                if need>0:constraints.append((ids,weights,need))
    if not constraints:return {'constraint_count':0,'max_lift_m':0}
    rows=[];cols=[];data=[];rhs=[]
    for row,(ids,weights,need) in enumerate(constraints):
        rhs.append(-need)
        for v,w in zip(ids,weights):rows.append(row);cols.append(v);data.append(-float(w))
    result=linprog(np.ones(len(me.vertices)),A_ub=coo_matrix((data,(rows,cols)),shape=(len(rhs),len(me.vertices))).tocsr(),b_ub=rhs,bounds=[(0,.003) if v in card_ids else (0,0) for v in range(len(me.vertices))],method='highs')
    if not result.success:raise ValueError('Opaque preview-card clearance infeasible: '+result.message)
    inv=preview.matrix_world.inverted().to_3x3()
    for v,delta in enumerate(result.x):
        if delta:me.vertices[v].co+=inv@Vector((0,float(delta),0))
    me.update()
    return {'constraint_count':len(rhs),'max_lift_m':float(max(result.x)),'clearance_m':.0001,'max_allowed_lift_m':.003,'scope':'disposable preview card vertices only; finite alpha samples; artist review required'}
