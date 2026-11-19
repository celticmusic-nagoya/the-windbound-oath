#!/usr/bin/env python3
"""Offline, fail-closed TWO Actions planning. No GitHub API, dispatch or cancellation."""
import argparse
import hashlib
import json
from pathlib import Path

FIELDS = ("asset_id", "stage", "source_sha256", "script_sha256",
          "config_sha256", "tool_version", "reference_sha256", "output_contract")
VALID = {"SUCCESS", "QUEUED", "IN_PROGRESS", "FAILED", "CANCELLED", "BLOCKED"}


def fingerprint(job):
    missing = [k for k in FIELDS if not isinstance(job.get(k), str) or not job[k].strip()]
    if missing:
        raise ValueError("missing required job fields: " + ", ".join(missing))
    return hashlib.sha256(json.dumps({k: job[k] for k in FIELDS},
                                      sort_keys=True, ensure_ascii=False,
                                      separators=(",", ":")).encode()).hexdigest()


def classify(request, ledger):
    key = fingerprint(request)
    asset, stage = request["asset_id"], request["stage"]
    same = []
    overlapping = []
    for old in ledger:
        old_key = fingerprint(old)
        if old.get("status") not in VALID:
            raise ValueError("invalid ledger status")
        if old_key == key:
            same.append(old)
        elif old["asset_id"] == asset and old["stage"] == stage:
            overlapping.append(old)
    active = [x for x in same if x["status"] in ("QUEUED", "IN_PROGRESS")]
    if active:
        return {"decision": "REUSE_ACTIVE", "fingerprint": key,
                "reason": "identical job already active", "run_id": active[0].get("run_id")}
    complete = [x for x in same if x["status"] == "SUCCESS"
                and x.get("artifact_sha256_verified") is True
                and x.get("artifact_accessible") is True
                and x.get("output_contract_verified") is True]
    if complete:
        return {"decision": "REUSE_SUCCESS", "fingerprint": key,
                "reason": "verified identical artifact", "run_id": complete[0].get("run_id")}
    if overlapping:
        return {"decision": "REVIEW_REQUIRED", "fingerprint": key,
                "reason": "same asset/stage with different inputs or method"}
    if same:
        return {"decision": "REVIEW_REQUIRED", "fingerprint": key,
                "reason": "identical prior run without valid reusable artifact"}
    if request.get("prerequisites_verified") is not True:
        return {"decision": "BLOCKED", "fingerprint": key,
                "reason": "prerequisites not independently verified"}
    return {"decision": "RUN_ELIGIBLE", "fingerprint": key,
            "reason": "independent, nonduplicate work; no run dispatched"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    if not isinstance(ledger, list):
        raise ValueError("ledger must be an array")
    print(json.dumps(classify(request, ledger), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
