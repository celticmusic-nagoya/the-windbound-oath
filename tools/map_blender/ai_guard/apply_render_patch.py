"""Trusted Blender-side numeric lookdev adapter; never evaluates untrusted code."""
import argparse
import json
import pathlib
import sys
import bpy

def main():
    args = sys.argv[sys.argv.index("--")+1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", required=True)
    parser.add_argument("--output", required=True)
    opt = parser.parse_args(args)
    # Defense in depth; Blender ships with the same small validation logic.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from validate_patch import validate
    safe = validate(json.loads(pathlib.Path(opt.patch).read_text(encoding="utf-8")))
    adjustments = safe["adjustments"]
    scene = bpy.context.scene
    if "camera_ortho_multiplier" in adjustments:
        if not scene.camera or scene.camera.data.type != "ORTHO":
            raise ValueError("orthographic camera required")
        scene.camera.data.ortho_scale *= adjustments["camera_ortho_multiplier"]
    if "exposure_delta" in adjustments:
        scene.view_settings.exposure += adjustments["exposure_delta"]
    lights = [obj for obj in scene.objects if obj.type == "LIGHT"]
    if "light_energy_multiplier" in adjustments:
        if not lights:
            raise ValueError("no light objects")
        for obj in lights:
            obj.data.energy *= adjustments["light_energy_multiplier"]
    if "light_size_multiplier" in adjustments:
        area_lights = [obj for obj in lights if obj.data.type == "AREA"]
        if not area_lights:
            raise ValueError("no area lights")
        for obj in area_lights:
            obj.data.size *= adjustments["light_size_multiplier"]
    if "roughness_delta" in adjustments:
        materials = [m for m in bpy.data.materials if m.use_nodes]
        if not materials:
            raise ValueError("no node materials")
        for mat in materials:
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    sock = node.inputs.get("Roughness")
                    if sock and not sock.is_linked:
                        sock.default_value = max(0.0, min(1.0, sock.default_value + adjustments["roughness_delta"]))
    output = pathlib.Path(opt.output)
    if output.suffix.lower() != ".png":
        raise ValueError("output must be PNG")
    scene.render.filepath = str(output)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("render output missing")

if __name__ == "__main__":
    main()
