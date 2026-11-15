"""Explicit static 50% cage: constrained polygon-with-hole triangulation.

Structural switch from ruled quadrilateral rows: outer/inner segments are hard
constraints; the surface is a single-valued anterior graph, extruded into a closed
solid shell. No interpolation of the old expression/Dirichlet space is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
import triangle
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from contact_geometry_08 import walk_cycle,triangulate_aperture
from obstacle_constraints_08 import clear_eye
from build_contact_cage_08 import outer_edges,preview,ROOT
from run_structural_qa_07 import fingerprints



def build(face,side,m):
    me=face.data;xyz=np.array([tuple(face.matrix_world@v.co) for v in me.shape_keys.key_blocks[0].data]);tags=[a.value for a in me.attributes['elm_patch'].data];pid=1 if side=='R' else 2
    upper,lower=np.array(m['half_margin_upper']),np.array(m['half_margin_lower'])
    inner=np.r_[upper,lower[-2:0:-1]]
    outer_ids=walk_cycle(outer_edges(face,pid,tags));outer=xyz[outer_ids]
    outer2=outer[:,[0,2]];inner2=inner[:,[0,2]]
    triangulation=triangulate_aperture(outer2,inner2)
    plan=triangulation['vertices'];triangles=triangulation['triangles'];n=len(plan)
    me.calc_loop_triangles();source=[t for t in me.loop_triangles if all(tags[v]==pid for v in t.vertices)]
    bvh=BVHTree.FromPolygons([Vector(p) for p in xyz],[t.vertices[:] for t in source],all_triangles=True)
    front=np.array([[p[0],0,p[1]] for p in plan])
    for i,p in enumerate(front):
        if i<len(outer):front[i]=outer[i]
        elif i<len(outer)+len(inner):front[i]=inner[i-len(outer)]
        else:
            # Sample the original patch from the front; nearest-patch fallback
            # only where new coverage enters the old aperture. Never ray to head back.
            hit=bvh.ray_cast(Vector((p[0],.20,p[2])),Vector((0,-1,0)))[0]
            if hit is None:hit=bvh.find_nearest(Vector((p[0],.08,p[2])))[0]
            front[i,1]=hit.y
    eyes=bpy.data.objects['MORWEN_Eyes'];eyes.data.calc_loop_triangles()
    eye=np.array([tuple(eyes.matrix_world@v.co) for v in eyes.data.vertices])
    eye_triangles=np.array([t.vertices[:] for t in eyes.data.loop_triangles])
    locked=set(range(len(outer)))|{len(outer),len(outer)+len(upper)-1}
    front,obstacle=clear_eye(front,triangles,eye,eye_triangles,locked)
    rear=front-[0,.0006,0];verts=np.r_[front,rear]
    faces=[];roles=[]
    for triangle_ids in triangles:
        v=list(map(int,triangle_ids));p=verts[v]
        if np.cross(p[1]-p[0],p[2]-p[0])[1]<0:v=v[::-1]
        faces.extend([v,[i+n for i in v[::-1]]]);roles.extend(['front','rear'])
    # Boundary edges of oriented front triangles determine wall winding directly.
    from collections import defaultdict
    edges=defaultdict(list)
    for f,r in zip(faces,roles):
        if r!='front':continue
        for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted((a,b)))].append((a,b))
    for pairs in edges.values():
        if len(pairs)==1:
            a,b=pairs[0];faces.append([a,a+n,b+n,b]);roles.append('attachment_wall' if a<len(outer) and b<len(outer) else 'opening_wall')
    mesh=bpy.data.meshes.new('M08_'+side+'_PSLG_SHELL');mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new('M08_'+side+'_CONTACT_CAGE_050',mesh);bpy.context.scene.collection.objects.link(ob)
    mesh.materials.append(next(m for m in me.materials if 'Face_00_SKIN' in m.name))
    # A new continuous affine UV chart is fitted to source patch texels. This
    # avoids nearest-triangle jumps; it does not touch any original Face UV.
    source_uv=me.uv_layers.active.data;position=[];uvcoords=[]
    for t in source:
        for v,li in zip(t.vertices,t.loops):position.append([xyz[v,0],xyz[v,2],1]);uvcoords.append(source_uv[li].uv[:])
    fit=np.linalg.lstsq(np.array(position),np.array(uvcoords),rcond=None)[0]
    if abs(np.linalg.det(fit[:2,:]))<1e-8:raise ValueError('Degenerate fitted cage UV chart')
    chart=np.c_[front[:,[0,2]],np.ones(n)]@fit;layer=mesh.uv_layers.new(name='M08_IndependentSkinChart')
    for poly,role in zip(mesh.polygons,roles):
        poly.use_smooth=role in ('front','rear')
        if role.endswith('wall'):
            center=np.mean([chart[v%n] for v in poly.vertices],axis=0)
            for li,offset in zip(poly.loop_indices,((-1,-1),(1,-1),(1,1),(-1,1))):layer.data[li].uv=center+np.array(offset)*1e-5
        else:
            for li,v in zip(poly.loop_indices,poly.vertices):layer.data[li].uv=chart[v%n]
    ob.shape_key_add(name='Basis')
    ob['basis_pose']='EXPLICIT_STATIC_HALF_050_NOT_NEUTRAL';ob['status']='UNREVIEWED_CONTACT_CAGE';ob['method_family']='CONSTRAINED_PSLG_CONTACT_SHELL_050'
    new=dict(m);new['face_roles']=roles
    new['half_margin_upper']=front[len(outer):len(outer)+len(upper)].tolist()
    new['half_margin_lower']=np.r_[front[len(outer)][None,:],front[len(outer)+len(upper):len(outer)+len(inner)][::-1],front[len(outer)+len(upper)-1][None,:]].tolist()
    new['eye_obstacle_constraints']=obstacle
    new['topology']={'front_vertices':n,'front_triangles':len(triangles),'outer_boundary_vertices':len(outer),'inner_boundary_vertices':len(inner),'thickness_anterior_m':.0006,'boundary_steiner_points':0,'uv_chart':'least-squares affine source-skin fit; independent new chart'}
    return ob,new


def main():
    ledger=json.loads((ROOT/'tools/blender/morwen_production/_qa/morwen_shared_attempt_ledger.json').read_text())
    failures=sum(a.get('outcome')=='FAIL' and a.get('asset_id')=='morwen-head' and a.get('defect_id')=='MORWEN-EYELID-OPENING-RETOPO' and a.get('method_family')=='CONSTRAINED_PSLG_CONTACT_SHELL_050' for a in ledger['attempts'])
    if failures>=2:raise RuntimeError('STOPPED family: inspect saved disabled candidate; no third build')
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--guide',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    source_hash=hashlib.sha256(a.source.read_bytes()).hexdigest();guide=json.loads(a.guide.read_text());assert source_hash==guide['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()));face=bpy.data.objects['Face'];before=fingerprints();meta={}
    for side in ('R','L'):_,meta[side]=build(face,side,guide['sides'][side])
    copy=preview(face,meta)
    from card_clearance_08 import clear_preview_cards
    card_report=clear_preview_cards(copy,{s:bpy.data.objects[f'M08_{s}_CONTACT_CAGE_050'] for s in ('R','L')},meta)
    face.hide_render=True;face.hide_set(True)
    for ob in bpy.data.objects:
        if ob.name.startswith('M07_SCULPT_'):ob.hide_render=True;ob.hide_set(True)
    assert all(fingerprints().get(k)==v for k,v in before.items())
    guide.update(preview_card_clearance=card_report,status='EXPLICIT_HALF_CAGE_NOT_ADOPTED',attempt_id='M08-PSLG-02',method_family='CONSTRAINED_PSLG_CONTACT_SHELL_050',sides=meta,preview_object=copy.name,neutral_to_half_animation='NOT_RUN_STATIC_HALF_TARGET',source_guide_sha256=hashlib.sha256(a.guide.read_bytes()).hexdigest())
    bpy.ops.wm.save_as_mainfile(filepath=str((a.out/'CONTACT_CAGE_050_08.blend').resolve()),compress=True,copy=True)
    assert hashlib.sha256(a.source.read_bytes()).hexdigest()==source_hash
    (a.out/'CONTACT_CAGE_DESIGN_08.json').write_text(json.dumps(guide,indent=2)+'\n')

if __name__=='__main__':main()
