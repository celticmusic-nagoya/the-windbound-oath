"""Render saved V4 clay checkpoints with held cameras and first-hit sightline QA."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def make_camera(name,location,target,ortho):
    bpy.ops.object.camera_add(location=location)
    cam=bpy.context.object
    cam.name=name
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO"
    cam.data.ortho_scale=ortho
    return cam


def first_hit(scene, camera, out):
    graph=bpy.context.evaluated_depsgraph_get()
    frame=camera.data.view_frame(scene=scene)
    origin=camera.matrix_world.translation
    rot=camera.matrix_world.to_3x3()
    xmin,xmax=min(v.x for v in frame),max(v.x for v in frame)
    ymin,ymax=min(v.y for v in frame),max(v.y for v in frame)
    w,h=418,235
    counts=Counter()
    lower=Counter()
    blockers=Counter()
    study=next(obj for obj in scene.objects if obj.name.startswith("V4 | sea-axis"))
    mesh=study.data
    rock_faces=[
        list(face.vertices) for face in mesh.polygons
        if mesh.materials[face.material_index].name.startswith("V4 gray")
        and not mesh.materials[face.material_index].name.endswith(("cap","heel"))
    ]
    exposed_proxy=BVHTree.FromPolygons([study.matrix_world @ v.co for v in mesh.vertices],rock_faces)
    pix=[]
    palette={"main":(.29,.77,.91),"first_shoulder":(.98,.62,.25),
             "incision":(.61,.47,.81),"second_shoulder":(.93,.37,.58)}
    for row in range(h):
        for col in range(w):
            px=xmin+(xmax-xmin)*(col+.5)/w
            py=ymin+(ymax-ymin)*(row+.5)/h
            ray=(rot@Vector((px,py,frame[0].z))).normalized()
            hit,p,_,face,obj,_=scene.ray_cast(graph,origin,ray)
            label=None
            if hit and face>=0 and obj.name.startswith("V4 | sea-axis"):
                mat=obj.data.materials[obj.data.polygons[face].material_index]
                if mat and mat.name.startswith("V4 gray") and not mat.name.endswith(("cap","heel")):
                    label=("main" if p.y>-11.4 else "first_shoulder" if p.y>-15.45
                           else "incision" if p.y>-19.2 else "second_shoulder")
            if not label and hit:
                proxy, _, _, _ = exposed_proxy.ray_cast(origin, ray)
                if proxy is not None and (p-origin).length + 1e-4 < (proxy-origin).length:
                    blockers[obj.name] += 1
            if label:
                counts[label]+=1
                lower[label]+=p.z<=4.8
                pix.extend((*palette[label],1))
            else:
                pix.extend((.07,.085,.105,1))
    img=bpy.data.images.new("V4 rock ID",width=w,height=h)
    img.pixels.foreach_set(pix)
    img.filepath_raw=str(out/"visible-ids.png")
    img.file_format="PNG"
    img.save()
    (out/"visibility.json").write_text(json.dumps({
        "raster_px":[w,h],"camera":camera.name,
        "scope":"first-hit triangles of authored exposed rock, grouped by provisional Y bands",
        "occluding_objects_before_authored_rock":dict(blockers.most_common()),
        "camera_location_BU":list(origin),
        "camera_rotation_quaternion_wxyz":list(rot.to_quaternion()),
        "camera_lens_mm":camera.data.lens,
        "pixel_counts":{k:counts[k] for k in palette},
        "at_or_below_Z_4_8_BU":{k:lower[k] for k in palette},
    },indent=2)+"\n")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("output",type=Path)
    p.add_argument("--full",action="store_true")
    p.add_argument("--projection-only",action="store_true")
    args=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    out=args.output
    scene=bpy.context.scene
    assert not [i.name for i in bpy.data.images if i.source=="FILE" and i.users and not i.packed_file]
    if args.projection_only:
        first_hit(scene,bpy.data.objects["Sunset study"],out)
        return
    scene.render.resolution_percentage=55 if args.full else 39
    scene.cycles.samples=8 if args.full else 5
    scene.cycles.use_denoising=True
    neutral=bpy.data.materials.new("V4 render only | neutral")
    neutral.diffuse_color=(.58,.58,.58,1)
    for layer in scene.view_layers:
        layer.material_override=neutral
    sunset=bpy.data.objects["Sunset study"]
    views=[("sunset",sunset),("front",bpy.data.objects["front"]),
           ("overhead",bpy.data.objects["elevated"])]
    if args.full:
        views.extend([("right",bpy.data.objects["right"]),
                      ("left",make_camera("QA left",(-44,-10,12),(1,-10,4),54)),
                      ("rear",make_camera("QA rear",(0,47,16),(0,-7,3.1),56))])
    for label,cam in views:
        scene.camera=cam
        scene.render.filepath=str(out/f"clay-{label}.png")
        bpy.ops.render.render(write_still=True)
    scene.camera=sunset
    for layer in scene.view_layers:
        layer.material_override=None
    first_hit(scene,sunset,out)
    if args.full:
        # Diagnostic below-sea view: expose the shell, not the occluding water.
        scene.camera=make_camera("QA underside",(-12,-14,-34),(1,-10,-.6),48)
        for obj in scene.objects:
            if obj.type=="MESH" and not obj.name.startswith(("V4 | sea-axis","V3-D | detached skerry")):
                obj.hide_render=True
        bpy.ops.object.light_add(type="AREA",location=(-10,-13,-25))
        light=bpy.context.object
        light.rotation_euler=(Vector((1,-11,0))-light.location).to_track_quat("-Z","Y").to_euler()
        light.data.energy=3100
        light.data.size=14
        for layer in scene.view_layers:
            layer.material_override=neutral
        scene.render.filepath=str(out/"clay-underside.png")
        bpy.ops.render.render(write_still=True)


main()
sys.stdout.flush()
os._exit(0)
