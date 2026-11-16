"""Generate a tiny isolated Blender TECHNICAL fixture. Never an art candidate."""
import argparse
from pathlib import Path
import bpy

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(__import__("sys").argv[__import__("sys").argv.index("--")+1:])
    path = Path(args.out).resolve()
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))
    obj = bpy.context.object
    obj.name = "TECHNICAL_FIXTURE_NOT_ART"
    mat = bpy.data.materials.new("test_roughness")
    mat.use_nodes = True
    obj.data.materials.append(mat)
    bpy.ops.object.light_add(type="AREA", location=(1,-3,5))
    bpy.context.object.data.energy = 350
    bpy.context.object.data.size = 3
    bpy.ops.object.camera_add(location=(4,-6,5))
    cam = bpy.context.object
    direction = -cam.location
    cam.rotation_euler = direction.to_track_quat("-Z","Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 6
    scene = bpy.context.scene
    scene.camera = cam
    enum = scene.render.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in enum else ("BLENDER_EEVEE" if "BLENDER_EEVEE" in enum else "CYCLES")
    scene.render.resolution_x = 96
    scene.render.resolution_y = 96
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.wm.save_as_mainfile(filepath=str(path))

if __name__ == "__main__":
    main()
