"""Non-destructive four-view contact sheet renderer for a frozen Morwen candidate.

Run under Blender Python: python -m bpy -b --python tools/character_blender/morwen_four_view_capture.py -- source.blend output_dir
This produces technical review inputs, NOT approved art or a new model.
"""
import bpy
import hashlib
import json
import math
import os
import pathlib
import sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) != 2:
    raise SystemExit("Usage: -- source.blend output_dir")
source = pathlib.Path(args[0]).resolve()
output = pathlib.Path(args[1]).resolve()
output.mkdir(parents=True, exist_ok=True)

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

before = digest(source)
report = {
    "source": str(source),
    "source_sha256": before,
    "status": "BLOCKED",
    "blender_version": bpy.app.version_string,
    "views": [],
    "artistic_qa": "NOT_RUN",
    "canonical_design_match": "BLOCKED",
    "game_qa": "NOT_RUN",
}
try:
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    meshes = [obj for obj in scene.objects if obj.type == "MESH" and not obj.hide_render]
    if not meshes:
        raise RuntimeError("No visible meshes")
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low + high) * 0.5
    size = high - low
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    camera_data = bpy.data.cameras.new("MORWEN_QA_FOUR_VIEW_CAMERA")
    camera = bpy.data.objects.new("MORWEN_QA_FOUR_VIEW_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    distance = max(size.length * 2, 1.0)
    aspect = scene.render.resolution_x / scene.render.resolution_y
    # Explicit camera positions avoid mirrored image substitutions.
    directions = (
        ("front", (0, -1, 0)),
        ("back", (0, 1, 0)),
        ("facing_right", (1, 0, 0)),
        ("facing_left", (-1, 0, 0)),
    )
    for name, direction in directions:
        camera.location = center + Vector(direction) * distance
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        inverse = camera.rotation_euler.to_matrix().inverted()
        projected = [inverse @ (point - center) for point in points]
        xspan = max(p.x for p in projected) - min(p.x for p in projected)
        yspan = max(p.y for p in projected) - min(p.y for p in projected)
        camera_data.ortho_scale = max(yspan, xspan / aspect, 0.001) / 0.82
        destination = output / ("MORWEN_QA_" + name.upper() + ".png")
        scene.render.filepath = str(destination)
        bpy.ops.render.render(write_still=True)
        if not destination.is_file() or destination.stat().st_size == 0:
            raise RuntimeError("Missing render: " + name)
        report["views"].append({
            "direction": name,
            "filename": destination.name,
            "sha256": digest(destination),
            "bytes": destination.stat().st_size,
            "ortho_scale": round(camera_data.ortho_scale, 6),
            "status": "RENDERED_NOT_ART_REVIEWED",
        })
    report["status"] = "PASS_FOUR_RENDER_FILES_ONLY"
except Exception as error:
    report["status"] = "BLOCKED_RENDER_ERROR"
    report["error"] = str(error)
finally:
    report["source_sha256_after"] = digest(source)
    report["source_unchanged"] = report["source_sha256_after"] == before
    if not report["source_unchanged"]:
        report["status"] = "FAIL_SOURCE_MUTATED"
    (output / "MORWEN_FOUR_VIEW_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": report["status"], "views": len(report["views"])}))
if report["status"] != "PASS_FOUR_RENDER_FILES_ONLY":
    raise SystemExit(1)
