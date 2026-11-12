"""MORWEN-RIG-05: create non-destructive four-view reference alignment scene.

Usage: blender -b --python tools/blender/align_morwen_views.py -- --input-dir /path/to/images --output-dir /tmp/morwen-rig-05
Requires original source images, which are NOT committed to the public repo.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy

SOURCES = {
    "front": ("7694.png", "a0f9bdbdfaf928aab49ea116d3ec40620f1558efe55f5f90aa55002213ae7bbd"),
    "left": ("7693.png", "cd1dbc8447de72f0b4239cb6e76ea12c703df0812b1fc225ecb892c34db1b984"),
    "right": ("7684.png", "f5b5787cce36806a365251095f1c43138e4a12409e176c24af8a8406642117d1"),
    "back": ("7776.png", "d9506845f6377ad465b291b8ba6bc0ff2e60340f836ad7c18c213c453e7bb393"),
}

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for facing, (name, sha) in SOURCES.items():
        p = args.input_dir / name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != sha:
            raise ValueError("Source missing or SHA mismatch: " + facing)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 500
    scene.render.film_transparent = True
    info = {}
    for idx, (facing, (name, sha)) in enumerate(SOURCES.items()):
        image = bpy.data.images.load(str((args.input_dir / name).resolve()), check_existing=False)
        image.pack()
        obj = bpy.data.objects.new("REFERENCE_" + facing.upper(), None)
        bpy.context.collection.objects.link(obj)
        obj.empty_display_type = "IMAGE"
        obj.data = image
        obj.empty_display_size = 1.0
        obj.location = (float(idx) * 1.25, 0.0, 0.5)
        obj.show_in_front = True
        obj["source_sha256"] = sha
        obj["facing"] = facing
        obj["approval_status"] = "REFERENCE_ONLY"
        info[facing] = {"source": name, "sha256": sha, "pixel_size": list(image.size),
                        "anchor_status": "NOT_MEASURED", "image_packed": True}
    # Explicit guides only. Do not claim body joints have been measured.
    for idx in range(4):
        guide = bpy.data.objects.new("GROUND_GUIDE_" + str(idx), None)
        bpy.context.collection.objects.link(guide)
        guide.empty_display_type = "CUBE"
        guide.empty_display_size = 0.02
        guide.location = (float(idx) * 1.25, 0.0, 0.0)
    path = args.output_dir / "morwen_four_view_reference.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    report = {"task":"MORWEN-RIG-05", "status":"PASS", "references":info,
              "joint_anchors_measured":False, "canon_approved":False,
              "production_assets_modified":False}
    (args.output_dir / "qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("MORWEN_RIG_05_PASS")

if __name__ == "__main__":
    run()
