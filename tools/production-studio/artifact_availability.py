"""Conservative handling of expired, already-published pinned artifact receipts."""
from datetime import datetime, timezone
import re

def recorded_expired_404(item, stderr, now):
    """404 alone is insufficient: require exact recorded expiry and entry pins."""
    if not re.fullmatch(r"gh: Not Found \(HTTP 404\)\s*", stderr):
        return False
    try:
        expiry = datetime.fromisoformat(item["expires_at"].replace("Z", "+00:00"))
        entries = item["entries"]
        pins = item["entry_sha256"]
        return (
            now.tzinfo is not None and expiry.tzinfo is not None and expiry <= now
            and type(entries) is list and bool(entries) and len(entries) == len(set(entries))
            and type(pins) is dict and set(entries) == set(pins)
            and all(isinstance(v, str) and re.fullmatch(r"[a-f0-9]{64}", v) for v in pins.values())
            and bool(re.fullmatch(r"sha256:[a-f0-9]{64}", item["artifact_digest"]))
        )
    except (KeyError, TypeError, ValueError, AttributeError):
        return False

def retained_receipt_matches(item, history):
    """Only already-published exact entries may be skipped; later merge rehashes bytes."""
    if history.get("version") != 1 or not isinstance(history.get("entries"), list):
        return False
    for name, sha in item["entry_sha256"].items():
        matches = [e for e in history["entries"] if isinstance(e, dict)
                   and e.get("sha256") == sha and e.get("name") == name
                   and all(e.get(k) == item[k] for k in ("run_id", "artifact_id", "head"))]
        if len(matches) != 1:
            return False
    return True
