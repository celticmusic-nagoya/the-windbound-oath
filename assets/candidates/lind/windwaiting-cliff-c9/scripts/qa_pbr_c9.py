"""Reopen the PBR scenes and verify unchanged geometry and packed assets."""
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy
from PIL import Image

manifest, c8, c9, output = map(Path, sys.argv[1:])
assets = json.loads(manifest.read_text())["assets"]
expected = {Path(record["uri"]).name: record["sha256"]
            for asset in assets for record in asset["maps"]}


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    meshes = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        digest = hashlib.sha256()
        digest.update(struct.pack("<16f", *(value for row in obj.matrix_world for value in row)))
        for vert in obj.data.vertices:
            digest.update(struct.pack("<3f", *vert.co))
        for poly in obj.data.polygons:
            digest.update(struct.pack("<I", len(poly.vertices)))
            digest.update(struct.pack(f"<{len(poly.vertices)}I", *poly.vertices))
        for layer in obj.data.uv_layers:
            for value in layer.uv:
                digest.update(struct.pack("<2f", *value.vector))
        meshes[obj.name] = digest.hexdigest()
    lighting = {
        obj.name: [list(row) for row in obj.matrix_world]
        for obj in bpy.data.objects if obj.type in {"LIGHT", "CAMERA"}
    }
    return meshes, lighting


report = {}
for label, baseline in (("B", c8), ("C", c9)):
    initial = snapshot(baseline)
    candidate = output / f"{label}_UNAPPROVED.blend"
    final = snapshot(candidate)
    assert initial == final, label
    packed = {}
    for img in bpy.data.images:
        if img.source != "FILE":
            continue
        assert img.packed_file and tuple(img.size) == (1024, 1024) and img.has_data, img.name
        actual = hashlib.sha256(img.packed_file.data).hexdigest()
        assert expected[img.name] == actual, img.name
        packed[img.name] = {"size": list(img.size), "sha256": actual, "color_space": img.colorspace_settings.name}
    assert packed.keys() == expected.keys()
    report[label] = {
        "reopen": "PASS", "geometry_uv_and_transforms_unchanged": "PASS",
        "camera_light_transforms_unchanged": "PASS", "packed_textures": packed,
        "blend_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
    }
for png in sorted(output.glob("*.png")):
    with Image.open(png) as img:
        img.load()
        report[png.name] = {"size": list(img.size), "sha256": hashlib.sha256(png.read_bytes()).hexdigest()}
result = {"blender": bpy.app.version_string, "G1": "BLOCKED", "G3_texture_subset": "PASS",
          "G4": "NOT_RUN", "results": report}
(output / "qa.json").write_text(json.dumps(result, indent=2) + "\n")
