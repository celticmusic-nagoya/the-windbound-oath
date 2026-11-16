#!/usr/bin/env python3
"""Offline rights/provenance preflight for NONCANONICAL 3D AI technical canaries.

PASS here does not mean that model weights, dependency licenses, GPU inference,
art quality, or commercial redistribution have been verified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SOURCES = {
    "TripoSR": {"code_license": "MIT", "weights_tag": "MIT",
                "repo": "https://github.com/VAST-AI-Research/TripoSR"},
    "InstantMesh": {"code_license": "Apache-2.0", "weights_tag": "Apache-2.0",
                    "repo": "https://github.com/TencentARC/InstantMesh"},
}
MAX_INPUT_BYTES = 10 * 1024 * 1024

def assess(image: Path, *, model: str, source_class: str, external_upload: bool,
           expected_sha256: str | None = None) -> dict:
    blockers = []
    if model not in SOURCES:
        blockers.append("Unsupported model: no checked source record")
    if source_class != "project-generated-synthetic-canary":
        blockers.append("Source ownership/license not independently proven")
    if external_upload:
        blockers.append("External transfer not authorized by this preflight")
    if not image.exists() or not image.is_file():
        blockers.append("Local candidate image missing")
        content_sha = None
        size = None
    else:
        size = image.stat().st_size
        if size > MAX_INPUT_BYTES:
            blockers.append("Input exceeds 10MB canary limit")
            content_sha = None
        else:
            content_sha = hashlib.sha256(image.read_bytes()).hexdigest()
        if image.suffix.lower() != ".png":
            blockers.append("Only PNG technical canaries supported")
        if expected_sha256 and expected_sha256 != content_sha:
            blockers.append("Input SHA256 mismatch")
    metadata = SOURCES.get(model)
    return {
        "status": "BLOCKED" if blockers else "PASS_INPUT_ONLY_NOT_MODEL_EXECUTION",
        "model": model,
        "source_class": source_class,
        "image_sha256": content_sha,
        "input_size_bytes": size,
        "reference_model_license": metadata,
        "blockers": blockers,
        "commercial_rights_complete": "NOT_RUN",
        "dependency_license_audit": "NOT_RUN",
        "model_weights_download": "NOT_RUN",
        "gpu_inference": "NOT_RUN",
        "output_mesh": "NOT_RUN",
        "G1": "BLOCKED",
        "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN",
    }

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--model", choices=sorted(SOURCES), default="TripoSR")
    p.add_argument("--source-class", required=True)
    p.add_argument("--expected-sha256", default=None)
    p.add_argument("--external-upload", action="store_true")
    args = p.parse_args()
    if args.out.exists():
        p.error("Refusing to overwrite previous QA evidence")
    result = assess(args.image, model=args.model, source_class=args.source_class,
                    external_upload=args.external_upload,
                    expected_sha256=args.expected_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print("AI3D_PILOT_PREFLIGHT=" + json.dumps({
        "status": result["status"], "blockers": result["blockers"],
        "image_sha256": result["image_sha256"],
        "gpu_inference": result["gpu_inference"]}, sort_keys=True))
    return 0 if result["status"].startswith("PASS_INPUT") else 1

if __name__ == "__main__":
    raise SystemExit(main())
