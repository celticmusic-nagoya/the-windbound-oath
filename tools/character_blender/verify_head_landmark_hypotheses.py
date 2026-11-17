#!/usr/bin/env python3
"""Audit unreviewed head/chin pixel hypotheses across orthographic views.

This does not identify anatomy automatically or approve the head ratio.
"""
import argparse,hashlib,json,pathlib
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from raycast_basemesh_surface import VIEWS,WIDTH,HEIGHT,SCALE

TARGET="GEO-body_female_realistic"
HYPOTHESES={"head_top":77,"chin":160}
def main():
    p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--manifest",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();src=pathlib.Path(a.source).resolve();manifest=pathlib.Path(a.manifest).resolve();out=pathlib.Path(a.output).resolve()
    if not src.is_file() or not manifest.is_file() or src==out:raise SystemExit("BLOCKED missing source or manifest")
    source_sha=hashlib.sha256(src.read_bytes()).hexdigest()
    entries=json.loads(manifest.read_text())["views"]
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
    ob=bpy.data.objects.get(TARGET)
    if ob is None or ob.type!="MESH":raise SystemExit("BLOCKED missing realistic mesh")
    coords=[ob.matrix_world@v.co for v in ob.data.vertices]
    lo=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    hi=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    center=(lo+hi)*0.5;dist=max(hi-lo)*3
    ob.data.calc_loop_triangles()
    tree=BVHTree.FromPolygons(coords,[tuple(t.vertices) for t in ob.data.loop_triangles],all_triangles=True)
    report={"status":"CANDIDATE_CROSSVIEW_GEOMETRY_ONLY","source_sha256":source_sha,
            "hypotheses_pixels":HYPOTHESES,"anatomical_qa":"BLOCKED","reviewer_confirmed":False,"views":[]}
    for view,direction in VIEWS.items():
        entry=next((e for e in entries if e["object"]==TARGET and e["view"]==view),None)
        if entry is None:raise SystemExit("BLOCKED missing render "+view)
        img=manifest.parent/entry["file"]
        if hashlib.sha256(img.read_bytes()).hexdigest()!=entry["sha256"]:raise SystemExit("FAIL render hash mismatch")
        camera=center+Vector(direction)*dist
        rot=(center-camera).to_track_quat("-Z","Y")
        right=rot@Vector((1,0,0));up=rot@Vector((0,1,0));forward=rot@Vector((0,0,-1))
        view_data={"view":view,"image_sha256":entry["sha256"],"hypotheses":{}}
        for name,y in HYPOTHESES.items():
            samples=[]
            for x in range(160,353,8):
                origin=camera+right*((x+0.5-WIDTH/2)*SCALE/HEIGHT)+up*((HEIGHT/2-y-0.5)*SCALE/HEIGHT)
                hit,normal,idx,distance=tree.ray_cast(origin,forward,dist*3)
                if hit is not None:samples.append({"pixel":[x,y],"xyz":[round(float(v),6) for v in hit]})
            view_data["hypotheses"][name]={"scanline_y":y,"hit_count":len(samples),"samples":samples}
        report["views"].append(view_data)
    report["source_unchanged"]=hashlib.sha256(src.read_bytes()).hexdigest()==source_sha
    if not report["source_unchanged"]:raise SystemExit("FAIL original changed")
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"hit_counts":{v["view"]:{k:h["hit_count"] for k,h in v["hypotheses"].items()} for v in report["views"]}}))
if __name__=="__main__":main()
