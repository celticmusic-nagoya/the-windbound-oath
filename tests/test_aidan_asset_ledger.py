"""Offline tests for tools/map_production/aidan_asset_ledger.py (MAP-ASSET-PREP-01)."""
import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("aidan_asset_ledger", ROOT / "tools/map_production/aidan_asset_ledger.py")
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)


@pytest.fixture()
def ledger():
    return L.load()


def test_committed_ledger_passes(ledger):
    assert L.validate(ledger) == []


def test_canonical_reference_hash_is_enforced(ledger):
    bad = copy.deepcopy(ledger)
    bad["canonical_reference"]["sha256"] = "0" * 64
    assert any("SHA-256 mismatch" in e for e in L.validate(bad))


def test_unknown_license_cannot_be_candidate(ledger):
    bad = copy.deepcopy(ledger)
    bad["assets"][0]["license"] = "unknown"
    assert any("non-open/unknown license" in e for e in L.validate(bad))


def test_thatch_cannot_be_promoted_under_slate_canon(ledger):
    bad = copy.deepcopy(ledger)
    thatch = next(a for a in bad["assets"] if "thatch" in a["role"])
    thatch["status"] = "CANDIDATE"
    assert any("thatch role" in e for e in L.validate(bad))


def test_restricted_redistribution_cannot_be_candidate(ledger):
    bad = copy.deepcopy(ledger)
    q = next(a for a in bad["assets"] if a["provider"] == "Quaternius")
    q["status"] = "CANDIDATE"
    errs = L.validate(bad)
    assert any("non-redistributable" in e for e in errs)


def test_attribution_assets_need_explicit_status(ledger):
    bad = copy.deepcopy(ledger)
    by = next(a for a in bad["assets"] if a["status"] == "CANDIDATE_ATTRIBUTION_REQUIRED")
    by["status"] = "CANDIDATE"
    assert any("attribution required" in e for e in L.validate(bad))


def test_fetch_refuses_repository_output(ledger):
    with pytest.raises(SystemExit):
        L.fetch(ledger, ROOT / "assets" / "tmp-should-not-exist", priority=1)
    assert not (ROOT / "assets" / "tmp-should-not-exist").exists()


def test_hash_helpers(tmp_path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"windbound")
    import hashlib
    assert L.sha256_file(p) == hashlib.sha256(b"windbound").hexdigest()
    assert L.md5_file(p) == hashlib.md5(b"windbound").hexdigest()


def test_compare_locks_detects_drift():
    exp = {"files": [{"url": "u1", "sha256": "a"}, {"url": "u2", "sha256": "b"}]}
    assert L.compare_locks(exp, exp) == []
    drift = {"files": [{"url": "u1", "sha256": "x"}]}
    errs = L.compare_locks(exp, drift)
    assert any("changed: u1" in e for e in errs) and any("missing from new fetch: u2" in e for e in errs)


def test_locked_set_matches_committed_lock(ledger):
    import json
    lock = json.loads((ROOT / "docs/map-production/aidan_asset_sha256.lock.json").read_text())
    assert {f["asset"] for f in lock["files"]} == L.locked_set_ids(ledger)
    assert lock["errors"] == []
    assert all(f.get("md5_ok", True) for f in lock["files"])
