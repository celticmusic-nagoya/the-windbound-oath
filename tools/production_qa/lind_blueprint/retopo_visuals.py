"""Render fixed production views and measure the before/after image delta."""
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rebuild import pixels


def main():
    root = Path(sys.argv[sys.argv.index("--") + 1])
    out = root / "visuals"
    out.mkdir()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 65
    scene.render.image_settings.file_format = "PNG"
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    size, values = pixels(root / "blueprint/verification/source.png")
    previous_size, previous = pixels(root / "baseline/pre_retopo.png")
    if size != previous_size:
        raise ValueError("Fixed comparison images have different dimensions")
    image = bpy.data.images.new("Retopology RGB delta", width=size[0], height=size[1], alpha=True)
    changes = [abs(a-b) if i % 4 != 3 else 1.0 for i,(a,b) in enumerate(zip(values, previous))]
    image.pixels.foreach_set([min(v*8, 1) if i % 4 != 3 else 1 for i,v in enumerate(changes)])
    image.filepath_raw = str(out / "before_after_rgb_difference_x8.png")
    image.file_format = "PNG"
    image.save()
    rgb = [v for i,v in enumerate(changes) if i % 4 != 3]
    (out / "visual_delta.json").write_text(json.dumps({
        "dimensions":size, "compared":"same cg_review camera, cut candidate before vs after retopo",
        "max_decoded_rgb_delta":max(rgb), "mean_decoded_rgb_delta":sum(rgb)/len(rgb),
        "changed_pixels":sum(any(changes[i:i+3]) for i in range(0,len(changes),4)),
        "difference_display_gain":8
    }, sort_keys=True)+"\n")
    for camera in ("front", "shore_detail", "elevated"):
        scene.camera = scene.objects[camera]
        scene.render.filepath = str(out / f"{camera}.png")
        bpy.ops.render.render(write_still=True)
    scene.camera = scene.objects["cg_review"]
    clay = bpy.data.materials.new("Junction review clay")
    clay.diffuse_color = (.34,.34,.34,1)
    bpy.context.view_layer.material_override = clay
    scene.render.filepath = str(out / "cg_review_clay.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
