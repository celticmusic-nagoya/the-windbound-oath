"""Read-only targeted inspection of degenerate triangles in ART-02 Blender candidate.
blender -b candidate.blend --python tools/map_blender/aidan_art02_degenerate_inspect.py -- --out /tmp/aidan-degenerate.json
"""
import argparse,json,math,pathlib,sys
import bpy
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
p=argparse.ArgumentParser();p.add_argument("--out",required=True);p.add_argument("--object",default="stone_32_B_c4");p.add_argument("--threshold-m2",type=float,default=1e-12);a=p.parse_args(argv)
obj=bpy.data.objects.get(a.object)
if obj is None or obj.type!="MESH":raise RuntimeError("Missing mesh: "+a.object)
deps=bpy.context.evaluated_depsgraph_get()
ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
try:
    mesh.calc_loop_triangles()
    problems=[]
    for tri in mesh.loop_triangles:
        pts=[obj.matrix_world @ mesh.vertices[i].co for i in tri.vertices]
        area=(pts[1]-pts[0]).cross(pts[2]-pts[0]).length*.5
        lengths=[(pts[(j+1)%3]-pts[j]).length for j in range(3)]
        if not math.isfinite(area) or area<=a.threshold_m2 or min(lengths)<=1e-8:
            problems.append({"triangle_index":tri.index,"polygon_index":tri.polygon_index,
                             "vertex_indices":list(tri.vertices),"area_m2":area,
                             "edge_lengths_m":lengths,
                             "vertices_world_m":[[float(c) for c in v] for v in pts]})
    result={"task":"AIDAN-MASONRY-ART-02","object":a.object,
            "blend":bpy.data.filepath,"blender":bpy.app.version_string,
            "triangle_count":len(mesh.loop_triangles),"threshold_m2":a.threshold_m2,
            "degenerate_count":len(problems),"triangles":problems,
            "caveat":"Triangle inspection only; does not determine Boolean/scan/bevel causal stage or certify G3."}
finally:ev.to_mesh_clear()
out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2))
print("AIDAN_DEGENERATE_INSPECTION="+json.dumps({k:result[k] for k in ("object","triangle_count","degenerate_count")}))
