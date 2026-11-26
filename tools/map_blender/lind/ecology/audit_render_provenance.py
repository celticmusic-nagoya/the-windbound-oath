#!/usr/bin/env python3
"""Read-only LIND-ECO-01 render provenance audit. Stdlib only."""
import argparse
import hashlib
import json
from pathlib import Path

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def audit(root):
    manifest = root / "renders.json"
    if not manifest.is_file():
        return {"status": "FAIL", "issues": ["renders.json missing"], "checked": 0}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return {"status": "FAIL", "issues": [f"manifest unreadable: {exc}"], "checked": 0}
    entries = data.get("files", {})
    if not isinstance(entries, dict) or not entries:
        return {"status": "FAIL", "issues": ["no render records"], "checked": 0}
    issues, build_hashes, checked = [], set(), 0
    for name, rec in sorted(entries.items()):
        if not isinstance(rec, dict):
            issues.append(f"{name}: invalid record")
            continue
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts or rel.name != name:
            issues.append(f"{name}: unsafe path")
            continue
        target = root / rel
        if not target.is_file():
            issues.append(f"{name}: missing")
            continue
        expected = rec.get("sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            issues.append(f"{name}: missing/invalid SHA256")
        elif sha(target) != expected.lower():
            issues.append(f"{name}: SHA256 mismatch")
        checked += 1
        if rec.get("engine") not in ("PIL", "postprocess"):
            for key in ("blend_sha256", "build_combined_geometry_sha256", "render_script_sha256"):
                val = rec.get(key)
                if not isinstance(val, str) or len(val) != 64:
                    issues.append(f"{name}: missing {key}")
            if rec.get("build_combined_geometry_sha256"):
                build_hashes.add(rec["build_combined_geometry_sha256"])
    if len(build_hashes) > 1:
        issues.append("render records reference multiple geometry builds")
    return {"status": "PASS" if not issues else "FAIL",
            "checked": checked, "build_geometry_hashes": sorted(build_hashes), "issues": issues,
            "scope": "manifest/PNG consistency only; NOT independent G2 or source rebuild proof"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("assets/candidates/LIND-ECO-01/eco_kit_v1/renders"))
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
