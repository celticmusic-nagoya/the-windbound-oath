"""Bind an independently verified handoff to one queued production stage.

The coordinator verifies the referenced owner records. This module checks that
the resulting attestation applies to the job, writer inventory and inputs.
"""
from shared_blueprint_contract import digest_record, matches_digest, present, target_issues


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
    return issues + target_issues(handoff.get("design"), request)


def handoff_digest(handoff):
    return digest_record(handoff)
