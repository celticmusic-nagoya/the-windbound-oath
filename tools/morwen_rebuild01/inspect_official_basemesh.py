#!/usr/bin/env python3
"""Non-destructive intake of the official Blender Studio CC0 base-mesh bundle.

Inventory only. No source asset is renamed, altered, adopted, or merged.
"""
import hashlib
import json
import pathlib
import sys
import zipfile

SOURCE = "https://mirror.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip"
LICENSE_SOURCE = "https://www.blender.org/download/demo-files/"

def main():
    archive = pathlib.Path(sys.argv[1])
    destination = pathlib.Path(sys.argv[2])
    if not archive.is_file():
        raise RuntimeError("Official archive missing")
    digest = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
    with zipfile.ZipFile(archive) as z:
        bad = z.testzip()
        if bad is not None:
            raise RuntimeError("ZIP CRC error: " + bad)
        entries = [
            {"path": info.filename, "bytes": info.file_size, "crc32": f"{info.CRC:08x}"}
            for info in z.infolist() if not info.is_dir()
        ]
        if not any(x["path"].lower().endswith(".blend") for x in entries):
            raise RuntimeError("Official bundle has no Blender asset")
        if any(pathlib.PurePosixPath(x["path"]).is_absolute()
               or ".." in pathlib.PurePosixPath(x["path"]).parts for x in entries):
            raise RuntimeError("Unsafe ZIP member path")
    result = {
        "source": SOURCE,
        "license_claim": "CC0 on official Blender demo files page",
        "license_source": LICENSE_SOURCE,
        "sha256": digest,
        "archive_bytes": archive.stat().st_size,
        "entry_count": len(entries),
        "entries": entries,
        "status": "SOURCE_INVENTORY_ONLY_NOT_SCULPT_NOT_ADOPTED",
        "art_qa": "NOT_RUN",
        "canonical_modified": False,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("OFFICIAL_BASE_SOURCE_INVENTORY_PASS", digest, len(entries))

if __name__ == "__main__":
    main()
