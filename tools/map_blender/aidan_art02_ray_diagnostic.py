"""Targeted Blender BVH diagnosis of ART-02 arris misses.
Usage:
 blender -b candidate_a/aidan_scan_carved_corner_v1.blend --python tools/map_blender/aidan_art02_ray_diagnostic.py -- --manifest candidate_a/aidan_scan_carved_corner_v1_manifest.json --out /tmp/aidan-rays.json
Read-only: never saves .blend or modifies canonical source files.
"""
import argparse,json,sys,pathlib
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argsv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
p=argparse.ArgumentParser();p.add_argument("--manifest",required=True);p.add_argument("--out",required=True);args=p.parse_args(argsv)
m=json.loads(pathlib.Path(args.manifest).read_text())
objects=[o for o in bpy.data.objects if o.type=="MESH" and (o.name.startswith("stone_") or o.name=="mortar_matrix")]
assert objects,"No stone_/mortar_matrix objects in opened blend"
deps=bpy.context.evaluated_depsgraph_get()
trees=[(o.name,BVHTree.FromObject(o,deps)) for o in objects]
T=float(m["params"]["T"])
records=[]
for face,a,z in m["qa"]["see_through_rays"]["miss_points"]:
    origin=Vector((a,-.5,z)) if face=="y" else Vector((-.5,a,z))
    direction=Vector((0,1,0)) if face=="y" else Vector((1,0,0))
    hits=[]
    for name,tree in trees:
        loc,normal,face_id,distance=tree.ray_cast(origin,direction,.5+T+.2)
        if loc is not None:
            hits.append({"object":name,"distance_m":round(distance,6),
                         "location":[round(v,6) for v in loc],
                         "normal":[round(v,6) for v in normal],"face_id":face_id})
    hits.sort(key=lambda h:h["distance_m"])
    records.append({"axis":face,"arris_offset_m":a,"z_m":z,"hits":hits,
                    "hit_any":bool(hits),"nearest_hit_m":hits[0]["distance_m"] if hits else None})
out={"task":"AIDAN-MASONRY-ART-02","source_blend":bpy.data.filepath,
     "blender":bpy.app.version_string,"objects_tested":len(objects),
     "tested_rays":len(records),"hit_any_count":sum(x["hit_any"] for x in records),
     "no_hit_count":sum(not x["hit_any"] for x in records),
     "rays":records,
     "limitations":"Only evaluates the 95 manifest rays, with a slightly extended distance; this does not backproject dark image pixels or certify G2."}
dest=pathlib.Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(out,indent=2))
print("AIDAN_ART02_RAY_DIAGNOSTIC="+json.dumps({k:out[k] for k in ("tested_rays","hit_any_count","no_hit_count")}))
