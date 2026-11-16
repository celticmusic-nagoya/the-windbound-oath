"""Build isolated EYELID-09 surface-frame lash candidates, not official assets.

Replaces world-up-only lash direction with a root-local frame derived from
adjacent upper margin points and verified root normals. Geometry is intentionally
not auto-approved; BVH collision and visual QA must run separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import bpy
from mathutils import Vector

def frame(roots,index):
    root=roots[index]
    p=Vector(root["root_world_m"])
    normal=Vector(root["normal_world"])
    if normal.length<1e-8:raise ValueError("Degenerate cage normal")
    normal.normalize()
    prev=Vector(roots[max(0,index-1)]["root_world_m"])
    nxt=Vector(roots[min(len(roots)-1,index+1)]["root_world_m"])
    tangent=nxt-prev
    tangent-=normal*tangent.dot(normal)
    if tangent.length<1e-8:raise ValueError("Degenerate margin tangent")
    tangent.normalize()
    transverse=normal.cross(tangent)
    if transverse.length<1e-8:raise ValueError("Degenerate transverse")
    transverse.normalize()
    # Outward surface normal defines the primary clearance direction.
    # Transverse controls eyelid-relative sweep; world-up is never used.
    growth=(normal*0.65+transverse*0.35).normalized()
    return p,normal,tangent,growth

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--anchors",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    raw=a.anchors.read_bytes()
    data=json.loads(raw)
    if data.get("status")!="UNAPPROVED_ANCHOR_CANDIDATES":raise ValueError("Unapproved root source required")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    counts={}
    for side in ("R","L"):
        roots=data["sides"][side]
        if len(roots)!=9:raise ValueError("Expected 9 anchors per side")
        for j in range(9):
            p,normal,tangent,growth=frame(roots,j)
            verts=[]
            for k in range(6):
                t=k/5
                center=p+normal*(0.00045+0.00025*t)+growth*(0.0028*t)
                half=0.00025*max(0.025,(1-t)**1.25)
                verts.extend([center-tangent*half,center+tangent*half])
            faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(5)]
            name=f"M09_{side}_LASH_CANDIDATE_{j:02d}"
            mesh=bpy.data.meshes.new(name+"_mesh")
            mesh.from_pydata(verts,[],faces)
            mesh.update()
            ob=bpy.data.objects.new(name,mesh)
            bpy.context.collection.objects.link(ob)
            assert len(mesh.vertices)==12 and len(mesh.polygons)==5
        counts[side]=9
    a.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
    print("M09_SURFACE_FRAME_CANDIDATE="+json.dumps({"status":"UNAPPROVED_GEOMETRY",
        "root_input_sha256":hashlib.sha256(raw).hexdigest(),
        "counts":counts,"vertices":216,"faces":90,
        "collision_qa":"NOT_RUN","art_qa":"NOT_RUN","canonical_approval":"BLOCKED"},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
