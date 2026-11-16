"""09G structural candidate: replace crossing two-quad root with a single tapered root fan.

This is not a displacement of the old root. The first two quads are removed,
and a new three-triangle fan bridges a surface-adjacent apex to section 2.
Candidate only; no canonical edits. BVH intersection QA is independent.
"""
import argparse,hashlib,json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SOURCE_SHA="9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4"
NAME="M09_L_LASH_CANDIDATE_00"
CAGE="M08_L_CONTACT_CAGE_050"

def main():
    p=argparse.ArgumentParser()
    for k in ("model","strips","out","report"):p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists() or a.report.exists():raise ValueError("Refuse overwrite")
    if hashlib.sha256(a.model.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError("Wrong model")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    cage=bpy.data.objects[CAGE]
    mesh=cage.to_mesh()
    try:
        mesh.calc_loop_triangles()
        cv=[cage.matrix_world@v.co for v in mesh.vertices]
        ct=[tuple(t.vertices) for t in mesh.loop_triangles]
        cb=BVHTree.FromPolygons(cv,ct,all_triangles=True)
    finally:cage.to_mesh_clear()
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith("M09_") and "_LASH_CANDIDATE_" in n]
    if len(dst.objects)!=18:raise ValueError("Expected 18 strips")
    for ob in dst.objects:
        if ob is None:raise ValueError("Missing strip")
        if not ob.users_collection:bpy.context.collection.objects.link(ob)
    lash=bpy.data.objects[NAME]
    old=lash.data
    if len(old.vertices)!=12 or len(old.polygons)!=5:raise ValueError("Unexpected original topology")
    world=[lash.matrix_world@v.co for v in old.vertices]
    # Root apex is independently constructed from the cage surface near the
    # original first section, using triangle winding, not nearest-side flip.
    root=(world[0]+world[1])*0.5
    hit,n,tri,d=cb.find_nearest(root)
    if hit is None:raise ValueError("No cage root")
    ids=ct[tri];x,y,z=(cv[i] for i in ids)
    normal=(y-x).cross(z-x).normalized()
    # Candidate apex only; no change to original section 2 onward.
    apex=hit+normal*0.00045
    # Preserve all distal sections 2..5 exactly. New apex replaces 0..3.
    verts=[lash.matrix_world.inverted()@apex]+[lash.matrix_world.inverted()@w for w in world[4:]]
    # A single triangular root face, then the original three distal quads.
    # Original section 2 is new indices 1/2, section 3 is 3/4 etc.
    faces=[(0,1,2)]+[(1+2*k,2+2*k,4+2*k,3+2*k) for k in range(3)]
    new=bpy.data.meshes.new(NAME+"_ROOT_FAN_09G")
    new.from_pydata(verts,[],faces)
    new.update()
    lash.data=new
    if old.users==0:bpy.data.meshes.remove(old)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
    report={"status":"UNAPPROVED_STRUCTURAL_ROOT_FAN_09G","source_sha256":SOURCE_SHA,
        "input_strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
        "changed_object":NAME,"old_vertices":12,"old_faces":5,
        "new_vertices":len(verts),"new_faces":len(faces),
        "apex_nearest_cage_triangle":tri,"apex_world_m":list(apex),
        "distal_sections_unchanged":True,"collision_qa":"NOT_RUN",
        "G1":"BLOCKED","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"}
    a.report.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_ROOT_FAN_09G="+json.dumps({"tri":tri,"verts":len(verts),
        "faces":len(faces),"status":report["status"]}),flush=True)
if __name__=="__main__":main()
