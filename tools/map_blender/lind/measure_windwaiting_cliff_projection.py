"""Measure the first visible headland rock surface at fixed sunset pixel rays."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def image_rows(scene, target_name, reference_size):
    cam=bpy.data.objects["Sunset study"]
    depsgraph=bpy.context.evaluated_depsgraph_get()
    frame=cam.data.view_frame(scene=scene)
    origin=cam.matrix_world.translation
    xf,yf=map(min,([v.x for v in frame],[v.y for v in frame]))
    xp,yp=map(max,([v.x for v in frame],[v.y for v in frame]))
    z=frame[0].z
    width,height=reference_size
    result=[]
    for y in range(height):
        row=[]
        sy=yp-(yp-yf)*(y+.5)/height
        for x in range(width):
            sx=xf+(xp-xf)*(x+.5)/width
            direction=cam.matrix_world.to_3x3()@Vector((sx,sy,z))
            hit,_,_,index,obj,_=scene.ray_cast(depsgraph,origin,direction.normalized())
            if hit and obj.name==target_name and index>=0:
                material=obj.data.materials[obj.data.polygons[index].material_index]
                if material and material.name.startswith("Headland rock"):
                    row.append(x)
        spans=[]
        for x in row:
            if spans and x==spans[-1][1]+1:
                spans[-1][1]=x
            else:
                spans.append([x,x])
        if spans:
            result.append({"y":y,"inclusive_x_spans":spans})
    return result


def main():
    paths=list(map(Path,sys.argv[sys.argv.index("--")+1:]))
    reference_size=(418,235)
    records={}
    for path,key,target in zip(paths[:2],("previous","current"),(
        "Rebuilt headland | promontory, rock shoulders, gully",
        "Sunset headland | integrated bedrock and meadow",
    ),strict=True):
        bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
        rows=image_rows(bpy.context.scene,target,reference_size)
        records[key]={"rows":rows,"first_hit_pixels":sum(b-a+1 for row in rows for a,b in row["inclusive_x_spans"])}
    paths[2].write_text(json.dumps({
        "image_size_px":reference_size,
        "method":"first hit evaluated scene ray; authored Headland rock material only; fixed camera",
        "comparison_scope":"CG tracing covers manually labeled rock; image percentages give composition scale, not a registered IoU",
        "captures":records
    },indent=2)+"\n")


if __name__=="__main__":
    main()
