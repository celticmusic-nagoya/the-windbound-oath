"""Fail-closed, non-runtime contract validator for a future full-3D character/world bridge.

No game engine, scene coordinates, units, projection or camera is approved by this tool.
Usage: python tools/character_blender/validate_character_world_bridge.py manifest.json
"""
import hashlib
import json
import pathlib
import sys

SHA_KEYS = ("character_asset_sha256", "world_asset_sha256")
GATES = ("G1", "G2", "G3", "G4")
REQUIRED = ("schema_version", "status", "character_id", "character_asset_sha256",
            "world_asset_sha256", "coordinate_system", "units_per_meter",
            "projection", "camera", "ground_contact", "shadow", "occlusion",
            "animation_states", "collision", "renderer", "qa")
UNAPPROVED = {"BLOCKED", "NOT_RUN", "FAIL"}

def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["root must be an object"]
    for key in REQUIRED:
        if key not in data:
            errors.append("missing " + key)
    if data.get("schema_version") != "character-world-bridge/v1":
        errors.append("unsupported schema_version")
    if data.get("status") != "CANDIDATE":
        errors.append("only CANDIDATE is allowed")
    for key in SHA_KEYS:
        value = data.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            errors.append("invalid " + key)
    qa = data.get("qa")
    if not isinstance(qa, dict):
        errors.append("qa must be an object")
    else:
        for gate in GATES:
            if qa.get(gate) not in UNAPPROVED:
                errors.append(gate + " cannot be declared PASS by an unapproved bridge candidate")
    # Never infer unapproved physical scale, transform, projection or runtime.
    for key in ("coordinate_system", "units_per_meter", "projection", "camera", "renderer"):
        if data.get(key) is not None:
            errors.append(key + " must remain null pending cross-team approval")
    for key in ("ground_contact", "shadow", "occlusion", "animation_states", "collision"):
        if data.get(key) is not None:
            errors.append(key + " must remain null pending measured integration")
    return errors

def main(path):
    p = pathlib.Path(path)
    if not p.is_file():
        raise SystemExit("BLOCKED: manifest missing")
    data = json.loads(p.read_text(encoding="utf-8"))
    errors = validate(data)
    print(json.dumps({"status": "PASS_CANDIDATE_SCHEMA_ONLY" if not errors else "BLOCKED",
                      "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
