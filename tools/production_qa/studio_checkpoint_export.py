"""Read-only Studio metadata intake from a restored, verified checkpoint.

A producer can include a JSON export descriptor as a checkpoint evidence file.
The Studio owner supplies independent publication approvals pinned to the exact
descriptor SHA. This tool does not publish, extract an archive, or assign QA.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import re

from shared_blueprint_contract import matches_digest, present
from shared_git_checkpoint_store import files_for
from verify_actions_artifact import verify


HEAD = re.compile(r"[0-9a-f]{40}\Z")
IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
MODELS = {".glb", ".vrm"}
QA = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
ADOPTION = {"UNDETERMINED", "CANDIDATE", "ADOPTED", "REJECTED"}


def check_files(root, files):
    verify(root, {"output_contract": "studio-export", "files": files}, "studio-export")


def safe_path(name):
    return (present(name) and "\\" not in name and not PurePosixPath(name).is_absolute()
            and all(part not in ("", ".", "..", ".git") for part in name.split("/"))
            and not any(ord(character) < 32 for character in name))


def export_records(root, ledger, approvals):
    """Return explicitly approved metadata, failing closed on invalid selections."""
    root = Path(root).resolve(strict=True)
    files_for(ledger)
    native_paths = {entry["path"] for entry in ledger.values()}
    if not isinstance(approvals, list):
        raise ValueError("Studio publication approvals must be a list")
    records = []
    keys = set()
    for approval in approvals:
        if not isinstance(approval, dict) or not (
            approval.get("public") is True and approval.get("redistribution_verified") is True
            and present(approval.get("review_ref"))
        ):
            raise ValueError("Studio publication approval required")
        stage = approval.get("checkpoint_stage")
        name = approval.get("descriptor_path")
        digest = approval.get("descriptor_sha256")
        if not present(stage) or stage not in ledger or not safe_path(name) or not matches_digest(digest):
            raise ValueError("invalid Studio descriptor pin")
        evidence = ledger[stage].get("files", {})
        if evidence.get(name) != digest or name in native_paths:
            raise ValueError("Studio descriptor not bound to checkpoint")
        check_files(root, {name: digest})
        if (root / name).stat().st_size > 65536:
            raise ValueError("Studio descriptor exceeds metadata limit")
        data = json.loads((root / name).read_text())
        if not isinstance(data, dict):
            raise ValueError("Studio descriptor must be an object")
        local = data.get("checkpoint_path")
        artifact_path = data.get("path")
        sha = data.get("sha256")
        if (not safe_path(local) or not safe_path(artifact_path) or local in native_paths
                or not matches_digest(sha) or evidence.get(local) != sha):
            raise ValueError("Studio output is not bound evidence or is a native file")
        suffix = PurePosixPath(artifact_path).suffix.lower()
        if suffix != PurePosixPath(local).suffix.lower() or suffix not in IMAGES | MODELS:
            raise ValueError("unsupported Studio publication format")
        if suffix in MODELS and approval.get("embedded_model_verified") is not True:
            raise ValueError("Studio model requires independent embedded-export verification")
        if (not present(data.get("head")) or not HEAD.fullmatch(data["head"])
                or any(type(data.get(key)) is not int or data[key] <= 0 for key in ("run_id", "artifact_id"))
                or not matches_digest(data.get("artifact_sha256")) or not present(data.get("stage"))):
            raise ValueError("Studio provenance incomplete")
        expires = data.get("expires_at")
        if not present(expires) or datetime.fromisoformat(expires).utcoffset() is None:
            raise ValueError("Studio artifact expiry must include a timezone")
        qa = data.get("qa")
        adoption = data.get("adoption")
        if (not isinstance(qa, dict) or set(qa) != {"G1", "G2", "G3", "G4"}
                or any(not present(value) or value not in QA for value in qa.values())
                or not present(adoption) or adoption not in ADOPTION):
            raise ValueError("Studio QA and adoption must be recorded explicitly")
        key = (data["artifact_id"], artifact_path)
        if key in keys:
            raise ValueError("duplicate Studio artifact entry")
        keys.add(key)
        check_files(root, {local: sha})
        public = {key: data[key] for key in ("path", "sha256", "head", "run_id", "artifact_id",
                                              "artifact_sha256", "expires_at", "stage", "qa", "adoption")}
        records.append(public)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--approvals", type=Path, required=True, help="trusted Studio owner approval JSON")
    args = parser.parse_args()
    try:
        ledger = json.loads((args.checkpoint / "ledger.json").read_text())
        approvals = json.loads(args.approvals.read_text())
        records = export_records(args.checkpoint, ledger, approvals)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(records, sort_keys=True))


if __name__ == "__main__":
    main()
