#!/usr/bin/env python3
"""Offline dependency and safety audit for the seven-file shared review bundle.

No network, Blender execution, repo mutation, PR operation, or asset loading.
"""
import ast
import json
import re
import sys
import zipfile
from pathlib import Path

REQUIRED = {
    ".github/workflows/two-blender-524-qualification.yml",
    ".github/workflows/two-production-pr-inventory.yml",
    "tools/production_qa/install_blender_524.sh",
    "tools/production_qa/validate_blender_runtime.py",
    "tools/production_qa/pr_workstream_guard.py",
    "docs/production/BLENDER_VERSION_STANDARD_20261118.md",
    "docs/production/PR_TRIAGE_INITIAL_20261118.json",
}
def main(path):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        assert names == REQUIRED | {"ISOLATION_MANIFEST.json"}, "Unexpected or missing ZIP member"
        manifest = json.loads(z.read("ISOLATION_MANIFEST.json"))
        assert manifest["status"] == "REVIEW_ONLY_NOT_APPROVED_FOR_MERGE"
        assert {e["path"] for e in manifest["entries"]} == REQUIRED
        for entry in manifest["entries"]:
            import hashlib
            raw = z.read(entry["path"])
            assert len(raw) == entry["bytes"]
            assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
        scripts = [p for p in REQUIRED if p.endswith(".py")]
        for script in scripts:
            ast.parse(z.read(script).decode("utf-8"), filename=script)
        installer = z.read("tools/production_qa/install_blender_524.sh").decode()
        runtime = z.read(".github/workflows/two-blender-524-qualification.yml").decode()
        inventory = z.read(".github/workflows/two-production-pr-inventory.yml").decode()
        assert "sha256sum -c expected.sha256" in installer
        assert "mirror.blender.org/release/Blender5.2" in installer
        assert "bash tools/production_qa/install_blender_524.sh" in runtime
        assert "tools/production_qa/validate_blender_runtime.py" in runtime
        assert "tools/production_qa/pr_workstream_guard.py" in inventory
        assert "pull-requests: read" in inventory
        assert "persist-credentials: false" in runtime and "persist-credentials: false" in inventory
        assert not any(p.startswith(("assets/", "tools/blender/")) or p.endswith((".blend", ".png", ".glb")) for p in REQUIRED)
        report = {"status": "PASS_STATIC_BUNDLE_AUDIT", "files": len(REQUIRED),
                  "checks": ["allowlist", "manifest_hashes", "python_syntax",
                             "installer_sha", "runtime_dependency_edges",
                             "inventory_read_permissions", "no_3d_assets"],
                  "limits": ["Not a clean-branch install test", "No runtime execution in this audit",
                             "Not approved for merge", "No independent G1-G4 asset approval"]}
        print(json.dumps(report, ensure_ascii=False))
if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_shared_infrastructure_bundle.py ZIP")
    main(Path(sys.argv[1]))
