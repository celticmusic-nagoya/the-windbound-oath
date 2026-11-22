"""Match coordinator-authenticated independent review evidence to native bytes."""
from datetime import datetime
from shared_blueprint_contract import matches_digest


def review_passes(review, native_sha256, *, now):
    """The coordinator supplies authenticated records and a timezone-aware clock."""
    if (not isinstance(review, dict) or review.get("authenticated") is not True
            or review.get("independent") is not True or review.get("status") != "PASS"
            or not matches_digest(native_sha256) or review.get("native_sha256") != native_sha256):
        return False
    try:
        expires = datetime.fromisoformat(review["expires_at"])
        return now.utcoffset() is not None and expires.utcoffset() is not None and now < expires
    except (KeyError, TypeError, ValueError):
        return False
