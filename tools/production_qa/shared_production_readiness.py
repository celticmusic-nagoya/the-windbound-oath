"""Bind an independently verified handoff to one queued production stage.

The coordinator verifies the referenced owner records. This module checks that
the resulting attestation applies to the job, writer inventory and inputs.
"""
import hashlib
import json
import math
import re


SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def matches_digest(value):
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def present(value):
    return isinstance(value, str) and bool(value.strip())


def readiness_issues(request, handoff, writer_paths):
    if not isinstance(handoff, dict):
        return ["handoff"]
    issues = []
    for key in ("asset_id", "stage", "head_sha", "branch", "workflow_path"):
        if not present(request.get(key)) or handoff.get(key) != request[key]:
            issues.append(key)
    if handoff.get("owner_ack_verified") is not True or not all(
            present(handoff.get(key)) for key in ("owner", "owner_ack_ref", "verified_by")):
        issues.append("owner_ack")
    if not all(present(handoff.get(key)) for key in ("recovery_authority", "recovery_authority_ref")):
        issues.append("recovery_authority")
    if not matches_digest(handoff.get("native_sha256")) or handoff["native_sha256"] != request.get("source_sha256"):
        issues.append("native_sha256")
    dependencies = handoff.get("dependencies")
    if (not isinstance(dependencies, dict) or dependencies != request.get("dependency_hashes")
            or any(not present(path) or not matches_digest(digest) for path, digest in dependencies.items())):
        issues.append("dependencies")
    stopped = handoff.get("stopped_writers")
    if (not isinstance(stopped, dict) or not stopped or not set(writer_paths) <= stopped.keys()
            or any(not present(path) or not present(ack) for path, ack in stopped.items())
            or handoff.get("writer_inventory_verified") is not True):
        issues.append("stopped_writers")
    design = handoff.get("design")
    if not isinstance(design, dict) or not matches_digest(design.get("sha256")) or (
            design["sha256"] != request.get("reference_sha256")):
        issues.append("design")
    else:
        tolerances = design.get("tolerances")
        if (not present(design.get("target_id")) or design["target_id"] != request.get("target_id")
                or not isinstance(tolerances, dict) or not tolerances
                or any(not present(metric) or type(limit) not in (int, float)
                       or limit < 0 or (type(limit) is float and not math.isfinite(limit))
                       for metric, limit in tolerances.items())):
            issues.append("design_tolerances")
    return issues


def handoff_digest(handoff):
    return hashlib.sha256(json.dumps(handoff, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()
