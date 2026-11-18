#!/usr/bin/env python3
"""Render the actual unapproved head-study mesh from four fixed review cameras."""
import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args(argv)
    if bpy.context.scene.get("status") not in ("UNAPPROVED_HEAD_SURFACE_STUDY_NOT_A_CHARACTER", "UNAPPROVED_FACIAL_PLANES_BLOCKOUT_NOT_A_CHARACTER"):
        raise RuntimeError("Expected the unapproved head study scene")
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if len(meshes) != 1 or meshes[0].name not in ("MORWEN_HEAD_CONTINUOUS_QUAD_STUDY", "MORWEN_FACIAL_PLANES_BLOCKOUT_UNAPPROVED"):
        raise RuntimeError("Expected exactly one authored head study mesh")
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("HEAD_STUDY_REVIEW_WORLD")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.08, 0.10, 0.15, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    mat = bpy.data.materials.new("UNAPPROVED_CLAY_MATERIAL")
    mat.diffuse_color = (0.55, 0.43, 0.42, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.55, 0.43, 0.42, 1)
    bsdf.inputs["Roughness"].default_value = 0.8
    meshes[0].data.materials.append(mat)
    light_data = bpy.data.lights.new("STUDY_SOFTBOX", "AREA")
    light = bpy.data.objects.new("STUDY_SOFTBOX", light_data)
    scene.collection.objects.link(light)
    light.location = (-2, -3, 4)
    light_data.energy = 320
    light_data.shape = "DISK"
    light_data.size = 3
    a.output_dir.mkdir(parents=True, exist_ok=True)
    for view in ("FRONT", "RIGHT", "BACK", "LEFT"):
        cam = bpy.data.objects["CAM_" + view]
        cam.data.ortho_scale = 0.52
        direction = Vector((0, 0, 1.70)) - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam
        scene.render.filepath = str(a.output_dir / ("MORWEN_HEAD_STUDY_" + view + "_UNAPPROVED.png"))
        bpy.ops.render.render(write_still=True)
        print("HEAD_STUDY_RENDER", view, scene.render.filepath)

if __name__ == "__main__":
    main()
