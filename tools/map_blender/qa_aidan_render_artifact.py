#!/usr/bin/env python3
"""Independent, read-only G3 audit of Aidan Home candidate render artifacts."""
import argparse
import hashlib
import json
import pathlib
import struct

VIEWS = ("front", "rear", "left", "right", "game")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

def audit(folder):
    folder = pathlib.Path(folder)
    errors = []
    evidence = {}
    try:
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        views = manifest["views"]
        if set(views) != set(VIEWS):
            errors.append("expected exactly five named views")
        if manifest.get("status") != "CANDIDATE_NOT_CANON":
            errors.append("candidate status missing")
        for view in VIEWS:
            path = folder / ("aidan_" + view + ".png")
            if path.is_symlink() or not path.is_file():
                errors.append(view + ": missing or symlink")
                continue
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if views.get(view) != digest:
                errors.append(view + ": SHA-256 mismatch")
            if len(data) < 33 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
                errors.append(view + ": invalid PNG header")
                continue
            width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
            evidence[view] = {"sha256": digest, "width": width, "height": height, "bit_depth": depth, "color_type": color_type}
            if width < 128 or height < 128 or color_type != 6 or depth != 8:
                errors.append(view + ": unexpected dimensions or non-RGBA PNG")
        blend = folder / "aidan_candidate.blend"
        if blend.is_symlink() or not blend.is_file() or blend.stat().st_size <= 1000:
            errors.append("missing or undersized .blend")
    except (OSError, ValueError, KeyError, TypeError, struct.error) as exc:
        errors.append("invalid render artifact: " + str(exc))
    return {"status": "FAIL" if errors else "PASS", "scope": "G3_HEADER_HASH_ONLY", "errors": errors, "evidence": evidence, "G1": "PENDING", "G2": "PENDING", "G4": "NOT_RUN"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    result = audit(args.folder)
    report = pathlib.Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
