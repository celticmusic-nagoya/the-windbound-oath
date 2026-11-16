#!/usr/bin/env python3
"""Export reproducible vertex evidence for HUMAN review; never auto-approve anatomy."""
import argparse,hashlib,json,pathlib
import bpy
from mathutils import Vector
NAMES=("GEO-body_female_stylized","GEO-body_female_realistic")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--output",required=True)
    args=p.parse_args();src=pathlib.Path(args.source).resolve();out=pathlib.Path(args.output).resolve()
    if not src.is_file() or src.is_relative_to(out) or out.is_relative_to(src):
        raise SystemExit("BLOCKED invalid source/output paths")
    sha=hashlib.sha256(src.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
    result={"status":"PASS_GEOMETRY_EVIDENCE_ONLY","source_sha256":sha,
            "landmark_review":"BLOCKED","reviewer_confirmed":False,"models":{}}
    for name in NAMES:
        ob=bpy.data.objects.get(name)
        if ob is None or ob.type!="MESH":raise SystemExit("BLOCKED missing source "+name)
        if not ob.data.vertices:raise SystemExit("BLOCKED empty mesh "+name)
        mat=ob.matrix_world
        coords=[mat@v.co for v in ob.data.vertices]
        low=[min(c[i] for c in coords) for i in range(3)]
        high=[max(c[i] for c in coords) for i in range(3)]
        # Select nearby source vertices by relative height, without calling them anatomical landmarks.
        bands={}
        for fraction in (0.0,0.05,0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,0.95,1.0):
            z=low[2]+(high[2]-low[2])*fraction
            chosen=sorted(range(len(coords)),key=lambda i:(abs(coords[i].z-z),i))[:12]
            bands[f"{fraction:.2f}"]={"target_z":round(z,6),
                "vertices":[{"index":i,"world_xyz":[round(coords[i][axis],6) for axis in range(3)]} for i in chosen]}
        result["models"][name]={"object_matrix_world":[[round(float(v),8) for v in row] for row in mat],
            "vertex_count":len(coords),"bounds_world_xyz":{"min":low,"max":high},
            "horizontal_sampling_bands_NOT_anatomical_landmarks":bands,
            "head_top":None,"chin":None,"shoulder":None,"waist":None,
            "hip":None,"crotch":None,"knee":None,"ankle":None,"sole":None}
    result["source_unchanged"]=hashlib.sha256(src.read_bytes()).hexdigest()==sha
    if not result["source_unchanged"]:raise SystemExit("FAIL source modified")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"objects":len(result["models"]),"source_unchanged":True}))
if __name__=="__main__":main()
