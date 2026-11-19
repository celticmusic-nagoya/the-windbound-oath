#!/usr/bin/env python3
"""Fail-closed read-only review of persistent job reservations.

This module never deletes refs, transfers ownership, dispatches jobs or
concludes that stale age alone permits a retry.
"""
from datetime import datetime, timezone
from classify_actions_jobs import fingerprint
from reserve_actions_job_ref import inspect_existing_ref, PREFIX


def assess(request, reservation, ledger_entry, snapshot, now,
           queued_hours=2, running_hours=3):
    key = fingerprint(request)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not isinstance(reservation, dict):
        raise ValueError("reservation evidence required")
    inspect_existing_ref(key, reservation.get("ref"), reservation.get("anchor_sha"))
    if not isinstance(ledger_entry, dict) or fingerprint(ledger_entry) != key:
        raise ValueError("matching ledger entry required")
    owner = ledger_entry.get("owner_pr")
    if type(owner) is not int or owner <= 0:
        raise ValueError("valid owner PR required")
    stamp = ledger_entry.get("updated_at")
    if not isinstance(stamp, str):
        raise ValueError("ledger update timestamp required")
    updated = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if updated.tzinfo is None or updated > now:
        raise ValueError("invalid ledger timestamp")
    age = (now - updated).total_seconds() / 3600
    status = ledger_entry.get("status")
    if status not in ("QUEUED", "IN_PROGRESS", "SUCCESS", "FAILED", "CANCELLED", "BLOCKED"):
        raise ValueError("unknown ledger status")
    # Snapshot must explicitly attest the exact run. Missing/partial snapshot
    # is not evidence that a job has stopped.
    if not isinstance(snapshot, dict) or snapshot.get("complete") is not True:
        return _result(key, owner, "BLOCKED", "snapshot missing or incomplete")
    if snapshot.get("fingerprint") != key:
        return _result(key, owner, "BLOCKED", "snapshot identity mismatch")
    run_id = ledger_entry.get("run_id")
    if type(run_id) is not int or run_id <= 0 or snapshot.get("run_id") != run_id:
        return _result(key, owner, "BLOCKED", "run identity not independently verified")
    remote_status = snapshot.get("status")
    remote_conclusion = snapshot.get("conclusion")
    if remote_status in ("queued", "in_progress", "waiting", "pending", "requested"):
        return _result(key, owner, "KEEP_RESERVED", "remote job remains active")
    if remote_status != "completed":
        return _result(key, owner, "BLOCKED", "unknown remote job state")
    if remote_conclusion == "success":
        if (ledger_entry.get("artifact_sha256_verified") is True
                and ledger_entry.get("artifact_accessible") is True
                and ledger_entry.get("output_contract_verified") is True):
            return _result(key, owner, "REUSE_VERIFIED", "verified success; retain reservation")
        return _result(key, owner, "REVIEW_REQUIRED", "success without independently verified artifact")
    if remote_conclusion in ("failure", "cancelled", "timed_out", "action_required"):
        return _result(key, owner, "REVIEW_REQUIRED", "terminal run requires owner review")
    return _result(key, owner, "BLOCKED", "unknown or ambiguous completion")

def _result(key, owner, decision, reason):
    return {"fingerprint": key, "owner_pr": owner, "decision": decision,
            "reason": reason, "dispatch_authorized": False,
            "ref_deletion_authorized": False, "owner_transfer_authorized": False}
