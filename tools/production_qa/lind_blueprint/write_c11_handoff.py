"""Emit a fail-closed, portable C11 session checkpoint; no Blender or AI API."""
import argparse
import hashlib
import json
from pathlib import Path

SCRIPT = Path("tools/production_qa/lind_blueprint/c11_recess_patch.py")
SOURCE_SHA = "0b6b0f3f6e8e270594cdac5fc81008ffe5210b7e98de352d826360dfd6676508"
C10_ARTIFACT = "https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44653659021"
OWNER = "feature/lind-cliff-rock-art-study-20261118"

def build(commit, run_id, preflight):
    digest = hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
    return {
        "schema": "two.c11.handoff.v1",
        "asset": "windwaiting-cliff",
        "stage": "C11_local_recess_patch",
        "owner_pr": 421,
        "branch": OWNER,
        "head_commit": commit,
        "workflow_run_id": run_id,
        "source": {
            "candidate": "hero_fracture_UNAPPROVED.blend",
            "expected_sha256": SOURCE_SHA,
            "artifact_reference": C10_ARTIFACT,
            "verified_against_actual_blend": False,
        },
        "script": str(SCRIPT),
        "script_sha256": digest,
        "checkpoint": "PREFLIGHT_PASS" if preflight == "success" else "PREFLIGHT_FAILED",
        "preflight": preflight,
        "outputs": {"c11_blend": None, "renders": [], "qa_report": None},
        "gates": {"G1": "BLOCKED", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"},
        "next_task": "Verify exact C10 .blend SHA and carrier in Blender 5.3, then execute bounded C11 patch and render only if safe",
        "stop_conditions": ["input SHA mismatch", "missing carrier", "disjoint region", "boundary displacement", "nonmanifold geometry", "two failures of same root cause"],
        "resume_rule": "Read main AGENTS.md and SESSION_CONTINUITY_INDEX.md; compare this checkpoint with live PR HEAD, Actions, artifact SHA and source; never claim Blender run from preflight",
        "approval": "UNAPPROVED_CANDIDATE",
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--preflight", choices=("success", "failure", "cancelled"), required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    data = build(args.commit, args.run_id, args.preflight)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
