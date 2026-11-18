#!/usr/bin/env python3
"""Render four orthographic camera views of unapproved reference-only workspace.

No meshes or approved assets are created/modified. Output is visual QA evidence.
"""
import sys
from pathlib import Path
import bpy

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise RuntimeError("Expected output directory after --")
    out = Path(args[0]).resolve()
    scene = bpy.context.scene
    assert scene.get("status") == "UNAPPROVED_TEMPLATE_NOT_A_SCULPT"
    assert scene.get("projection_calibrated") is False
    assert len(bpy.data.meshes) == 0
    out.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8
    scene.world.color = (0.1, 0.1, 0.1)
    # Image empties are viewport guides and do not appear in final renders.
    # Create disposable textured planes in memory, matching their transforms.
    for view in ("FRONT", "RIGHT", "BACK", "LEFT"):
        ref = bpy.data.objects[f"REF_{view}_DO_NOT_EDIT"]
        image = ref.data
        assert image and image.packed_file
        width = 2.0 * image.size[0] / image.size[1]
        height = 2.0
        mesh = bpy.data.meshes.new(f"QA_ONLY_{view}_PLANE")
        mesh.from_pydata([(-width/2,-height/2,0),(width/2,-height/2,0),(width/2,height/2,0),(-width/2,height/2,0)], [], [(0,1,2,3)])
        mesh.update()
        uv = mesh.uv_layers.new()
        for loop, coord in zip(mesh.polygons[0].loop_indices, ((0,0),(1,0),(1,1),(0,1))):
            uv.data[loop].uv = coord
        obj = bpy.data.objects.new(f"QA_ONLY_{view}_PLANE", mesh)
        scene.collection.objects.link(obj)
        obj.matrix_world = ref.matrix_world.copy()
        mat = bpy.data.materials.new(f"QA_ONLY_{view}_EMISSION")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Strength"].default_value = 1.0
        mat.node_tree.links.new(tex.outputs["Color"], emission.inputs["Color"])
        output = nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(emission.outputs[0], output.inputs["Surface"])
        mesh.materials.append(mat)
        obj.hide_render = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    # Never save these disposable review meshes to the original .blend.
    for view in ("FRONT", "RIGHT", "BACK", "LEFT"):
        cam = bpy.data.objects[f"CAM_{view}"]
        assert cam.type == "CAMERA" and cam.data.type == "ORTHO"
        scene.camera = cam
        bpy.data.objects[f"QA_ONLY_{view}_PLANE"].hide_render = False
        scene.render.filepath = str(out / f"MORWEN_L0_CAMERA_{view}_UNCALIBRATED.png")
        bpy.ops.render.render(write_still=True)
        if not Path(scene.render.filepath).is_file():
            raise RuntimeError(f"Render missing: {view}")
        print("REFERENCE_CAMERA_RENDER_CREATED", view, scene.render.filepath)
        bpy.data.objects[f"QA_ONLY_{view}_PLANE"].hide_render = True
    print("FOUR_CAMERA_RENDER_PASS")

if __name__ == "__main__":
    main()
