#!/usr/bin/env python3
"""Prototype durable, create-only Git ref reservation for identical job fingerprints.

Not a dispatch controller. This does not authorize ref creation on the real repo.
GitHub's create-ref uniqueness is the atomic primitive; no check-then-create.
Reservations persist and must not be deleted automatically. The referenced
commit SHA is only an anchor, NOT a job state or verified artifact manifest.
"""
import re
from classify_actions_jobs import classify, fingerprint

HEX = re.compile(r"[0-9a-f]{40}\Z")
KEY = re.compile(r"[0-9a-f]{64}\Z")
PREFIX = "refs/tags/two-job-reservation/v1/"


def reserve(request, ledger, anchor_sha, create_ref):
    """create_ref(ref, sha) must perform one atomic create-only GitHub API POST.

    Returns a result status or raises an exception with .status or .status_code.
    Never call a read/exists endpoint to decide whether to create a ref.
    """
    decision = classify(request, ledger)
    key = fingerprint(request)
    if decision["decision"] != "RUN_ELIGIBLE":
        return {"decision": decision["decision"], "fingerprint": key,
                "reservation_created": False}
    if not isinstance(anchor_sha, str) or HEX.fullmatch(anchor_sha) is None:
        raise ValueError("full immutable commit SHA required")
    if not callable(create_ref):
        raise TypeError("create_ref callback required")
    ref = PREFIX + key
    try:
        create_ref(ref, anchor_sha)
    except Exception as error:
        status = getattr(error, "status", getattr(error, "status_code", None))
        if status in (409, 422):
            # A conflict may mean an existing reservation or a validation error.
            # Fail closed: do not dispatch, do not assume an existing owner.
            return {"decision": "REVIEW_REQUIRED", "fingerprint": key,
                    "reservation_created": False,
                    "reason": "GitHub create-ref conflict/validation; inspect exact ref"}
        raise
    return {"decision": "RESERVED_ONLY", "fingerprint": key,
            "reservation_created": True, "ref": ref,
            "dispatch_authorized": False}


def inspect_existing_ref(expected_fingerprint, ref, sha):
    """Validate an observed ref identity only; no ownership or run authorization."""
    if not isinstance(expected_fingerprint, str) or KEY.fullmatch(expected_fingerprint) is None:
        raise ValueError("invalid fingerprint")
    if ref != PREFIX + expected_fingerprint or not isinstance(sha, str) or HEX.fullmatch(sha) is None:
        raise ValueError("ref identity or SHA mismatch")
    return {"fingerprint": expected_fingerprint, "ref_exists": True,
            "anchor_sha": sha, "dispatch_authorized": False,
            "artifact_verified": False}


if __name__ == "__main__":
    raise SystemExit("Prototype library only; no CLI, API writes or dispatch")
