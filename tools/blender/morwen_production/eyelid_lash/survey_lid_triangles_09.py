"""EYELID-09 read-only candidate triangle survey. Geometry sampling is not art approval."""
import argparse,hashlib,json,math
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse to overwrite evidence")
    digest=hashlib.sha256(a.candidate.read_bytes()).hexdigest()
    if digest!="9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4":
        raise ValueError("Unexpected saved EYELID-08 candidate")
    bpy.ops.wm.open_mainfile(filepath=str(a.candidate.resolve()))
    report={"candidate_sha256":digest,"status":"SURVEY_ONLY","anchor_approval":"BLOCKED",
            "lash_mesh_generated":False,"collision_qa":"NOT_RUN","eyes":{}}
    for side in ("R","L"):
        obj=bpy.data.objects[f"M08_{side}_CONTACT_CAGE_050"]
        mesh=obj.data
        mesh.calc_loop_triangles()
        world=obj.matrix_world
        entries=[]
        for tri in mesh.loop_triangles:
            pts=[world@mesh.vertices[i].co for i in tri.vertices]
            n=(pts[1]-pts[0]).cross(pts[2]-pts[0])
            area=n.length/2
            if area<1e-12:continue
            n.normalize()
            center=sum(pts,Vector())/3
            if n.y<0.25:continue
            entries.append({"triangle_vertices":list(tri.vertices),"center_world_m":list(center),
                "normal_world":list(n),"area_m2":area})
        entries.sort(key=lambda x:x["center_world_m"][2],reverse=True)
        if not entries:raise ValueError("No anterior candidate triangles: "+side)
        zmax=entries[0]["center_world_m"][2]
        # Top band is merely a survey region, NOT a confirmed upper lash line.
        band=[x for x in entries if x["center_world_m"][2]>=zmax-.004]
        band.sort(key=lambda x:x["center_world_m"][0])
        stride=max(1,len(band)//10)
        sampled=band[::stride][:11]
        report["eyes"][side]={"anterior_triangle_count":len(entries),
            "top_band_4mm_count":len(band),"top_band_sample":sampled,
            "warning":"Top-of-mesh triangles are NOT verified anatomical upper lid margins"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("EYELID09_SURVEY_JSON="+json.dumps({"status":report["status"],
        "counts":{s:{"anterior":x["anterior_triangle_count"],"top_band":x["top_band_4mm_count"],
        "sampled":len(x["top_band_sample"])} for s,x in report["eyes"].items()}},sort_keys=True))
if __name__=="__main__":main()
