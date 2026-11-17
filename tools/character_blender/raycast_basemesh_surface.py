#!/usr/bin/env python3
"""Orthographic pixel-to-triangle raycast evidence; no inferred anatomy."""
import argparse,hashlib,json,pathlib
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

NAMES=("GEO-body_female_stylized","GEO-body_female_realistic")
VIEWS={"front":(0,-1,0),"back":(0,1,0),"left":(-1,0,0),"right":(1,0,0)}
WIDTH,HEIGHT,SCALE=512,768,2.05

def raycast(ob,view,pixels):
    coords=[ob.matrix_world@v.co for v in ob.data.vertices]
    lo=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    hi=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    center=(lo+hi)*0.5
    size=hi-lo
    dist=max(size)*3
    camera=center+Vector(VIEWS[view])*dist
    rotation=(center-camera).to_track_quat("-Z","Y")
    right=rotation@Vector((1,0,0))
    up=rotation@Vector((0,1,0))
    forward=rotation@Vector((0,0,-1))
    # BVH in world space; transform vertices rather than relying on object.ray_cast local coordinates.
    triangles=[]
    ob.data.calc_loop_triangles()
    for tri in ob.data.loop_triangles:triangles.append(tuple(tri.vertices))
    tree=BVHTree.FromPolygons(coords,triangles,all_triangles=True)
    hits=[]
    for px,py in pixels:
        origin=camera+right*((px+0.5-WIDTH/2)*SCALE/HEIGHT)+up*((HEIGHT/2-py-0.5)*SCALE/HEIGHT)
        hit,normal,index,distance=tree.ray_cast(origin,forward,dist*3)
        hits.append({"pixel":[px,py],"hit":hit is not None,
            "world_xyz":[round(float(v),6) for v in hit] if hit is not None else None,
            "triangle_index":int(index) if index is not None else None,
            "distance":round(float(distance),6) if distance is not None else None})
    return {"object":ob.name,"view":view,"bounds_z":[round(lo.z,6),round(hi.z,6)],
        "camera":{"resolution":[WIDTH,HEIGHT],"ortho_scale":SCALE,
                  "position":[round(v,6) for v in camera],
                  "ray_direction":[round(v,6) for v in forward]},
        "samples":hits}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--contours")
    a=p.parse_args()
    src=pathlib.Path(a.source).resolve();out=pathlib.Path(a.output).resolve()
    if not src.is_file() or src==out:raise SystemExit("BLOCKED invalid paths")
    sha=hashlib.sha256(src.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
    result={"status":"PASS_RAYCAST_EVIDENCE_ONLY","source_sha256":sha,
        "method":"BVH world-space raycast through orthographic pixel centers",
        "landmark_identification":"BLOCKED","reviewer_confirmed":False,"views":[]}
    # A small fixed diagnostic grid across upper portion of frame; points are not anatomy labels.
    pixels=[(x,y) for y in (80,120,160,200,240) for x in (192,256,320)]
    contour_data=json.loads(pathlib.Path(a.contours).read_text()) if a.contours else None
    if contour_data and (contour_data.get("status")!="PASS_RENDER_CONTOUR_CANDIDATES_ONLY" or contour_data.get("reviewer_confirmed") is not False):
        raise SystemExit("BLOCKED invalid contour candidate input")
    for name in NAMES:
        ob=bpy.data.objects.get(name)
        if ob is None or ob.type!="MESH":raise SystemExit("BLOCKED missing mesh "+name)
        for view in VIEWS:
            chosen=next((v for v in contour_data["views"] if v["object"]==name and v["view"]==view),None) if contour_data else None
            if contour_data and chosen is None:raise SystemExit("BLOCKED contour view missing")
            points=[s["pixel"] for s in chosen["samples"]] if chosen else pixels
            view_result=raycast(ob,view,points)
            view_result["sample_source"]="render_alpha_contour" if chosen else "fixed_diagnostic_grid"
            result["views"].append(view_result)
    result["source_unchanged"]=hashlib.sha256(src.read_bytes()).hexdigest()==sha
    if not result["source_unchanged"]:raise SystemExit("FAIL source modified")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"views":len(result["views"]),
        "hits":sum(sum(s["hit"] for s in v["samples"]) for v in result["views"])}))
if __name__=="__main__":main()
