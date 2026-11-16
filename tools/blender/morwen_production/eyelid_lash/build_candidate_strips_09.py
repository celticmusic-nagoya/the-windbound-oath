"""Create independent EYELID-09 candidate lash strips; never modify saved source."""
import argparse,json,math
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--anchors",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    d=json.loads(a.anchors.read_text())
    if d.get("status")!="UNAPPROVED_ANCHOR_CANDIDATES":raise ValueError("Unverified roots")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    result={"status":"CANDIDATE_GEOMETRY_ONLY","art_qa":"NOT_RUN",
        "collision_qa":"NOT_RUN","canonical_approval":"BLOCKED","objects":[]}
    for side in ("R","L"):
        roots=d["sides"][side]
        for j,root in enumerate(roots):
            p0=Vector(root["root_world_m"])
            normal=Vector(root["normal_world"]).normalized()
            # World up is a temporary scaffold direction, not artist-approved lash flow.
            forward=Vector((0,0,1))
            lateral=normal.cross(forward)
            if lateral.length<1e-6:lateral=Vector((1,0,0))
            lateral.normalize()
            verts=[]
            for i in range(6):
                t=i/5
                center=p0+forward*(0.0028*t)+normal*(0.00015+0.0005*t*t)
                half=0.00034*max(0.02,(1-t)**1.3)
                verts.extend([center-lateral*half,center+lateral*half])
            faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(5)]
            name=f"M09_{side}_LASH_CANDIDATE_{j:02d}"
            mesh=bpy.data.meshes.new(name+"_mesh")
            mesh.from_pydata(verts,[],faces)
            mesh.update()
            ob=bpy.data.objects.new(name,mesh)
            bpy.context.collection.objects.link(ob)
            if len(mesh.vertices)!=12 or len(mesh.polygons)!=5:raise ValueError("Invalid strip")
            result["objects"].append({"name":name,"vertices":12,"faces":5,
                "source_margin_index":root["margin_index"]})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    # A disposable, isolated candidate .blend; no protected model is loaded or saved.
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
    print("EYELID09_LASH_CANDIDATE="+json.dumps({"count":len(result["objects"]),
        "vertices":sum(x["vertices"] for x in result["objects"]),
        "faces":sum(x["faces"] for x in result["objects"]),
        "status":result["status"]},sort_keys=True))
if __name__=="__main__":main()
