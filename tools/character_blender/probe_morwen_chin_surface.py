#!/usr/bin/env python3
"""Probe true mesh surface at head/neck scanlines in front and side views.
No automatic anatomical classification or modification of source.
"""
import argparse,hashlib,json,pathlib
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
NAME="GEO-body_female_realistic"
ROWS=(132,136,140,144,148,152,156,160)
VIEWS={"front":(0,-1,0),"left":(-1,0,0),"right":(1,0,0)}
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 src=pathlib.Path(a.source).resolve();dest=pathlib.Path(a.output).resolve()
 if not src.is_file() or src==dest:raise SystemExit("BLOCKED missing/unsafe source")
 digest=sha(src);bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 ob=bpy.data.objects.get(NAME)
 if ob is None or ob.type!="MESH":raise SystemExit("BLOCKED missing realistic mesh")
 coords=[ob.matrix_world@v.co for v in ob.data.vertices]
 lo=Vector(tuple(min(v[i] for v in coords) for i in range(3)));hi=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
 center=(lo+hi)*.5;dist=max(hi-lo)*3
 ob.data.calc_loop_triangles()
 tree=BVHTree.FromPolygons(coords,[tuple(t.vertices) for t in ob.data.loop_triangles],all_triangles=True)
 result={"status":"SURFACE_CROSSVIEW_EVIDENCE_ONLY","source_sha256":digest,"mesh":NAME,"resolution":[512,768],"ortho_scale":2.05,"reviewer_confirmed":False,"anatomical_chin":"BLOCKED","views":{}}
 for view,direction in VIEWS.items():
  camera=center+Vector(direction)*dist;rotation=(center-camera).to_track_quat("-Z","Y")
  right=rotation@Vector((1,0,0));up=rotation@Vector((0,1,0));forward=rotation@Vector((0,0,-1))
  scan=[]
  for y in ROWS:
   hits=[]
   for x in range(196,317,4):
    origin=camera+right*((x+.5-256)*2.05/768)+up*((384-y-.5)*2.05/768)
    hit,normal,tri,distance=tree.ray_cast(origin,forward,dist*3)
    if hit is not None:hits.append({"pixel":[x,y],"world_xyz":[round(float(v),6) for v in hit],"triangle_index":int(tri)})
   scan.append({"row":y,"world_z":round(float(center.z+(384-y-.5)*2.05/768),6),"hits":hits,"hit_count":len(hits)})
  result["views"][view]=scan
 if sha(src)!=digest:raise SystemExit("FAIL source changed")
 result["source_unchanged"]=True
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({"status":result["status"],"views":len(result["views"]),"rows":len(ROWS)}))
if __name__=="__main__":main()
