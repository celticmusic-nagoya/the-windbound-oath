#!/usr/bin/env python3
"""Map a #427 VRoid native checkpoint manifest (session_checkpoint.publish) onto the #468 planner record.

The #468 planner needs {path (relative to its root), sha256, reopened: True, fingerprint}. #427 publishes
{stage, sha256, fingerprint, path (absolute), reopened_bytes_match, remote_verified}. `reopened_bytes_match` proves byte
identity of a re-read file, not that VRoid Studio reopened the project, so the bridge only sets reopened=True when an
explicit app-reopen proof is supplied (sha256 of the file VRoid reopened + observed values). Otherwise the planner
correctly treats the stage as not yet reusable.
"""
from pathlib import Path


def to_planner_record(manifest, root, app_reopen=None):
    root = Path(root).resolve()
    p = Path(manifest["path"]).resolve()
    if not p.is_relative_to(root):
        raise ValueError("checkpoint outside planner root")
    ok_app = bool(app_reopen) and app_reopen.get("reopened_sha256") == manifest["sha256"] and bool(app_reopen.get("observed_values"))
    return {"path": p.relative_to(root).as_posix(), "sha256": manifest["sha256"], "fingerprint": manifest["fingerprint"],
            "reopened": bool(manifest.get("reopened_bytes_match")) and ok_app,
            "reopen_evidence": {"bytes": bool(manifest.get("reopened_bytes_match")), "vroid_app": ok_app},
            "remote_verified": bool(manifest.get("remote_verified"))}
