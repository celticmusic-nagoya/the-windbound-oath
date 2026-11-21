"""Matched clay frames, underside inspection, and first-hit sightline QA."""
from collections import Counter
import json
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

out=Path(sys.argv[-1])
scene=bpy.context.scene
candidate=bpy.data.objects["V3-D | integrated grassy headland and eroded bedrock"]
previous=bpy.data.objects["V3 | protected ground and reconstructed shoreline"]
author=bpy.data.objects["V3-D authored | continuous cliffs"]
assert not [img.name for img in bpy.data.images if img.source=="FILE" and img.users and not img.packed_file]
scene.render.resolution_percentage=55
scene.cycles.samples=8
scene.cycles.use_denoising=True
neutral=bpy.data.materials.new("V3-D view only | neutral clay")
neutral.diffuse_color=(.58,.58,.58,1)
for layer in scene.view_layers:
    layer.material_override=neutral
sunset=bpy.data.objects["Sunset study"]
for label,name in [("sunset","Sunset study"),("front","front"),("side","right"),("overhead","elevated")]:
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(out/f"clay-{label}.png")
    bpy.ops.render.render(write_still=True)
scene.camera=sunset

# First-hit labels use the actual cut geometry rather than projection bounding boxes.
for layer in scene.view_layers:
    layer.material_override=None
frame=sunset.data.view_frame(scene=scene)
origin=sunset.matrix_world.translation
rot=sunset.matrix_world.to_3x3()
dg=bpy.context.evaluated_depsgraph_get()
xmin,xmax=min(v.x for v in frame),max(v.x for v in frame)
ymin,ymax=min(v.y for v in frame),max(v.y for v in frame)
w,h=418,235
palette={"main":(.29,.77,.91),"first_shoulder":(.98,.62,.25),
         "incision":(.61,.47,.81),"second_shoulder":(.93,.37,.58),"skerry":(.54,.77,.37)}
counts=Counter()
low=Counter()
pixels=[]
depth=[]
for row in range(h):
    for col in range(w):
        x=xmin+(xmax-xmin)*(col+.5)/w
        y=ymin+(ymax-ymin)*(row+.5)/h
        ray=(rot @ Vector((x,y,frame[0].z))).normalized()
        hit,p,_,face,obj,_=scene.ray_cast(dg,origin,ray)
        label=None
        if hit and face>=0 and obj==candidate:
            mat=obj.data.materials[obj.data.polygons[face].material_index]
            if mat and mat.name.startswith("V3-D clay") and not mat.name.endswith(("turf","underside")):
                label="main" if p.x<1.7 else "first_shoulder" if p.x<4.55 else "incision" if p.x<5.75 else "second_shoulder"
        elif hit and obj.name.startswith("V3-D | detached skerry"):
            label="skerry"
        if label:
            counts[label]+=1
            low[label]+=p.z<=4.8
            pixels.extend((*palette[label],1))
            d=min(1.0,(p-origin).length/46)
            depth.extend((d,d,d,1))
        else:
            pixels.extend((.07,.085,.105,1))
            depth.extend((0,0,0,1))
for label,array in [("visible-ids",pixels),("visible-depth",depth)]:
    img=bpy.data.images.new(label,width=w,height=h)
    img.pixels.foreach_set(array)
    img.filepath_raw=str(out/f"{label}.png")
    img.file_format="PNG"
    img.save()

# Verify why the second shoulder, when hidden, is unavailable in the fixed view.
author.data.calc_loop_triangles()
blockers=Counter()
samples=[]
for tri in author.data.loop_triangles:
    p=sum((author.data.vertices[i].co for i in tri.vertices),Vector())/3
    r=p-origin
    if p.x<5.75 or not .15<p.z<4.8 or tri.normal.dot(r)>=0:
        continue
    uv=world_to_camera_view(scene,sunset,p)
    if not (0<uv.x<1 and 0<uv.y<1):
        continue
    hit,loc,_,face,obj,_=scene.ray_cast(dg,origin,r.normalized(),distance=r.length-.035)
    if hit and obj.type=="MESH":
        mat=obj.data.materials[obj.data.polygons[face].material_index] if face>=0 else None
        key=mat.name if mat else obj.name
        blockers[key]+=1
        if len(samples)<350:
            samples.append({"target_BU":list(p),"blocking_point_BU":list(loc),"material_or_object":key})
(out/"visibility.json").write_text(json.dumps({
    "camera":sunset.name,"raster_px":[w,h],"depth_value":"distance/46 BU",
    "visible_pixels":dict(counts),"visible_z_le_4_8_BU":dict(low),
    "second_shoulder_occluder_counts":dict(blockers),"second_shoulder_ray_samples":samples,
},indent=2)+"\n")

# Only the actual bedrock is shown in the matched underside pair; sea/foliage
# would hide the lower caps and create false black shapes in this diagnostic.
bpy.ops.object.camera_add(location=(-16,-27,-10))
under=bpy.context.object
under.name="V3-D diagnostic underside"
under.rotation_euler=(Vector((.5,-10,-.65))-under.location).to_track_quat("-Z","Y").to_euler()
under.data.lens=41
scene.camera=under
for node in scene.objects:
    if node.type=="MESH":
        node.hide_render=True
bpy.ops.object.light_add(type="AREA",location=(-6,-16,-11))
light=bpy.context.object
light.rotation_euler=(Vector((.3,-10,0))-light.location).to_track_quat("-Z","Y").to_euler()
light.data.energy=1800
light.data.shape="DISK"
light.data.size=14
for layer in scene.view_layers:
    layer.material_override=neutral
for suffix,node in [("previous",previous),("candidate",candidate)]:
    node.hide_render=False
    scene.render.filepath=str(out/f"underside-{suffix}.png")
    bpy.ops.render.render(write_still=True)
    node.hide_render=True
