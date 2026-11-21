"""Render the saved V3 clay and derive material-ID masks at the same camera."""
import json
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.kdtree import KDTree

out=Path(sys.argv[-1])
scene=bpy.context.scene
scene.render.resolution_percentage=55
scene.cycles.samples=8
scene.cycles.use_denoising=True
camera=bpy.data.objects["Sunset study"]
for label,name in [("sunset","Sunset study"),("front","front"),("overhead","elevated"),("side","right")]:
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(out/f"clay-{label}.png")
    neutral=bpy.data.materials.get("QA neutral geometry")
    if neutral is None:
        neutral=bpy.data.materials.new("QA neutral geometry")
        neutral.diffuse_color=(.57,.57,.57,1)
    for layer in scene.view_layers:
        layer.material_override=neutral
    bpy.ops.render.render(write_still=True)
scene.camera=camera
for layer in scene.view_layers:
    layer.material_override=None
# Orthogonal colors identify named components carried through the exact union.
colors={"main":(.28,.80,1.0),"shoulder-a":(1.0,.60,.20),
        "shoulder-b":(.96,.38,.62),"tidal-root":(.65,.86,.33),"landward-tie":(.71,.64,.47)}
width,height=418,235
image=bpy.data.images.new("V3 ID visibility",width=width,height=height)
depth=bpy.data.images.new("V3 ID depth",width=width,height=height)
fx=camera.data.view_frame(scene=scene)
xmin,xmax=min(x.x for x in fx),max(x.x for x in fx)
ymin,ymax=min(x.y for x in fx),max(x.y for x in fx)
origin=camera.matrix_world.translation
a=camera.matrix_world.to_3x3()
dg=bpy.context.evaluated_depsgraph_get()
mask,depth_pixels=[],[]
counts={k:0 for k in colors}
below=counts.copy()
extents={k:[] for k in colors}
for row in range(height):
    for col in range(width):
        xy=(xmin+(xmax-xmin)*(col+.5)/width,ymin+(ymax-ymin)*(row+.5)/height)
        direction=(a@Vector((*xy,fx[0].z))).normalized()
        hit,p,_,face,obj,_=scene.ray_cast(dg,origin,direction)
        tag=None
        if hit and face>=0 and obj.type=="MESH" and obj.name.startswith("V3 | protected"):
            material=obj.data.materials[obj.data.polygons[face].material_index]
            if material and material.name.startswith("V3 clay | "):
                tag=material.name.split(" | ",1)[1]
        if tag in counts:
            counts[tag]+=1
            below[tag]+=p.z<=4.8
            extents[tag].append([col,height-1-row])
            mask.extend((*colors[tag],1))
            d=min(1,(p-origin).length/44)
            depth_pixels.extend((d,d,d,1))
        else:
            mask.extend((.075,.092,.12,1))
            depth_pixels.extend((0,0,0,1))
for img,pixels,name in [(image,mask,"visible-ids.png"),(depth,depth_pixels,"visible-depth.png")]:
    img.pixels.foreach_set(pixels)
    img.filepath_raw=str(out/name)
    img.file_format="PNG"
    img.save()
base=Path(__file__).resolve().parents[3]/"assets/candidates/lind/windwaiting-cliff-playable"
nav=json.loads((base/"navigation.json").read_text())
supported=[(nav["origin"][0]+i%nav["width"]*nav["stride"],
            -(nav["origin"][1]+i//nav["width"]*nav["stride"]),0)
           for i,z in enumerate(nav["levels"]) if z is not None]
tree=KDTree(len(supported))
for i,xy in enumerate(supported):
    tree.insert(xy,i)
tree.balance()
blocked=[]
for obj in bpy.data.objects:
    if not obj.name.startswith("V3 authored") or obj.name.endswith("root"):
        continue
    obj.data.calc_loop_triangles()
    for t in obj.data.loop_triangles:
        p=sum((obj.data.vertices[i].co for i in t.vertices),Vector())/3
        if not 1<p.z<5.3:
            continue
        ray=p-origin
        view=world_to_camera_view(scene,camera,p)
        if not (.33<view.x<.95 and .1<view.y<.72 and t.normal.dot(ray)<0):
            continue
        if ray.length<=.04:
            continue
        hit,where,_,idx,blocker,_=scene.ray_cast(dg,origin,ray.normalized(),distance=ray.length-.04)
        if hit and idx>=0 and blocker.type=="MESH":
            mat=blocker.data.materials[blocker.data.polygons[idx].material_index]
            blocked.append({"target":obj.name,"target_BU":list(p),"first_hit_BU":list(where),
                            "material":mat.name if mat else None,
                            "nearest_supported_xy_BU":tree.find((where.x,where.y,0))[2]})
out.joinpath("visibility.json").write_text(json.dumps({
    "occluder_samples":blocked,
    "raster_px":[width,height],"camera":camera.name,"depth_mask":"gray encodes Euclidean camera ray distance / 44 BU",
    "parts":{k:{"visible_pixels":counts[k],"visible_z_le_4_8_BU":below[k],
                "bbox_xy_px":[[min(p[i] for p in extents[k]),max(p[i] for p in extents[k])] for i in range(2)]
                              if extents[k] else None} for k in counts},
},indent=2)+"\n")
