#!/usr/bin/env python3
"""Read-only bridge from GitHub run snapshot to reservation recovery evidence.

A bounded list response is not proof of completeness or absence. Only a
uniquely matched run with explicit ledger head/branch may be reviewed.
No dispatch or reservation mutation is permitted.
"""
import re
from classify_actions_jobs import fingerprint
from assess_actions_reservation_recovery import assess

SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def review(request, reservation, ledger_entry, snapshot, now):
    key = fingerprint(request)
    if not isinstance(snapshot, dict) or snapshot.get("read_only") is not True:
        raise ValueError("read-only GitHub snapshot required")
    if not isinstance(snapshot.get("runs"), list):
        raise ValueError("snapshot runs required")
    run_id = ledger_entry.get("run_id")
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("explicit run ID required")
    matches = [run for run in snapshot["runs"]
               if isinstance(run, dict) and run.get("run_id") == run_id]
    if len(matches) != 1:
        return _blocked(key, ledger_entry, "missing or duplicate exact run in bounded snapshot")
    run = matches[0]
    if (not isinstance(ledger_entry.get("head_sha"), str)
            or SHA40.fullmatch(ledger_entry["head_sha"]) is None
            or run.get("head_sha") != ledger_entry["head_sha"]
            or not isinstance(ledger_entry.get("branch"), str)
            or run.get("head_branch") != ledger_entry["branch"]):
        return _blocked(key, ledger_entry, "HEAD or branch mismatch")
    # Explicit match of a single run is sufficient to observe its state, not
    # to conclude that there are no competing runs or that artifacts are valid.
    observed = {"complete": True, "fingerprint": key, "run_id": run_id,
                "status": run.get("status"), "conclusion": run.get("conclusion")}
    result = assess(request, reservation, ledger_entry, observed, now)
    # Existing ledger artifact flags are not cryptographic proof here.
    # Never promote them to a reusable artifact without external verification.
    if result["decision"] == "REUSE_VERIFIED":
        return _blocked(key, ledger_entry, "external artifact proof not supplied")
    return result


def _blocked(key, ledger_entry, reason):
    return {"fingerprint": key, "owner_pr": ledger_entry.get("owner_pr"),
            "decision": "BLOCKED", "reason": reason,
            "dispatch_authorized": False, "ref_deletion_authorized": False,
            "owner_transfer_authorized": False}
