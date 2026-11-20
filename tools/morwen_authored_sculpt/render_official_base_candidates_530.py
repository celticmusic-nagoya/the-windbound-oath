"""Render exact Blender Studio base assets without changing their mesh data."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

TARGETS = {
    "head": ("Head - Stylized", "GEO-head_stylized"),
    "body_female": ("Body Female - Stylized", "GEO-body_female_stylized"),
}
VIEWS = {
    "front": (0, -5, 0), "right": (-5, 0, 0), "back": (0, 5, 0),
    "left": (5, 0, 0), "three_quarter": (3, -4, 1),
}


def mesh_inventory(collection):
    return {
        obj.name: {
            "vertices": len(obj.data.vertices), "edges": len(obj.data.edges),
            "faces": len(obj.data.polygons), "mesh": obj.data.name,
            "world_matrix": [list(row) for row in obj.matrix_world],
        }
        for obj in sorted(collection.all_objects, key=lambda obj: obj.name)
        if obj.type == "MESH"
    }


def aim(obj, center):
    obj.rotation_euler = (center - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_asset(source, out, slug, collection_name, primary_name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(source)) as (available, loaded):
        if collection_name not in available.collections:
            raise ValueError(f"Missing source collection {collection_name}")
        loaded.collections = [collection_name]
    collection = loaded.collections[0]
    scene = bpy.context.scene
    scene.collection.children.link(collection)
    bpy.context.view_layer.update()
    inventory = mesh_inventory(collection)
    if set(inventory) != {primary_name, primary_name + ".eye.L", primary_name + ".eye.R"}:
        raise ValueError(f"Unexpected source mesh set: {sorted(inventory)}")
    points = [obj.matrix_world @ Vector(corner) for obj in collection.all_objects
              if obj.type == "MESH" for corner in obj.bound_box]
    low = Vector(min(p[axis] for p in points) for axis in range(3))
    high = Vector(max(p[axis] for p in points) for axis in range(3))
    height = high.z - low.z
    if not math.isfinite(height) or height <= 0:
        raise ValueError(f"Invalid source height for {collection_name}")
    center = (low + high) / 2
    unit = height / 2

    clay = bpy.data.materials.new("Neutral clay")
    clay.diffuse_color = (0.55, 0.49, 0.44, 1)
    clay.use_nodes = True
    clay.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = clay.diffuse_color
    bpy.context.view_layer.material_override = clay
    scene.world = bpy.data.worlds.new("Neutral world")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    for offset, energy, size in [((3, -4, 5), 850, 5), ((-3, 1, 3), 600, 4)]:
        light = bpy.data.lights.new("Softbox", "AREA")
        light.energy = energy * unit ** 2
        light.size = size * unit
        lamp = bpy.data.objects.new("Softbox", light)
        scene.collection.objects.link(lamp)
        lamp.location = center + Vector(offset) * unit
        aim(lamp, center)

    camera = bpy.data.cameras.new("Orthographic camera")
    camera.type = "ORTHO"
    camera.ortho_scale = 3.1 * unit
    cam = bpy.data.objects.new("Orthographic camera", camera)
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 512
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene["asset_status"] = "SOURCE_ONLY_NOT_ADOPTED"

    cameras = {}
    for view, offset in VIEWS.items():
        cam.location = center + Vector(offset) * unit
        aim(cam, center)
        cameras[view] = {"location": list(cam.location), "rotation": list(cam.rotation_euler)}
        scene.render.filepath = str(out / f"{slug}_{view}.png")
        bpy.ops.render.render(write_still=True)

    cam.location = cameras["front"]["location"]
    cam.rotation_euler = cameras["front"]["rotation"]
    scene.render.filepath = "//"
    bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{slug}_source_candidate.blend"))
    wire = bpy.data.materials.new("Topology wire")
    wire.use_nodes = True
    nodes = wire.node_tree.nodes
    edge = nodes.new("ShaderNodeWireframe")
    edge.use_pixel_size = True
    edge.inputs["Size"].default_value = 0.6
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.54, 0.49, 0.44, 1)
    ramp.color_ramp.elements[1].color = (0.015, 0.015, 0.015, 1)
    wire.node_tree.links.new(edge.outputs[0], ramp.inputs[0])
    wire.node_tree.links.new(ramp.outputs[0], nodes.get("Principled BSDF").inputs["Base Color"])
    bpy.context.view_layer.material_override = wire
    scene.render.filepath = str(out / f"{slug}_wire.png")
    bpy.ops.render.render(write_still=True)
    return {"source_collection": collection_name, "meshes": inventory, "height": height,
            "ortho_scale": camera.ortho_scale, "cameras": cameras,
            "wire_display": "Cycles wire shader displays render triangulation",
            "layer0_fit": "NOT_COMPARABLE", "reason": (
                "Standalone source head; no complete character registration."
                if slug == "head" else
                "Unmodified source pose and silhouette lack matched Layer 0 correspondence.")}


def main():
    out, source, *archives = (Path(s).resolve() for s in sys.argv[sys.argv.index("--") + 1:])
    out.mkdir(parents=True, exist_ok=True)
    expected = "811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515"
    digest = hashlib.sha256(archives[0].read_bytes()).hexdigest() if archives else None
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if (archives and digest != expected) or source_digest != "3c121505651140ceb4d69fd1d8923f7788ffadd81672f5be14845a5f2c75c137":
        raise ValueError("Pinned Blender Studio source hash mismatch")
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    license_line = "All provided assets are public domain under the CC0 license."
    if license_line not in bpy.data.texts["README"].as_string().splitlines():
        raise ValueError("Embedded bundle README does not confirm CC0")
    manifest = {"release": "1.4.1", "archive_sha256": digest, "expected_archive_sha256": expected,
                "source_blend_sha256": source_digest,
                "license": "CC0-1.0", "license_evidence": f"Embedded README: {license_line}",
                "license_scope": "Human Base Meshes collections only; separate Rain Rig notice excluded",
                "upstream": "https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip"}
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    report = {"status": "SOURCE_ONLY_NOT_ADOPTED", "blender": bpy.app.version_string,
              "objects": {slug: render_asset(source, out, slug, *names) for slug, names in TARGETS.items()}}
    (out / "source_candidate_qa.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
