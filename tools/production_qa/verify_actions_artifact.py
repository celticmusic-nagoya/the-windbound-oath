#!/usr/bin/env python3
"""Offline byte-level verification of extracted Actions artifact files.

Manifest format: {"output_contract": "...", "files": {"relative/path": "sha256hex"}}
A valid report is evidence for local files only, not remote Artifact accessibility,
origin, license, canonical adoption, or G1-G4.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def verify(root, manifest, expected_contract):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("artifact root must be a directory")
    if not isinstance(manifest, dict) or not isinstance(expected_contract, str) or not expected_contract:
        raise ValueError("invalid manifest or expected contract")
    if manifest.get("output_contract") != expected_contract:
        raise ValueError("output contract mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("nonempty files dictionary required")
    verified = []
    for relative, expected in sorted(files.items()):
        if not isinstance(relative, str) or not relative or "\\" in relative:
            raise ValueError("invalid artifact relative path")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or any(part in (".", "..") for part in relative.split("/")):
            raise ValueError("unsafe artifact relative path")
        if not isinstance(expected, str) or SHA256.fullmatch(expected) is None:
            raise ValueError("invalid SHA256 digest")
        path = root.joinpath(*pure.parts)
        if path.is_symlink():
            raise ValueError("symlink artifact file prohibited")
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError("artifact path escapes root or is not a file")
        digest = hashlib.sha256()
        with resolved.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != expected:
            raise ValueError("artifact SHA256 mismatch: " + relative)
        verified.append(relative)
    return {"local_sha256_verified": True, "output_contract": expected_contract,
            "file_count": len(verified), "files": verified,
            "remote_artifact_accessible": "NOT_VERIFIED",
            "provenance": "NOT_VERIFIED", "qa_gates": "NOT_RUN"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-contract", required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(json.dumps(verify(args.root, manifest, args.expected_contract),
                     sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
