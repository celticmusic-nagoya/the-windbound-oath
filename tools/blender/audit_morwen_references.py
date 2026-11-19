"""MORWEN-RIG-04: read-only reference image alignment manifest validation.

No image modification, cropping, mirroring or upload is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "front": ("7694.png", "a0f9bdbdfaf928aab49ea116d3ec40620f1558efe55f5f90aa55002213ae7bbd", "JPEG", (1152, 1536)),
    "left": ("7693.png", "cd1dbc8447de72f0b4239cb6e76ea12c703df0812b1fc225ecb892c34db1b984", "JPEG", (1152, 1536)),
    "right": ("7684.png", "f5b5787cce36806a365251095f1c43138e4a12409e176c24af8a8406642117d1", "PNG", (1200, 1600)),
    "back": ("7776.png", "d9506845f6377ad465b291b8ba6bc0ff2e60340f836ad7c18c213c453e7bb393", "PNG", (1086, 1448)),
}

def audit(root):
    from PIL import Image
    results = {}
    for facing, (filename, expected_sha, expected_format, size) in EXPECTED.items():
        p = root / filename
        if not p.is_file():
            results[facing] = {"status": "MISSING", "filename": filename}
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        with Image.open(p) as im:
            fmt, dims = im.format, im.size
        ok = sha == expected_sha and fmt == expected_format and dims == size
        results[facing] = {
            "status": "PASS" if ok else "FAIL",
            "filename": filename,
            "sha256": sha,
            "format": fmt,
            "dimensions": list(dims),
            "facing": facing,
            "canon_approved": False,
            "joint_positions_measured": False,
        }
    return {
        "task": "MORWEN-RIG-04",
        "status": "PASS" if all(v["status"] == "PASS" for v in results.values()) else "BLOCKED",
        "references": results,
        "source_images_modified": False,
        "note": "Hash and format audit only. Reference coordinates and visual canon require review.",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    report = audit(args.input_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(report["status"])
    raise SystemExit(0 if report["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
