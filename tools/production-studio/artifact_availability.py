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


def reusable_published_images(item, history, approvals):
    """Require all exact image pins, approved provenance and unchanged display metadata.

    This is a download decision only. The downstream merge must still rehash
    every retained file and the publication gate must preserve all old records.
    """
    try:
        entries, pins = item["entries"], item["entry_sha256"]
        if (type(entries) is not list or not entries or len(entries) != len(set(entries))
            or type(pins) is not dict or set(entries) != set(pins)
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", item["artifact_digest"])
            or not re.fullmatch(r"[a-f0-9]{40}", item["head"])
            or any(type(item[k]) is not int or item[k] <= 0 for k in ("run_id", "artifact_id"))
            or item["cover"] not in entries or item["stage"].endswith("/ preview only")
            or not isinstance(item["review_ref"], str) or not item["review_ref"].strip()
            or history.get("version") != 1 or approvals.get("version") != 1):
            return False
        if not retained_receipt_matches(item, history):
            return False
        for name, sha in pins.items():
            if (not isinstance(name, str) or not re.fullmatch(r"(?:[A-Za-z0-9][A-Za-z0-9_.-]*/)*[A-Za-z0-9][A-Za-z0-9_.-]*\.(?:png|jpg|jpeg)", name, re.I)
                or not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{64}", sha)):
                return False
            path = "published/" + sha + "." + name.rsplit(".", 1)[1].lower()
            rows = [e for e in history["entries"] if e.get("sha256") == sha]
            receipts = [e for e in approvals["entries"] if e.get("sha256") == sha]
            if len(rows) != 1 or len(receipts) != 1:
                return False
            row, receipt = rows[0], receipts[0]
            if (row.get("path") != path or row.get("entry_pin_verified") is not True
                or row.get("category") != item["category"] or row.get("stage") != item["stage"]
                or row.get("cover") != (name == item["cover"])
                or row.get("subcategory") != item.get("entry_subcategories", {}).get(name)
                or row.get("review_ref") != item["review_ref"]
                or receipt.get("approval_ref") != item["review_ref"]
                or any(row.get(k) != receipt.get(k) for k in ("head", "name", "path", "run_id", "artifact_id", "source_path"))):
                return False
        return True
    except (KeyError, TypeError, ValueError, AttributeError):
        return False

# One reviewed, immutable archive is larger than the ordinary 128 MiB budget.
# Do not generalize this exception to native files or unreviewed artifacts.
_V82E = (15177030518, 45950645582, "79fe5d7662c6359b60fcfab8004c44da41a9d282",
         "sha256:d1a36847e95f2ea29306b0227213a48ffcc401b9963ccd127929109d3ca80f67", 139463532)
_V82E_PINS = {
    "v82e_atlas_altar_front.png": "5f953d4580c7fcd1c8213d18f53ce62cd9d62387bf9a1f2c241ac98c54ec27d6",
    "v82e_atlas_altar_oblique.png": "33ec83afd85e104e0de1cbe9170a7b6ce3d8dc8a9ba5dd1e6344bb6358d21013",
    "v82e_clay_altar_front.png": "31ae65a3a5f7e7ecfd714448bd94cc0270c7dc361f94a79016456ff0a9219b74",
    "v82e_clay_altar_oblique.png": "39bfed45bfbee7afcc94a98160cdf25caa435436268ca498e39cd71f24a503e2",
    "v82e_tileable_altar_front.png": "02b411723b85013b65b4f39485d0f832e63fdc5acffb56cbb974a557ca863a8f",
    "v82e_tileable_altar_oblique.png": "9e5e2ab74f4139541380882832182ace9f71c5cc49f2ed697f7a9f8870919198"
}
def archive_budget(item):
    if "exact_archive_bytes" not in item:
        return 128*1024*1024
    actual = (item.get("artifact_id"), item.get("run_id"), item.get("head"),
              item.get("artifact_digest"), item.get("exact_archive_bytes"))
    if (actual != _V82E or item.get("entry_sha256") != _V82E_PINS
        or not isinstance(item.get("entries"), list)
        or len(item["entries"]) != len(_V82E_PINS)
        or set(item["entries"]) != set(_V82E_PINS)
        or item.get("reuse_retained") is not True):
        raise ValueError("unqualified large archive exception")
    return _V82E[-1]
