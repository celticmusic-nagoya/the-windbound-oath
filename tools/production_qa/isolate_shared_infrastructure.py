#!/usr/bin/env python3
"""Build an isolated, review-only shared-infrastructure bundle from tracked files.

Does not change repository state or merge PRs. Explicit allowlist prevents
unapproved Morwen geometry, references or other production assets from leaking.
"""
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ALLOWLIST = (
    ".github/workflows/two-blender-524-qualification.yml",
    ".github/workflows/two-production-pr-inventory.yml",
    "tools/production_qa/install_blender_524.sh",
    "tools/production_qa/validate_blender_runtime.py",
    "tools/production_qa/pr_workstream_guard.py",
    "docs/production/BLENDER_VERSION_STANDARD_20261118.md",
    "docs/production/PR_TRIAGE_INITIAL_20261118.json",
)
def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: isolate_shared_infrastructure.py OUTPUT_ZIP")
    dest = Path(sys.argv[1])
    tracked = set(subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0"))
    if not set(ALLOWLIST).issubset(tracked):
        raise SystemExit(f"Missing tracked files: {sorted(set(ALLOWLIST) - tracked)}")
    for path in ALLOWLIST:
        if path.startswith(("assets/", "tools/blender/", "images/")) or ".." in Path(path).parts:
            raise SystemExit(f"Unsafe allowlist entry: {path}")
    manifest = {"status": "REVIEW_ONLY_NOT_APPROVED_FOR_MERGE",
                "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "entries": [], "excluded_files": len(tracked) - len(ALLOWLIST)}
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in ALLOWLIST:
            # Read committed bytes, not potentially modified working-tree contents.
            data = subprocess.check_output(["git", "show", f"HEAD:{path}"])
            archive.writestr(path, data)
            manifest["entries"].append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        archive.writestr("ISOLATION_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(dest) as archive:
        names = set(archive.namelist())
        assert names == set(ALLOWLIST) | {"ISOLATION_MANIFEST.json"}
        for entry in manifest["entries"]:
            assert hashlib.sha256(archive.read(entry["path"])).hexdigest() == entry["sha256"]
    print(json.dumps({"result": "ISOLATED_SHARED_INFRASTRUCTURE_PASS", "entries": len(ALLOWLIST),
                      "excluded_files": manifest["excluded_files"], "output": str(dest)}))
if __name__ == "__main__":
    main()
