"""Read-only audit of every saved Shape Key coordinate; no model writes."""
import hashlib
import json
import os
from pathlib import Path
import struct

import bpy

model = Path(os.environ.get("MORWEN_EYELID_BLEND", "render_output/morwen_eyelid_retopo_05/MORWEN_EYELID_05_CANDIDATE.blend")).resolve()
assert model.is_file(), f"Missing candidate model: {model}"
before = hashlib.sha256(model.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(model))
result = {"input_blend_sha256": before, "objects": {}, "status": "PASS"}
for obj in sorted((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: o.name):
    keys = obj.data.shape_keys
    record = {"vertex_count": len(obj.data.vertices), "shape_keys": {}}
    if keys:
        for key in keys.key_blocks:
            assert len(key.data) == len(obj.data.vertices), f"{obj.name}/{key.name}: vertex mismatch"
            digest = hashlib.sha256()
            for vert in key.data:
                digest.update(struct.pack("<3d", *[float(v) for v in vert.co]))
            record["shape_keys"][key.name] = digest.hexdigest()
    result["objects"][obj.name] = record
face_keys = list(result["objects"].get("Face", {}).get("shape_keys", {}))
assert len(face_keys) == 57 and "Basis" in face_keys and all(f"target_{i}" in face_keys for i in range(56)), "Expected Basis + target_0..target_55 (57 key blocks)"
assert hashlib.sha256(model.read_bytes()).hexdigest() == before, "Input blend changed"
out = Path(os.environ.get("MORWEN_SHAPEKEY_AUDIT_OUT", "render_output/morwen_eyelid_retopo_05/SHAPE_KEY_FINGERPRINTS_07.json"))
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "face_shape_key_count_including_basis": len(result["objects"]["Face"]["shape_keys"]), "input_blend_sha256": before, "note": "Saved-model inventory only; no cross-version equivalence asserted"}))
