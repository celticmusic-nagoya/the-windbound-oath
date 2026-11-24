"""Recovery evidence preflight only. Never deletes a reservation.

An independent reconciler must confirm all writers are stopped, validate
off-runner checkpoint bytes and explicitly authorize the existing CAS release.
A completed Actions run alone cannot prove external AI writers are stopped.
"""
import re

def recovery_preflight(record, observed_token, run, checkpoint_verified, writers_stopped):
    if not re.fullmatch(r"[0-9a-f]{40}", observed_token or ""):
        raise ValueError("invalid observed lease token")
    if record.get("token") != observed_token:
        raise RuntimeError("lease identity mismatch")
    if not isinstance(record.get("run_id"), int) or record["run_id"] != run.get("id"):
        raise RuntimeError("owner run mismatch")
    if record.get("run_attempt") != run.get("run_attempt") or not isinstance(run.get("run_attempt"), int):
        raise RuntimeError("owner attempt mismatch")
    if record.get("head") != run.get("head_sha") or not re.fullmatch(r"[0-9a-f]{40}", record.get("head","")):
        raise RuntimeError("owner head mismatch")
    if run.get("status") != "completed" or run.get("conclusion") not in {"success","failure","cancelled","timed_out","startup_failure"}:
        raise RuntimeError("owner termination not established")
    if checkpoint_verified is not True or writers_stopped is not True:
        raise RuntimeError("independent reconciliation incomplete")
    return {"token": observed_token, "decision": "REVIEW_REQUIRED"}
