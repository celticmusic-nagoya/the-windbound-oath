"""09P first structural candidate: re-anchor root and blend clearance into first ribbon section.

No canonical edits. The 17 unrelated strips and all vertices beyond first section
are preserved. This is a geometry experiment, not an approved asset.
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
    p.add_argument("--root-clearance",type=float,default=0.0008)
    p.add_argument("--section-clearance",type=float,default=0.0004)
    a=p.parse_args()
    if a.out.exists() or a.report.exists():raise ValueError("Refuse overwrite")
    if hashlib.sha256(a.model.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError("Source model hash mismatch")
    if not (0<a.root_clearance<=0.002 and 0<=a.section_clearance<=0.002):raise ValueError("Clearance out of bounds")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    cage=bpy.data.objects[CAGE]
    mesh=cage.to_mesh()
    try:
        mesh.calc_loop_triangles()
        cv=[cage.matrix_world@v.co for v in mesh.vertices]
        ct=[tuple(t.vertices) for t in mesh.loop_triangles]
        bvh=BVHTree.FromPolygons(cv,ct,all_triangles=True)
    finally:cage.to_mesh_clear()
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith("M09_") and "_LASH_CANDIDATE_" in n]
    if len(dst.objects)!=18 or any(x is None for x in dst.objects):raise ValueError("Expected 18 strips")
    for ob in dst.objects:
        if not ob.users_collection:bpy.context.collection.objects.link(ob)
    lash=bpy.data.objects[NAME]
    old=lash.data
    if len(old.vertices)!=9 or len(old.polygons)!=4:raise ValueError("09N topology mismatch")
    oldfaces=[tuple(f.vertices) for f in old.polygons]
    if oldfaces[0]!=(0,2,1):raise ValueError("09N winding mismatch")
    original=[tuple(v.co) for v in old.vertices]
    world=[lash.matrix_world@Vector(v) for v in original]
    hit,n,tri,d=bvh.find_nearest(world[0])
    if hit is None:raise ValueError("Root cage lookup failed")
    ids=ct[tri]
    x,y,z=(cv[i] for i in ids)
    normal=(y-x).cross(z-x).normalized()
    # Resolve outward direction using the pre-existing root-to-tip trajectory.
    # Orientation is recorded, not silently assumed from global axes.
    if normal.dot(world[1]-hit)<0:normal.negate()
    newworld=list(world)
    newworld[0]=hit+normal*a.root_clearance
    # Lift only the first cross-section, keeping distal vertices 3..8 identical.
    for i in (1,2):
        near,nn,ti,dist=bvh.find_nearest(world[i])
        if near is None:raise ValueError("First-section cage lookup failed")
        aa,bb,cc=(cv[k] for k in ct[ti])
        surface=(bb-aa).cross(cc-aa).normalized()
        if surface.dot(normal)<0:surface.negate()
        signed=(world[i]-near).dot(surface)
        if signed<a.section_clearance:
            newworld[i]=world[i]+surface*(a.section_clearance-signed)
    inv=lash.matrix_world.inverted()
    newverts=[tuple(inv@v) for v in newworld]
    candidate=bpy.data.meshes.new(NAME+"_09P_CLEARANCE")
    candidate.from_pydata(newverts,[],oldfaces)
    candidate.update()
    lash.data=candidate
    if old.users==0:bpy.data.meshes.remove(old)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
    report={"status":"UNAPPROVED_09P_GEOMETRY_CANDIDATE",
      "model_sha256":SOURCE_SHA,"input_strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
      "root_clearance_m":a.root_clearance,"section_clearance_m":a.section_clearance,
      "root_cage_triangle":tri,"normal_world":list(normal),
      "modified_vertex_indices":[i for i in range(9) if (Vector(original[i])-Vector(newverts[i])).length>1e-10],
      "distal_vertices_3_to_8_preserved":all((Vector(original[i])-Vector(newverts[i])).length<1e-10 for i in range(3,9)),
      "other_17_strips_untouched":True,
      "G1":"BLOCKED","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"}
    a.report.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_BUILD_09P="+json.dumps(report),flush=True)
if __name__=="__main__":main()
