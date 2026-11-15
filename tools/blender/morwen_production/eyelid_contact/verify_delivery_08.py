"""Read-only protected Face comparison and eye/opaque-card cage interference."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import bpy
import numpy as np
from mathutils import Vector
from qa_contact_cage_08 import mesh_snapshot,intersection_audit


def face_signature(face):
    me=face.data;h=hashlib.sha256()
    h.update(np.array(face.matrix_world,dtype='<f8').tobytes())
    for v in me.vertices:h.update(struct.pack('<I3d',v.index,*v.co))
    for e in me.edges:h.update(struct.pack('<2I',*e.vertices))
    for p in me.polygons:h.update(repr((tuple(p.vertices),p.material_index,p.use_smooth)).encode())
    for layer in me.uv_layers:
        h.update(layer.name.encode())
        for uv in layer.data:h.update(struct.pack('<2d',*uv.uv))
    for key in me.shape_keys.key_blocks:
        h.update(repr((key.name,key.relative_key.name,key.value,key.slider_min,key.slider_max,key.mute,key.vertex_group)).encode())
        for v in key.data:h.update(struct.pack('<3d',*v.co))
    for attr in me.attributes:
        if attr.name=='elm_patch':
            h.update(repr([v.value for v in attr.data]).encode())
    h.update(repr([(m.name,m.type) for m in face.modifiers]).encode())
    return h.hexdigest()


def card_samples(preview):
    me=preview.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;cache={};unclassified=0;points=[]
    for tri in me.loop_triangles:
        mat=me.materials[tri.material_index]
        if not any(x in mat.name for x in ('Eyeline','Eyelash','EyeExtra')):continue
        image=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat.use_nodes else None
        if image is None:unclassified+=1;continue
        if image.name not in cache:
            w,h=image.size;cache[image.name]=(np.array(image.pixels[:]).reshape(h,w,4),w,h)
        pixels,w,h=cache[image.name];world=np.array([tuple(preview.matrix_world@me.vertices[v].co) for v in tri.vertices]);tex=np.array([uv[l].uv[:] for l in tri.loops])
        for i in range(5):
            for j in range(5-i):
                weights=np.array([i/4,j/4,1-(i+j)/4]);t=weights@tex
                if pixels[min(h-1,max(0,int(t[1]*h))),min(w-1,max(0,int(t[0]*w))),3]>=.5:points.append(weights@world)
    return points,unclassified


def inside_closed_shell(p,snapshot):
    verts,tris,_,bvh=snapshot
    hit,_,_,distance=bvh.find_nearest(Vector(p))
    if hit is not None and distance<1e-7:return False # boundary contact
    # Generalized winding number avoids float32 self-hits during iterative BVH
    # parity rays. The shell has independently checked consistent orientation.
    vectors=verts[tris]-p
    a,b,c=vectors[:,0],vectors[:,1],vectors[:,2]
    la,lb,lc=(np.linalg.norm(x,axis=1) for x in (a,b,c))
    det=np.einsum('ij,ij->i',a,np.cross(b,c))
    denominator=la*lb*lc+np.einsum('ij,ij->i',a,b)*lc+np.einsum('ij,ij->i',b,c)*la+np.einsum('ij,ij->i',c,a)*lb
    angle=np.sum(2*np.arctan2(det,denominator))
    return abs(angle)>2*np.pi


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('New report path required')
    source_hash=hashlib.sha256(a.source.read_bytes()).hexdigest();candidate_hash=hashlib.sha256(a.candidate.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()));source=face_signature(bpy.data.objects['Face'])
    bpy.ops.wm.open_mainfile(filepath=str(a.candidate.resolve()));face=bpy.data.objects['Face'];actual=face_signature(face)
    assert source==actual,'Protected Face data changed'
    eye=mesh_snapshot(bpy.data.objects['MORWEN_Eyes']);cages={s:mesh_snapshot(bpy.data.objects[f'M08_{s}_CONTACT_CAGE_050']) for s in ('R','L')}
    preview=bpy.data.objects['M08_ATTACHMENT_PREVIEW_ONLY'];samples,unknown=card_samples(preview)
    report={'source_sha256':source_hash,'candidate_sha256':candidate_hash,'protected_face_signature':source,'protected_face_data_unchanged':True,'protected_face_key_count':len(face.data.shape_keys.key_blocks),'cage_eye_intersections':{s:intersection_audit(c,eye) for s,c in cages.items()},'opaque_card_sample_count':len(samples),'unclassified_card_triangles':unknown,'opaque_card_samples_inside_cage':{s:int(sum(inside_closed_shell(p,c) for p in samples)) for s,c in cages.items()},'sampling_note':'15 barycentric samples per card triangle, alpha>=0.5; finite sampling, not continuous collision proof'}
    assert hashlib.sha256(a.source.read_bytes()).hexdigest()==source_hash and hashlib.sha256(a.candidate.read_bytes()).hexdigest()==candidate_hash
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
