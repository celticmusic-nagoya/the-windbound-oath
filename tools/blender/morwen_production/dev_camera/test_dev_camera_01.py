"""Headless Blender QA for MORWEN-DEV-CAMERA-01; no production assets used."""
import hashlib
import importlib.util
import json
from pathlib import Path

import bpy


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("dev_camera_01", HERE / "dev_camera_01.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def digest(obj):
    payload = [[round(float(c), 9) for c in v.co] for v in obj.data.vertices]
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=(0, 0, 1))
    face = bpy.context.object
    face.name = "Face"
    face.shape_key_add(name="Basis")
    face.shape_key_add(name="Blink")
    original_keys = [k.name for k in face.data.shape_keys.key_blocks]
    before = digest(face)
    prod_data = bpy.data.cameras.new("PRODUCTION_DATA")
    production = bpy.data.objects.new("PRODUCTION_CAMERA", prod_data)
    bpy.context.scene.collection.objects.link(production)
    bpy.context.scene.camera = production
    observations = []
    for preset in mod.PRESETS:
        cam = mod.install(preset=preset, focus="face", distance=0.7)
        assert cam is not production
        assert bpy.context.scene.camera is production
        assert cam.get("preset") == preset
        assert cam.get("dev_only") is True
        assert digest(face) == before
        assert [k.name for k in face.data.shape_keys.key_blocks] == original_keys
        observations.append({"preset": preset, "camera_xyz": [round(float(x), 6) for x in cam.location]})
    try:
        mod.install(preset="invalid")
        raise AssertionError("Invalid preset was accepted")
    except ValueError:
        pass
    try:
        mod.install(distance=0.001)
        raise AssertionError("Invalid distance was accepted")
    except ValueError:
        pass
    report = {"status": "HEADLESS_SYNTHETIC_PASS", "production_camera_preserved": True,
              "mesh_digest_preserved": True, "shape_keys_preserved": True,
              "presets": observations, "real_morwen_art_qa": "NOT_RUN",
              "android_qa": "NOT_RUN"}
    out = HERE / "DEV_CAMERA_01_QA.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
