#!/usr/bin/env python3
"""Deterministic, fail-closed TWO stage checkpoint writer/validator. Stdlib only.

This records evidence, never grants artistic or canonical approval.
"""
import argparse
import hashlib
import json
from pathlib import Path

GATES = ("G1", "G2", "G3", "G4")
VERDICTS = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
STATES = {"READY", "PREFLIGHT_FAILED", "RENDERING", "RENDER_FAILED",
          "TECH_QA_FAILED", "WAITING_FOR_ART_QA", "BLOCKED", "NEXT_STAGE_READY"}
REQUIRED = ("asset_id", "stage", "owner", "owning_pr", "branch", "head_sha",
            "input_sha256", "blueprint_sha256", "tool_versions", "method_family",
            "retry_count", "attempt_ledger_ref", "output_artifact_ids",
            "output_sha256", "error_category", "blocker", "next_action",
            "next_action_preconditions", "last_verified_at")

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def validate(d):
    if d.get("schema_version") != "two.stage_checkpoint.v1":
        raise ValueError("unsupported schema")
    if d.get("status") not in STATES:
        raise ValueError("invalid status")
    if any(k not in d for k in REQUIRED):
        raise ValueError("missing required checkpoint field")
    if not isinstance(d.get("gates"), dict) or set(d["gates"]) != set(GATES):
        raise ValueError("missing or unexpected quality gates")
    if any(v not in VERDICTS for v in d["gates"].values()):
        raise ValueError("invalid quality gate")
    if not isinstance(d["retry_count"], int) or d["retry_count"] < 0:
        raise ValueError("invalid retry count")
    if d["status"] == "NEXT_STAGE_READY" and not d["next_action"]:
        raise ValueError("missing next action")
    if d["status"] == "NEXT_STAGE_READY" and d["gates"]["G2"] != "PASS" and d["next_action"] in ("adopt", "merge", "publish"):
        raise ValueError("cannot adopt or publish without independent art QA")
    if not isinstance(d["head_sha"], str) or len(d["head_sha"]) != 40 or any(c not in "0123456789abcdef" for c in d["head_sha"]):
        raise ValueError("invalid HEAD SHA")
    return d

def build(args):
    source = Path(args.evidence).resolve(strict=True)
    if not source.is_dir():
        raise ValueError("evidence must be a directory")
    files = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlink in evidence")
        if path.is_file():
            files.append({"path": path.relative_to(source).as_posix(),
                          "sha256": digest(path), "bytes": path.stat().st_size})
    if not files:
        raise ValueError("no evidence")
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    d = {"schema_version": "two.stage_checkpoint.v1", "asset_id": args.asset,
         "stage": args.stage, "owner": args.owner, "owning_pr": args.pr,
         "branch": args.branch, "head_sha": args.head_sha,
         "input_sha256": fingerprint, "blueprint_sha256": args.blueprint_sha,
         "tool_versions": {}, "method_family": args.method_family,
         "retry_count": 0, "attempt_ledger_ref": "", "output_artifact_ids": [],
         "output_sha256": {f["path"]: f["sha256"] for f in files},
         "error_category": "", "blocker": "", "next_action": args.next_action,
         "next_action_preconditions": [], "last_verified_at": "",
         "status": "WAITING_FOR_ART_QA", "gates": {k: "NOT_RUN" for k in GATES},
         "evidence": files, "input_fingerprint_sha256": fingerprint,
         "scope": "EVIDENCE_ONLY_NO_ARTISTIC_PASS"}
    return validate(d)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence")
    p.add_argument("--output")
    p.add_argument("--asset", default="morwen")
    p.add_argument("--stage", default="visual_qa_handoff")
    p.add_argument("--owner", default="unassigned")
    p.add_argument("--pr", type=int, default=427)
    p.add_argument("--branch", default="")
    p.add_argument("--head-sha", default="")
    p.add_argument("--blueprint-sha", default="")
    p.add_argument("--method-family", default="evidence_handoff")
    p.add_argument("--next-action", default="independent_art_review")
    p.add_argument("--validate")
    args = p.parse_args()
    if args.validate:
        validate(json.loads(Path(args.validate).read_text()))
        print("TWO_CHECKPOINT_VALIDATE_PASS")
        return
    if not args.evidence or not args.output:
        p.error("--evidence and --output are required")
    d = build(args)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print("TWO_CHECKPOINT_WRITTEN_EVIDENCE_ONLY")

if __name__ == "__main__":
    main()
