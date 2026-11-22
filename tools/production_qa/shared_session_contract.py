"""Shared production identity and deterministic stage fingerprint contract."""
import hashlib
import json
import re

ASSET_KEYS = frozenset({"MORWEN", "LIND-CLIFF", "LIND-HOME", "LIND-BUILD", "LIND-WORLD"})
FIELDS = frozenset({"blueprint", "inputs", "code", "environment", "dependencies", "qa"})

def asset_key(value):
    if value not in ASSET_KEYS:
        raise ValueError("unregistered shared asset key")
    return value

def fingerprint(asset, stage, hashes):
    asset_key(asset)
    if not isinstance(stage, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", stage):
        raise ValueError("invalid stage ID")
    if set(hashes) != FIELDS:
        raise ValueError("incomplete fingerprint components")
    for field, entries in hashes.items():
        if not isinstance(entries, dict) or (not entries and field != "dependencies"):
            raise ValueError("missing component: " + field)
        for name, digest in entries.items():
            if not isinstance(name, str) or not name or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("invalid component digest")
    payload = dict(version=1, asset=asset, stage=stage, hashes=hashes)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
