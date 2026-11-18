#!/usr/bin/env python3
"""Build an UNAPPROVED, non-destructive Morwen reference-only Blender workspace.

Run in Blender 4.3+: blender -b --python tools/morwen_rebuild01/create_sculpt_workspace.py -- --output /absolute/path/MORWEN_SCULPT_WORKSPACE_UNAPPROVED.blend
Never writes to canonical references or approved .blend files.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "tools/blender/production_mesh_08/references"
LANDMARKS = ROOT / "docs/qa/morwen-rebuild-01/layer0-landmark-review/layer0-landmarks.json"
SOURCES = {
    "front": ("7809.png", "b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed"),
    "right": ("7807.png", "9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737"),
    "back": ("7810.png", "b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f"),
    "left": ("7808.png", "69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa"),
}
# Fixed scene convention from MORWEN_NEW_SCULPT_IMPLEMENTATION.md.
# The drawing's 1024 pixels correspond to 2.0 scene units; this is a
# VISUALIZATION scale only, not calibrated anatomy or physical dimensions.
SCALE = 2.0 / 1024.0
DIST = 3.0

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c

def link_only(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)

def camera(name, loc, target, coll):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    coll.objects.link(obj)
    obj.location = loc
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = 2.2
    return obj

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    opts = parser.parse_args(args)
    out = opts.output.resolve()
    if out.exists():
        raise RuntimeError(f"Refusing to overwrite existing file: {out}")
    if ROOT in out.parents or out == ROOT:
        # Keep generated .blend out of tracked source tree unless explicitly staged later.
        raise RuntimeError("Output must be outside repository; inspect before manually importing")
    doc = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    if doc.get("canvas_px") != [384, 1024]:
        raise RuntimeError("Unexpected reference dimensions")
    for view, (filename, digest) in SOURCES.items():
        path = REFERENCE_DIR / filename
        if not path.is_file() or sha256(path) != digest:
            raise RuntimeError(f"Missing or hash-mismatched reference: {path}")
        record = doc["views"][view]
        if record["source"] != filename or record["source_sha256"] != digest:
            raise RuntimeError(f"Landmark reference mismatch: {view}")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = "NONE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    refs = collection("00_CANONICAL_LAYER0_LOCKED")
    guides = collection("01_LANDMARK_GUIDES_UNCALIBRATED")
    sculpt = collection("02_AUTHOR_SCULPT_EMPTY")
    cameras = collection("03_FIXED_REVIEW_CAMERAS")
    for view, (filename, digest) in SOURCES.items():
        img = bpy.data.images.load(str(REFERENCE_DIR / filename), check_existing=True)
        img.pack()  # output workspace is portable; original PNG is untouched
        obj = bpy.data.objects.new(f"REF_{view.upper()}_DO_NOT_EDIT", None)
        refs.objects.link(obj)
        obj.empty_display_type = "IMAGE"
        obj.data = img
        obj.empty_display_size = 2.0
        obj.show_in_front = False
        obj.hide_select = True
        obj["reference_sha256"] = digest
        # Reference planes are displaced from the sculpt origin; the drawing is
        # not assumed to have a calibrated orthographic camera.
        if view == "front":
            obj.location = (0, -DIST, 1)
            obj.rotation_euler = (1.57079632679, 0, 0)
        elif view == "back":
            obj.location = (0, DIST, 1)
            obj.rotation_euler = (1.57079632679, 0, 3.14159265359)
        elif view == "right":
            obj.location = (-DIST, 0, 1)
            obj.rotation_euler = (1.57079632679, 0, -1.57079632679)
        else:
            obj.location = (DIST, 0, 1)
            obj.rotation_euler = (1.57079632679, 0, 1.57079632679)
    # Landmark data remains metadata rather than invented 3D anatomical points.
    guides["landmark_json"] = str(LANDMARKS.relative_to(ROOT))
    guides["observed_3d_positions"] = "NOT_CALIBRATED"
    sculpt["status"] = "EMPTY_BY_DESIGN; AUTHOR REQUIRED"
    camera("CAM_FRONT", (0, -6, 1), (0, 0, 1), cameras)
    camera("CAM_BACK", (0, 6, 1), (0, 0, 1), cameras)
    camera("CAM_RIGHT", (-6, 0, 1), (0, 0, 1), cameras)
    camera("CAM_LEFT", (6, 0, 1), (0, 0, 1), cameras)
    camera("CAM_3Q_FRONT_RIGHT", (-4.25, -4.25, 2.5), (0, 0, 1), cameras)
    camera("CAM_3Q_BACK_LEFT", (4.25, 4.25, 2.5), (0, 0, 1), cameras)
    scene.camera = bpy.data.objects["CAM_FRONT"]
    scene["status"] = "UNAPPROVED_TEMPLATE_NOT_A_SCULPT"
    scene["projection_calibrated"] = False
    scene["reference_manifest"] = str(LANDMARKS.relative_to(ROOT))
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"WORKSPACE_CREATED {out}")

if __name__ == "__main__":
    main()
