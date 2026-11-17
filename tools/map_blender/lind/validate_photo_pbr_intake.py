#!/usr/bin/env python3
"""Fail-closed provenance/texture-set intake. No downloads or source mutation."""
import argparse
import hashlib
import json
from pathlib import Path

CHANNELS = {"basecolor": "sRGB", "roughness": "Non-Color", "normal": "Non-Color"}
def validate(manifest_path):
    mpath = Path(manifest_path).resolve()
    root = mpath.parent
    data = json.loads(mpath.read_text(encoding="utf-8"))
    errors = []
    if data.get("asset_status") != "candidate":
        errors.append("asset_status must be candidate")
    for field in ("source_url", "author", "license", "license_evidence_url", "capture_location_claim"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append("missing " + field)
    if data.get("capture_location_claim") == "Ireland" and not data.get("ireland_provenance_evidence_url"):
        errors.append("Irish provenance claim requires evidence")
    textures = data.get("textures")
    if not isinstance(textures, dict) or not textures:
        errors.append("textures missing")
        textures = {}
    if "basecolor" not in textures or "roughness" not in textures:
        errors.append("basecolor and roughness required")
    for channel, item in textures.items():
        if channel not in CHANNELS:
            errors.append("unsupported channel " + channel)
            continue
        if not isinstance(item, dict):
            errors.append("invalid entry " + channel)
            continue
        path = item.get("path", "")
        p = (root / path).resolve() if isinstance(path, str) else root
        if not isinstance(path, str) or p == root or root not in p.parents:
            errors.append("unsafe texture path " + channel)
            continue
        if not p.is_file():
            errors.append("texture missing " + channel)
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            errors.append("hash mismatch " + channel)
        if item.get("color_space") != CHANNELS[channel]:
            errors.append("color space mismatch " + channel)
    return {"status": "FAIL" if errors else "INTAKE_PASS_NOT_ART_APPROVED",
            "G1": "FAIL" if errors else "PARTIAL", "G2": "NOT_RUN",
            "G3": "NOT_RUN", "G4": "NOT_RUN", "errors": errors}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--report")
    args = ap.parse_args()
    result = validate(args.manifest)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        Path(args.report).write_text(output + "\n", encoding="utf-8")
    print(output)
    raise SystemExit(1 if result["errors"] else 0)

if __name__ == "__main__":
    main()
