#!/usr/bin/env python3
"""Offline, read-only TWO Actions watchdog. Never dispatches, cancels, or posts."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from classify_actions_jobs import fingerprint, VALID

ACTIVE = {"QUEUED", "IN_PROGRESS"}
TERMINAL_FAILURE = {"FAILED", "CANCELLED", "BLOCKED"}


def audit(ledger, now, queued_hours=2, running_hours=3, owner_idle_hours=48):
    if not isinstance(ledger, list):
        raise ValueError("ledger must be an array")
    alerts = []
    for index, entry in enumerate(ledger):
        key = fingerprint(entry)
        status = entry.get("status")
        if status not in VALID:
            raise ValueError("invalid status in ledger entry " + str(index))
        owner = entry.get("owner_pr")
        if not isinstance(owner, int) or owner <= 0:
            raise ValueError("missing owner PR for ledger entry " + str(index))
        stamp = entry.get("updated_at")
        if not isinstance(stamp, str):
            raise ValueError("missing updated_at for ledger entry " + str(index))
        updated = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if updated.tzinfo is None:
            raise ValueError("updated_at must be timezone-aware")
        age = (now - updated).total_seconds() / 3600
        if age < 0:
            raise ValueError("ledger entry timestamp is in the future")
        issues = []
        if status == "QUEUED" and age >= queued_hours:
            issues.append("QUEUED_STALE")
        if status == "IN_PROGRESS" and age >= running_hours:
            issues.append("RUNNING_STALE")
        if status == "SUCCESS" and not (
            entry.get("artifact_sha256_verified") is True
            and entry.get("artifact_accessible") is True
            and entry.get("output_contract_verified") is True
        ):
            issues.append("ARTIFACT_UNVERIFIED")
        if status in TERMINAL_FAILURE:
            issues.append("FAILED_OR_BLOCKED")
        if age >= owner_idle_hours and status != "SUCCESS":
            issues.append("OWNER_INACTIVE")
        if issues:
            alerts.append({"owner_pr": owner, "asset_id": entry["asset_id"],
                           "stage": entry["stage"], "fingerprint": key,
                           "status": status, "age_hours": round(age, 2),
                           "alerts": issues, "run_id": entry.get("run_id")})
    return {"alert_count": len(alerts), "alerts": alerts, "read_only": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--now", help="ISO8601 time; defaults to UTC current time")
    args = parser.parse_args()
    now = (datetime.fromisoformat(args.now.replace("Z", "+00:00"))
           if args.now else datetime.now(timezone.utc))
    if now.tzinfo is None:
        raise ValueError("--now must be timezone-aware")
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    print(json.dumps(audit(ledger, now), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
