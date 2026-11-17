#!/usr/bin/env python3
"""Non-destructive cross-sectional head-region hypothesis from Blender mesh vertices.

This produces unlabeled cross-section evidence, NOT an anatomical chin or approved head count.
"""
import argparse,hashlib,json,math,pathlib
import bpy
from mathutils import Vector
NAMES=("GEO-body_female_stylized","GEO-body_female_realistic")
def inspect(ob,sections=80):
    coords=[ob.matrix_world@v.co for v in ob.data.vertices]
    zmin=min(v.z for v in coords);zmax=max(v.z for v in coords)
    span=zmax-zmin
    if span<=0:raise ValueError("degenerate mesh")
    bands=[]
    for i in range(sections):
        lo=zmin+span*i/sections;hi=zmin+span*(i+1)/sections
        points=[v for v in coords if (lo<=v.z<hi or (i==sections-1 and v.z==hi))]
        if points:
            xs=[v.x for v in points];ys=[v.y for v in points]
            bands.append({"index":i,"z_mid":round((lo+hi)/2,6),"vertex_count":len(points),
                "x_span":round(max(xs)-min(xs),6),"y_span":round(max(ys)-min(ys),6),
                "x_center":round((max(xs)+min(xs))/2,6),
                "y_center":round((max(ys)+min(ys))/2,6)})
        else:bands.append({"index":i,"z_mid":round((lo+hi)/2,6),"vertex_count":0,
                           "x_span":None,"y_span":None,"x_center":None,"y_center":None})
    # Sampled vertices can be sparse or contain multiple limbs. Do not infer anatomy automatically.
    return {"bounds_z":[round(zmin,6),round(zmax,6)],"section_count":sections,
            "sampling_method":"vertex occupancy in uniform world-Z bands (NOT true surface intersection)",
            "sections":bands,"head_top":None,"chin":None,
            "head_count":"BLOCKED_REVIEW_REQUIRED","reviewer_confirmed":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--source",required=True)
    p.add_argument("--output",required=True);p.add_argument("--sections",type=int,default=80)
    a=p.parse_args();src=pathlib.Path(a.source).resolve();out=pathlib.Path(a.output).resolve()
    if not src.is_file() or src.is_relative_to(out) or out.is_relative_to(src) or not 40<=a.sections<=200:
        raise SystemExit("BLOCKED invalid arguments")
    sha=hashlib.sha256(src.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
    result={"status":"PASS_SECTION_EVIDENCE_ONLY","source_sha256":sha,
            "anatomical_qa":"BLOCKED","art_qa":"NOT_RUN","models":{}}
    for name in NAMES:
        ob=bpy.data.objects.get(name)
        if ob is None or ob.type!="MESH":raise SystemExit("BLOCKED source object missing "+name)
        result["models"][name]=inspect(ob,a.sections)
    result["source_unchanged"]=hashlib.sha256(src.read_bytes()).hexdigest()==sha
    if not result["source_unchanged"]:raise SystemExit("FAIL source modified")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"models":list(result["models"])}))
if __name__=="__main__":main()
