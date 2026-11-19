#!/usr/bin/env python3
"""Read-only audit of SHA256SUMS embedded in a GitHub Actions artifact ZIP."""
import argparse
import hashlib
import json
from pathlib import PurePosixPath
import zipfile


def audit_zip(path, sums_path):
    errors = []
    matched = 0
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if sums_path not in names:
            return {"status": "FAIL", "matched": 0, "errors": ["manifest_missing"]}
        prefix = str(PurePosixPath(sums_path).parent)
        for line in archive.read(sums_path).decode("utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                errors.append("malformed_line")
                continue
            digest, relative = parts
            relative = relative.lstrip("*")
            p = PurePosixPath(relative)
            if p.is_absolute() or ".." in p.parts or not relative:
                errors.append("unsafe_path")
                continue
            full = str(PurePosixPath(prefix) / p)
            if full not in names:
                errors.append(f"missing:{relative}")
                continue
            actual = hashlib.sha256(archive.read(full)).hexdigest()
            if actual != digest:
                errors.append(f"sha_mismatch:{relative}")
            else:
                matched += 1
    return {"status": "FAIL" if errors or matched == 0 else "PASS",
            "matched": matched, "errors": errors,
            "scope": "archive_byte_integrity_only"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_file")
    parser.add_argument("manifest_entry")
    args = parser.parse_args()
    result = audit_zip(args.zip_file, args.manifest_entry)
    print(json.dumps(result, indent=2))
    return int(result["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
