"""09N structural winding repair candidate, preserving all vertex coordinates.

09M measured a 165-degree normal angle: root (0,1,2) and next quad
(1,2,4,3) traverse shared edge 1->2 in the same direction.
Reverse only the root triangle, then independently re-run topology and BVH QA.
"""
import argparse,hashlib,json
from pathlib import Path
import bpy
NAME="M09_L_LASH_CANDIDATE_00"
def main():
    p=argparse.ArgumentParser()
    for key in ("strips","out","report"):p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists() or a.report.exists():raise ValueError("Refuse overwrite")
    bpy.ops.wm.open_mainfile(filepath=str(a.strips.resolve()))
    ob=bpy.data.objects[NAME]
    old=ob.data
    if len(old.vertices)!=9 or len(old.polygons)!=4:raise ValueError("09G topology mismatch")
    faces=[tuple(f.vertices) for f in old.polygons]
    if faces[0]!=(0,1,2) or faces[1]!=(1,2,4,3):raise ValueError("Unexpected root winding")
    verts=[tuple(v.co) for v in old.vertices]
    faces[0]=(0,2,1)
    mesh=bpy.data.meshes.new(NAME+"_WINDING_09N")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    ob.data=mesh
    if old.users==0:bpy.data.meshes.remove(old)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
    report={"status":"UNAPPROVED_WINDING_REPAIR_09N",
      "input_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
      "changed_object":NAME,"changed_face":0,"before":[0,1,2],"after":[0,2,1],
      "all_vertices_unchanged":True,"other_17_objects_unchanged":True,
      "G1":"BLOCKED","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"}
    a.report.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_WINDING_REPAIR_09N="+json.dumps(report),flush=True)
if __name__=="__main__":main()
