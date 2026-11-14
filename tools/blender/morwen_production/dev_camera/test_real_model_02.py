"""Read-only integration QA on reconstructed EYELID-05 Morwen candidate."""
import hashlib
import json
import os
import runpy
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[4]
BLEND = ROOT / "render_output/morwen_eyelid_retopo_05/MORWEN_EYELID_05_CANDIDATE.blend"
OUT = ROOT / "render_output/morwen_eyelid_retopo_05/DEV_CAMERA_02_REAL_MODEL_QA.json"

def digest_mesh(obj):
    h = hashlib.sha256()
    for v in obj.data.vertices:
        h.update(("%d:%.9f,%.9f,%.9f;" % (v.index, *v.co)).encode())
    if obj.data.shape_keys:
        for key in obj.data.shape_keys.key_blocks:
            h.update(key.name.encode())
            for p in key.data:
                h.update(("%.9f,%.9f,%.9f;" % tuple(p.co)).encode())
    return h.hexdigest()

def main():
    assert BLEND.is_file(), "Reconstructed Morwen candidate missing"
    before_file = hashlib.sha256(BLEND.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    meshes = {o.name: digest_mesh(o) for o in bpy.data.objects if o.type == "MESH"}
    assert "Face" in meshes, "Morwen Face missing"
    original_camera = bpy.context.scene.camera
    original_ptr = original_camera.as_pointer() if original_camera else None
    module = runpy.run_path(str(Path(__file__).with_name("dev_camera_01.py")), run_name="__integration__")
    install, orbit = module["install"], module["orbit"]
    checks = []
    for preset in module["PRESETS"]:
        cam = install(preset=preset, focus="face", distance=0.7)
        checks.append(preset)
        assert cam.get("dev_only") is True
    for az, el in ((0, 0), (45, 15), (180, -20), (270, 45)):
        orbit(azimuth_deg=az, elevation_deg=el, distance=0.7, focus="face")
    current = bpy.context.scene.camera
    assert (current.as_pointer() if current else None) == original_ptr, "Production camera changed"
    assert {o.name: digest_mesh(o) for o in bpy.data.objects if o.type == "MESH"} == meshes, "Mesh/shape key mutation"
    assert hashlib.sha256(BLEND.read_bytes()).hexdigest() == before_file, "Source blend modified"
    report = {"status":"REAL_MODEL_HEADLESS_PASS", "input_blend_sha256":before_file,
              "mesh_count":len(meshes),"presets":checks,"orbit_cases":4,
              "production_camera_preserved":True,"meshes_and_shape_keys_preserved":True,
              "source_blend_unchanged":True,"visual_art_qa":"NOT_RUN","android_qa":"NOT_RUN"}
    OUT.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report))
if __name__ == "__main__":
    main()
