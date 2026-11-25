#!/usr/bin/env python3
"""Bounded, non-extracting ZIP inspection of Studio audit candidates."""
import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
import zipfile

IMAGE = re.compile(r"\.(?:png|jpe?g)$", re.I)
MODEL = re.compile(r"\.(?:glb|vrm)$", re.I)
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_ENTRY = 32 * 1024 * 1024
MAX_MEMBERS = 2000
MAX_TOTAL = 128 * 1024 * 1024

def valid_signature(name, prefix, size):
    ext = pathlib.PurePosixPath(name).suffix.lower()
    if ext == '.png':
        return prefix.startswith(b'\x89PNG\r\n\x1a\n')
    if ext in ('.jpg', '.jpeg'):
        return prefix.startswith(b'\xff\xd8\xff')
    return (len(prefix) >= 12 and prefix[:4] == b'glTF'
            and int.from_bytes(prefix[4:8], 'little') == 2
            and int.from_bytes(prefix[8:12], 'little') == size)


def inspect_zip(path):
    result = {"safe_images": 0, "safe_models": 0, "rejected_members": 0, "image_sha256": [], "model_sha256": []}
    with zipfile.ZipFile(path) as z:
        if len(z.infolist()) > MAX_MEMBERS:
            raise ValueError("too many ZIP members")
        if sum(i.file_size for i in z.infolist()) > MAX_TOTAL:
            raise ValueError('aggregate uncompressed size exceeded')
        seen = set()
        for info in z.infolist():
            name = info.filename
            parts = pathlib.PurePosixPath(name).parts
            unsafe = (name.startswith("/") or "\\" in name or ".." in parts or info.is_dir()
                      or info.file_size <= 0 or info.file_size > MAX_ENTRY
                      or (info.external_attr >> 16) & 0o170000 == 0o120000)
            kind = "image" if IMAGE.search(name) else "model" if MODEL.search(name) else None
            duplicate = name.casefold() in seen
            seen.add(name.casefold())
            if unsafe or duplicate or kind is None:
                result["rejected_members"] += 1
                continue
            digest = hashlib.sha256()
            count = 0
            prefix = b''
            with z.open(info) as stream:
                while chunk := stream.read(1024 * 1024):
                    if not prefix:
                        prefix = chunk[:12]
                    count += len(chunk)
                    if count > MAX_ENTRY:
                        raise ValueError("entry exceeded size limit")
                    digest.update(chunk)
            if not valid_signature(name, prefix, count):
                result["rejected_members"] += 1
                continue
            result[f"safe_{kind}s"] += 1
            result[f"{kind}_sha256"].append(digest.hexdigest())
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_json")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--output", default="studio-zip-inspection.json")
    args = parser.parse_args()
    if not 1 <= args.limit <= 5:
        parser.error("--limit must be 1..5")
    repo = os.environ["GITHUB_REPOSITORY"]
    candidates = json.loads(pathlib.Path(args.audit_json).read_text())["candidates"]
    results = []
    with tempfile.TemporaryDirectory(prefix="studio-audit-") as directory:
        for item in candidates[:args.limit]:
            row = {k: item[k] for k in ("artifact_id", "run_id", "category", "head", "name")}
            if item["size_bytes"] <= 0 or item["size_bytes"] > MAX_ARCHIVE or item["expired"]:
                row["status"] = "SKIPPED_ARCHIVE_SIZE_OR_EXPIRY"
            else:
                dest = pathlib.Path(directory) / f"{item['artifact_id']}.zip"
                with dest.open("wb") as stream:
                    subprocess.run(["gh", "api", f"repos/{repo}/actions/artifacts/{item['artifact_id']}/zip"], stdout=stream, check=True)
                if dest.stat().st_size > MAX_ARCHIVE:
                    row["status"] = "SKIPPED_DOWNLOADED_ARCHIVE_SIZE"
                else:
                    try:
                        row.update(inspect_zip(dest))
                        row["status"] = "ZIP_INSPECTED_NOT_PUBLICATION_APPROVED"
                    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile, NotImplementedError):
                        row["status"] = "REJECTED_INVALID_OR_UNSUPPORTED_ZIP"
            results.append(row)
    pathlib.Path(args.output).write_text(json.dumps({"status": "ISOLATED_REVIEW_ONLY", "inspected": results}, indent=2) + "\n")
    print(json.dumps([{"artifact_id": x["artifact_id"], "status": x["status"],
                       "images": x.get("safe_images"), "models": x.get("safe_models")} for x in results]))

if __name__ == "__main__":
    main()
