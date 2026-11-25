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


def policy_authority(registry, reference):
    """Classify an exact repo-relative reference from a verified registry snapshot."""
    if reference in registry["superseded"]:
        return "HISTORICAL"
    if reference in registry["active"]:
        return "ACTIVE"
    return "REFERENCE_ONLY"


def policy_migration_issues(root, registry, sources):
    """Check that every migration source is present and still in force."""
    from hashlib import sha256
    from pathlib import PurePosixPath

    v5 = registry["production_first_v5"]
    authority = v5["authority_resolution"]
    active = registry["active"]
    candidates = authority["retirement_candidates"]
    if (len(candidates) != 19 or set(candidates) != sources.keys()
            or len(active) != 20 or set(active) != sources.keys() | {v5["policy"]}):
        return ["migration inventory"]
    if authority["status"] != "MIGRATION_PENDING":
        return ["migration status"]
    issues = []
    for reference in active:
        path = PurePosixPath(reference)
        if (path.as_posix() != reference or path.parts[:2] != ("docs", "policy")
                or len(path.parts) != 3 or path.suffix != ".md"):
            issues.append(f"invalid path: {reference}")
            continue
        if policy_authority(registry, reference) != "ACTIVE":
            issues.append(f"authority conflict: {reference}")
            continue
        document = root / reference
        if not document.is_file() or document.is_symlink():
            issues.append(f"missing source: {reference}")
        elif reference in sources and sha256(document.read_bytes()).hexdigest() != sources[reference]:
            issues.append(f"source changed: {reference}")
    return issues


def main():
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Check the Production-First v5 transition snapshot")
    parser.add_argument("references", nargs="*", help="exact repository-relative policy paths")
    parser.add_argument("--extract", action="store_true", help="emit SHA-verified sources with line numbers")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    policy_dir = root / "docs/policy"
    try:
        registry = json.loads((policy_dir / "POLICY_REGISTRY.json").read_text(encoding="utf-8"))
        sources = json.loads((policy_dir / "PRODUCTION_FIRST_V5_SOURCES.json").read_text(encoding="utf-8"))
        issues = policy_migration_issues(root, registry, sources)
        decisions = {reference: policy_authority(registry, reference) for reference in args.references}
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"issues": [str(error)]}))
        return 1
    report = {"issues": issues, "authority": decisions}
    if args.extract and not issues:
        report["source_text"] = {
            reference: {
                "sha256": digest,
                "lines": dict(enumerate((root / reference).read_text(encoding="utf-8").splitlines(), 1)),
            }
            for reference, digest in sources.items()
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(issues) or any(decision != "ACTIVE" for decision in decisions.values()))


if __name__ == "__main__":
    raise SystemExit(main())
