"""09D: distinct geometry construction, surface-constrained root rather than normal averaging.

Only L00 is rebuilt. The first two face spans are projected to the saved
contact cage and pushed into an explicit outward safe envelope. Does not
alter the canonical model, nor claim final collision/motion/art QA.
"""
import argparse
import hashlib
import json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SOURCE_SHA = "9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4"
STRIP = "M09_L_LASH_CANDIDATE_00"
CAGE = "M08_L_CONTACT_CAGE_050"

def cage_bvh(obj):
    mesh=obj.to_mesh()
    try:
        mesh.calc_loop_triangles()
        verts=[obj.matrix_world@v.co for v in mesh.vertices]
        tris=[tuple(t.vertices) for t in mesh.loop_triangles]
        return BVHTree.FromPolygons(verts,tris,all_triangles=True)
    finally:
        obj.to_mesh_clear()

def main():
    p=argparse.ArgumentParser()
    for k in ("model","strips","out","report"):p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists() or a.report.exists():raise ValueError("Refuse overwrite")
    if hashlib.sha256(a.model.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError("Wrong cage source")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    cage=bpy.data.objects[CAGE]
    bvh=cage_bvh(cage)
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith("M09_") and "_LASH_CANDIDATE_" in n]
    if len(dst.objects)!=18:raise ValueError("Missing candidate strips")
    # Imported objects may not be linked to the scene, so link them before saving.
    for obj in dst.objects:
        if obj is None:raise ValueError("Missing imported object")
        if not obj.users_collection:bpy.context.collection.objects.link(obj)
    lash=bpy.data.objects[STRIP]
    old=lash.data
    vertices=[v.co.copy() for v in old.vertices]
    polygons=[tuple(poly.vertices) for poly in old.polygons]
    if len(vertices)!=12 or len(polygons)!=5:raise ValueError("Unexpected strip topology")
    # First 3 cross-sections = first 2 faces. Project each vertex to nearest
    # actual cage surface, then place it in a 0.45 mm outward clearance shell.
    # At section 2 use a continuous blend with original section to avoid a kink.
    changed=[]
    for section in range(3):
        for index in (section*2,section*2+1):
            world=lash.matrix_world@vertices[index]
            hit,normal,tri,dist=bvh.find_nearest(world)
            if hit is None or normal is None:raise ValueError("No nearest cage surface")
            n=normal.normalized()
            if n.length<1e-8:raise ValueError("Degenerate cage surface normal")
            # Normal orientation is verified against the original surface-facing
            # direction of the candidate. Avoid pushing into the cage.
            direction=world-hit
            if direction.length<1e-8:raise ValueError("Ambiguous side of cage")
            if n.dot(direction)<0:n=-n
            target=hit+n*0.00045
            # Section 2 retains original if already farther than clearance.
            if section==2 and dist>=0.00045:target=world
            vertices[index]=lash.matrix_world.inverted()@target
            changed.append({"vertex":index,"nearest_cage_triangle":tri,
                            "original_distance_m":dist,"new_world_m":list(target)})
    newmesh=bpy.data.meshes.new(STRIP+"_SURFACE_CLEARANCE_09D")
    newmesh.from_pydata(vertices,[],polygons)
    newmesh.update()
    lash.data=newmesh
    if old.users==0:bpy.data.meshes.remove(old)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
    report={"status":"UNAPPROVED_SURFACE_CONSTRAINED_ROOT","source_sha256":SOURCE_SHA,
            "input_strip_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
            "modified_strip":STRIP,"modified_vertex_count":len(changed),
            "clearance_m":0.00045,"changes":changed,
            "surface_intersection_qa":"NOT_RUN","containment":"NOT_RUN",
            "swept_motion":"NOT_RUN","art_qa":"NOT_RUN","canonical":"BLOCKED"}
    a.report.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_SURFACE_CLEARANCE_09D="+json.dumps({"changed_vertices":len(changed),
          "status":report["status"]}),flush=True)

if __name__=="__main__":main()
