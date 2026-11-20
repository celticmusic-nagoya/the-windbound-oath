#!/usr/bin/env python3
"""Generate a deterministic, read-only handoff manifest for existing render outputs.

Usage: python tools/production_qa/build_visual_qa_handoff.py --input DIR --output DIR
Does not render, call AI APIs, modify inputs, or assert artistic approval.
"""
import argparse
import hashlib
import json
from pathlib import Path

ALLOWED = {".png", ".jpg", ".jpeg", ".blend", ".json", ".txt", ".md"}
MAX_BYTES = 2 * 1024 * 1024 * 1024

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--asset", default="morwen")
    args = parser.parse_args()
    source = Path(args.input).resolve(strict=True)
    dest = Path(args.output).resolve()
    if not source.is_dir():
        parser.error("--input must be a directory")
    if dest == source or source in dest.parents:
        parser.error("--output must not be within --input")
    files = []
    for f in sorted(source.rglob("*")):
        if f.is_symlink() or not f.is_file() or f.suffix.lower() not in ALLOWED:
            continue
        if f.stat().st_size > MAX_BYTES:
            continue
        files.append({"path": f.relative_to(source).as_posix(), "bytes": f.stat().st_size, "sha256": sha256(f)})
    if not files:
        parser.error("No supported input evidence found")
    # Stable across machines, timestamps and directory locations; changes with evidence bytes or paths.
    fingerprint_payload = json.dumps({"asset": args.asset, "inputs": files}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    input_fingerprint_sha256 = hashlib.sha256(fingerprint_payload).hexdigest()
    result = {
        "input_fingerprint_sha256": input_fingerprint_sha256,
        "schema": "two.visual_qa_handoff.v1",
        "asset": args.asset,
        "scope": "EVIDENCE_ONLY_NO_ARTISTIC_PASS",
        "inputs": files,
        "gates": {"G1": "NOT_RUN", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"},
        "claude_review": {
            "task": "Compare supplied renders against separately verified official reference; identify structural art defects with evidence; do not assert PASS without independent review.",
            "required": ["official_reference_sha256", "view_and_camera", "observed_defect", "evidence_path", "suggested_structural_fix", "confidence"]
        },
        "codex_fix": {
            "task": "Apply only verified approved non-destructive changes on existing owning PR; do not rerun stopped method families.",
            "required": ["target_file", "root_cause", "structural_change", "acceptance_test", "stop_condition"]
        },
        "notes": "No AI agent is invoked. A manifest is not a model, render, or G1-G4 approval."
    }
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / "visual_qa_handoff.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Generated {out} for {len(files)} evidence files")

if __name__ == "__main__":
    main()
