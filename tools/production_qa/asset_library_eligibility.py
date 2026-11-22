"""Read-only preflight for reusing an explicitly selected library asset."""
from pathlib import Path

from shared_blueprint_contract import matches_digest, present
from verify_actions_artifact import verify


def assess_reuse(root, entry, *, usage, dependency_fingerprint, output_contract):
    """Check licensed scope, dependency identity and the actual local evidence."""
    if not present(usage) or not matches_digest(dependency_fingerprint):
        raise ValueError("explicit usage and dependency fingerprint required")
    if not isinstance(entry, dict) or entry.get("dependency_fingerprint") != dependency_fingerprint:
        return {"decision": "BLOCKED_DEPENDENCIES"}
    license_record = entry.get("license")
    if (not isinstance(license_record, dict)
            or not present(license_record.get("id"))
            or license_record.get("reviewed") is not True
            or not isinstance(license_record.get("permitted_uses"), list)
            or usage not in license_record["permitted_uses"]
            or not present(license_record.get("evidence_path"))
            or not matches_digest(license_record.get("evidence_sha256"))):
        return {"decision": "BLOCKED_LICENSE"}
    manifest = entry.get("manifest")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        return {"decision": "BLOCKED_ASSET_MANIFEST"}
    evidence_path = license_record["evidence_path"]
    if manifest["files"].get(evidence_path) != license_record["evidence_sha256"]:
        return {"decision": "BLOCKED_LICENSE_EVIDENCE"}
    native = entry.get("native_path")
    if not present(native) or native == evidence_path or not matches_digest(manifest["files"].get(native)):
        return {"decision": "BLOCKED_ASSET_MANIFEST"}
    try:
        result = verify(Path(root), manifest, output_contract)
    except (ValueError, OSError):
        return {"decision": "BLOCKED_ASSET_BYTES"}
    return {"decision": "REUSE_ELIGIBLE", "verified_files": result["file_count"]}
