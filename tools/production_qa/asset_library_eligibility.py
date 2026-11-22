"""Read-only preflight for reusing an explicitly pinned library asset."""
import argparse
import json
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


def select_reuse(root, entries, *, asset_id, native_sha256, usage, dependency_fingerprint,
                 output_contract):
    """Resolve an exact catalog pin before verifying its license and files."""
    if not present(asset_id) or not matches_digest(native_sha256):
        raise ValueError("explicit asset ID and native SHA-256 required")
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError("catalog entries must be objects")
    candidates = [entry for entry in entries if entry.get("asset_id") == asset_id
                  and entry.get("native_sha256") == native_sha256]
    if len(candidates) != 1:
        return {"decision": "BLOCKED_AMBIGUOUS_PIN" if candidates else "BLOCKED_UNAVAILABLE_PIN"}
    entry = candidates[0]
    manifest = entry.get("manifest")
    files = manifest.get("files") if isinstance(manifest, dict) else None
    path = entry.get("native_path")
    if not present(path) or not isinstance(files, dict) or files.get(path) != native_sha256:
        return {"decision": "BLOCKED_ASSET_MANIFEST"}
    result = assess_reuse(root, entry, usage=usage, dependency_fingerprint=dependency_fingerprint,
                          output_contract=output_contract)
    if result["decision"] == "REUSE_ELIGIBLE":
        return {**result, "asset_id": asset_id, "native_path": path, "native_sha256": native_sha256}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    for option in ("asset-id", "native-sha256", "usage", "dependency-fingerprint", "output-contract"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    try:
        catalog = json.loads(args.catalog.read_text())
        if not isinstance(catalog, dict):
            raise ValueError("catalog must be an object")
        result = select_reuse(args.root, catalog.get("entries"), asset_id=args.asset_id,
                              native_sha256=args.native_sha256, usage=args.usage,
                              dependency_fingerprint=args.dependency_fingerprint,
                              output_contract=args.output_contract)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "REUSE_ELIGIBLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
