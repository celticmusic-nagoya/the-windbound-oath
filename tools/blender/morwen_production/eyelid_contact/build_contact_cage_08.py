"""Candidate-only half-closed contact shells from the exact EYELID-07 source.

Original Face is never remeshed, reindexed, edited or given a modifier. A separate
unkeyed preview copy omits the old lid surfaces for geometric attachment review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from collections import defaultdict
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from contact_geometry_08 import walk_cycle,split,parameters,sample,shared_columns,shell

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'eyelid_sculpt'))
from audit_margin_topology_07 import audit
from correspondence_audit_07 import source_anchor_ids
from run_structural_qa_07 import fingerprints


def outer_edges(face,pid,tags):
    adjacent=defaultdict(list)
    for p in face.data.polygons:
        for e in p.edge_keys:adjacent[tuple(sorted(e))].append(p)
    selected={p.index for p in face.data.polygons if all(tags[v]==pid for v in p.vertices) and 'SKIN' in face.data.materials[p.material_index].name}
    return [e for e,polys in adjacent.items() if sum(p.index in selected for p in polys)==1 and not any(any(tags[v]==pid+10 for v in p.vertices) for p in polys)]


def build(face,side,component,record,curve,scale):
    me=face.data;mw=face.matrix_world;tags=[a.value for a in me.attributes['elm_patch'].data]
    xyz=np.array([tuple(mw@v.co) for v in me.shape_keys.key_blocks[0].data])
    anchors=source_anchor_ids(component,record['canthus_vertex_world'])
    upper,lower=split(walk_cycle(component['edge_ids']),*anchors,xyz)
    outer=walk_cycle(outer_edges(face,1 if side=='R' else 2,tags))
    c0,c1=xyz[anchors];axis=c1[[0,2]]-c0[[0,2]];axis/=np.linalg.norm(axis)
    superior=np.array([-axis[1],axis[0]])
    if superior[1]<0:superior=-superior
    origin=(c0[[0,2]]+c1[[0,2]])/2
    medial=min((v for v in outer if (xyz[v,[0,2]]-origin)@axis<0),key=lambda v:abs((xyz[v,[0,2]]-origin)@superior))
    lateral=min((v for v in outer if (xyz[v,[0,2]]-origin)@axis>0),key=lambda v:abs((xyz[v,[0,2]]-origin)@superior))
    ou,ol=split(outer,medial,lateral,xyz)
    raw=[xyz[chain] for chain in (upper,lower,ou,ol)];u=shared_columns(raw)
    neutral=[sample(c,u) for c in raw]
    # The same existing proposal supplies only a source-bound guide. Authoring
    # here is an explicit 50% aperture, not transfer of the old Blink key.
    endpoints=curve['points'][0],curve['points'][-1]
    py=np.interp(u,[p['u'] for p in curve['points']],[p['y_px'] for p in curve['points']])
    deviation=-(py-((1-u)*endpoints[0]['y_px']+u*endpoints[1]['y_px']))/scale
    contact=(1-u[:,None])*c0+u[:,None]*c1;contact[:,2]+=deviation
    # Anterior guide follows the upper neutral margin so contact cannot drift
    # behind the eyeball merely because the lower source curve has different depth.
    contact[:,1]=neutral[0][:,1]
    half=[c.copy() for c in neutral]
    for k in (0,1):half[k]=.5*neutral[k]+.5*contact
    for curves in (neutral,half):
        curves[0][0]=curves[1][0]=c0;curves[0][-1]=curves[1][-1]=c1
    rest,faces,roles,topology=shell(*neutral)
    closed,_,_,_=shell(*half)
    mesh=bpy.data.meshes.new('M08_'+side+'_CONTACT_SHELL');mesh.from_pydata(rest,[],faces);mesh.update()
    ob=bpy.data.objects.new('M08_'+side+'_CONTACT_CAGE_050',mesh);bpy.context.scene.collection.objects.link(ob)
    skin=next(m for m in me.materials if 'Face_00_SKIN' in m.name);mesh.materials.append(skin)
    # Rest UV from source skin triangle interpolation; same UVs in both poses.
    me.calc_loop_triangles();skin_slots={i for i,m in enumerate(me.materials) if 'SKIN' in m.name}
    tris=[t for t in me.loop_triangles if t.material_index in skin_slots]
    bvh=BVHTree.FromPolygons([Vector(p) for p in xyz],[t.vertices[:] for t in tris],all_triangles=True)
    uv=mesh.uv_layers.new(name='SourceSkinUV');source_uv=me.uv_layers.active.data
    for poly,role in zip(mesh.polygons,roles):
        poly.use_smooth=role in ('front','rear')
        for li,v in zip(poly.loop_indices,poly.vertices):
            q,_,idx,_=bvh.find_nearest(Vector(rest[v]));tri=tris[idx]
            uv.data[li].uv=barycentric_transform(q,*[Vector(xyz[i]) for i in tri.vertices],*[source_uv[l].uv.to_3d() for l in tri.loops]).xy
    ob.shape_key_add(name='Basis');key=ob.shape_key_add(name='M08_EXPLICIT_HALF_050');key.data.foreach_set('co',closed.ravel());key.value=1
    ob['status']='CANDIDATE_UNREVIEWED_NOT_CANON';ob['method_family']='MATCHED_COLUMN_THICK_CONTACT_CAGE_050'
    return ob,{'anchors':anchors,'outer_anchors':[medial,lateral],'source_upper_ids':upper,'source_lower_ids':lower,'source_outer_ids':outer,'u':u.tolist(),'neutral_margin_upper':neutral[0].tolist(),'neutral_margin_lower':neutral[1].tolist(),'half_margin_upper':half[0].tolist(),'half_margin_lower':half[1].tolist(),'contact_guide':contact.tolist(),'face_roles':roles,'topology':topology}


def preview(face,metadata):
    ob=face.copy();ob.data=face.data.copy();ob.name='M08_ATTACHMENT_PREVIEW_ONLY'
    bpy.context.scene.collection.objects.link(ob);ob.hide_set(False);ob.hide_render=False
    # Bake current neutral (NoseDepth 0.5) into the disposable preview copy only.
    keys=ob.data.shape_keys.key_blocks;coords=np.array([v.co[:] for v in keys[0].data])
    for key in keys[1:]:coords+=key.value*(np.array([v.co[:] for v in key.data])-np.array([v.co[:] for v in key.relative_key.data]))
    ob.shape_key_clear();ob.data.vertices.foreach_set('co',coords.ravel())
    tags=[a.value for a in ob.data.attributes['elm_patch'].data]
    # Reattach neutral lash/line cards to the explicit half margins on this copy.
    cardids={v for p in ob.data.polygons if any(k in ob.data.materials[p.material_index].name for k in ('Eyeline','Eyelash','EyeExtra')) for v in p.vertices}
    mw=ob.matrix_world;inv=mw.inverted().to_3x3()
    for v in cardids:
        point=np.array(mw@ob.data.vertices[v].co);side='R' if point[0]>0.00026 else 'L';d=metadata[side];best=None
        for arc in ('upper','lower'):
            old=np.array(d['neutral_margin_'+arc]);new=np.array(d['half_margin_'+arc])
            for i,(a,b) in enumerate(zip(old,old[1:])):
                ab=b-a;t=np.clip((point-a)@ab/max(ab@ab,1e-16),0,1);nearest=a+t*ab;dist=np.linalg.norm(point-nearest)
                if best is None or dist<best[0]:best=(dist,(1-t)*(new[i]-old[i])+t*(new[i+1]-old[i+1]))
        if best[0]<.012:ob.data.vertices[v].co+=inv@Vector(best[1])
    bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.verts.layers.int.get('elm_patch')
    remove=[p for p in bm.faces if all(v[layer] in (1,11) for v in p.verts) or all(v[layer] in (2,12) for v in p.verts)]
    bmesh.ops.delete(bm,geom=remove,context='FACES_ONLY');bm.to_mesh(ob.data);bm.free();ob.data.update()
    ob['status']='DISPOSABLE_RENDER_COPY_NOT_SOURCE_FACE';return ob


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    source_hash=hashlib.sha256(a.source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()))
    face=bpy.data.objects['Face'];before=fingerprints();key_order=[k.name for k in face.data.shape_keys.key_blocks]
    qroot=ROOT/'assets/candidates/morwen-eyelid-07-structural/qa';expected=json.loads((qroot/'SHAPE_KEY_FINGERPRINTS_07.json').read_text())
    assert all(before.get(k)==v for k,v in expected['objects'].items()),'Protected source fingerprint differs'
    actual=audit();captured=json.loads((qroot/'EYELID_07_TOPOLOGY_MAP.json').read_text());assert actual['sides']==captured['sides']
    baseline=json.loads((qroot/'EYELID_05_REPORT.json').read_text())
    calibration=json.loads((ROOT/'tools/blender/morwen_production/_qa/eyelid_retopo_05/EYE_TARGETS_05.json').read_text())
    curve=json.loads((ROOT/'tools/blender/morwen_production/eyelid_sculpt/CLOSED_CURVE_CANDIDATE_06.json').read_text());assert curve['source_sha256']==calibration['source']['sha256']
    meta={}
    for side in ('R','L'):
        comp=actual['sides'][side]['components'][0];assert len(comp['edge_ids'])==28
        _,meta[side]=build(face,side,comp,baseline['build']['lid_'+side],curve['sides'][side],calibration['calibration']['s'])
    copy=preview(face,meta)
    # Source remains in the file, hidden only for comparison rendering.
    face.hide_render=True;face.hide_set(True)
    for ob in bpy.data.objects:
        if ob.name.startswith('M07_SCULPT_'):ob.hide_render=True;ob.hide_set(True)
    assert all(fingerprints().get(k)==v for k,v in before.items())
    assert [k.name for k in face.data.shape_keys.key_blocks]==key_order
    report={'status':'UNVALIDATED_HALF_CAGE_NOT_ADOPTED','attempt_id':'M08-CONTACT-01','method_family':'MATCHED_COLUMN_THICK_CONTACT_CAGE_050','source_sha256':source_hash,'protected_key_count':len(key_order),'protected_key_order':key_order,'protected_source_fingerprints_unchanged':True,'anchor_approval':'SOURCE_AUTHORING_ONLY_NOT_FORMAL','sides':meta,'preview_object':copy.name,'G1':'PARTIAL_FULL_CANON_BLOCKED','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN'}
    bpy.ops.wm.save_as_mainfile(filepath=str((a.out/'CONTACT_CAGE_050_08.blend').resolve()),compress=True,copy=True)
    assert hashlib.sha256(a.source.read_bytes()).hexdigest()==source_hash
    (a.out/'CONTACT_CAGE_DESIGN_08.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
