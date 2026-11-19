#!/usr/bin/env python3
"""Fail-closed, read-only reconciliation of an explicit job ledger and run snapshot.

This tool does not claim cross-run atomicity, infer work identity from workflow
names, modify GitHub, dispatch, or cancel runs.
"""
import argparse
import json
from pathlib import Path
from classify_actions_jobs import fingerprint, VALID

GITHUB_STATES = {"queued", "in_progress", "waiting", "pending", "requested", "completed"}
CONCLUSIONS = {"success", "failure", "cancelled", "timed_out", "skipped", "neutral", "action_required", "stale"}


def reconcile(ledger, snapshot):
    if not isinstance(ledger, list) or not isinstance(snapshot, dict):
        raise ValueError("expected ledger array and snapshot object")
    if snapshot.get("read_only") is not True or not isinstance(snapshot.get("runs"), list):
        raise ValueError("invalid run snapshot")
    runs = {}
    for run in snapshot["runs"]:
        run_id = run.get("run_id")
        if not isinstance(run_id, int) or run_id <= 0:
            raise ValueError("invalid run ID")
        if run_id in runs and runs[run_id] != run:
            raise ValueError("conflicting duplicate run ID")
        runs[run_id] = run
    decisions = []
    seen = set()
    for entry in ledger:
        key = fingerprint(entry)
        status = entry.get("status")
        if status not in VALID:
            raise ValueError("invalid ledger status")
        run_id = entry.get("run_id")
        if not isinstance(run_id, int) or run_id <= 0:
            decisions.append({"fingerprint": key, "decision": "REVIEW_REQUIRED",
                              "reason": "missing explicit positive run_id"})
            continue
        if run_id in seen:
            raise ValueError("run ID assigned to multiple ledger records")
        seen.add(run_id)
        run = runs.get(run_id)
        if run is None:
            decisions.append({"fingerprint": key, "run_id": run_id,
                              "decision": "REVIEW_REQUIRED",
                              "reason": "run not present in bounded snapshot; not evidence of absence"})
            continue
        if entry.get("head_sha") != run.get("head_sha") or entry.get("branch") != run.get("head_branch"):
            decisions.append({"fingerprint": key, "run_id": run_id,
                              "decision": "REVIEW_REQUIRED",
                              "reason": "run identity (HEAD/branch) mismatch"})
            continue
        gh_status, conclusion = run.get("status"), run.get("conclusion")
        if gh_status not in GITHUB_STATES:
            raise ValueError("unknown GitHub run status")
        if gh_status == "completed" and conclusion not in CONCLUSIONS:
            raise ValueError("unknown completed run conclusion")
        expected = {
            "queued": "QUEUED", "waiting": "QUEUED",
            "pending": "QUEUED", "requested": "QUEUED",
            "in_progress": "IN_PROGRESS",
        }.get(gh_status)
        if gh_status == "completed":
            expected = {"success": "SUCCESS", "failure": "FAILED",
                        "cancelled": "CANCELLED", "timed_out": "FAILED",
                        "stale": "FAILED"}.get(conclusion)
        decision = "CONSISTENT" if expected == status else "REVIEW_REQUIRED"
        if expected is None:
            decision = "REVIEW_REQUIRED"
        if decision == "CONSISTENT" and status == "SUCCESS":
            if not (entry.get("artifact_sha256_verified") is True
                    and entry.get("artifact_accessible") is True
                    and entry.get("output_contract_verified") is True):
                decision = "REVIEW_REQUIRED"
        decisions.append({"fingerprint": key, "run_id": run_id,
                          "decision": decision, "ledger_status": status,
                          "observed_status": gh_status, "observed_conclusion": conclusion})
    return {"read_only": True, "decisions": decisions,
            "review_count": sum(x["decision"] != "CONSISTENT" for x in decisions),
            "note": "No writes, no atomic reservation, no artifact verification performed"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    print(json.dumps(reconcile(ledger, snapshot), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
