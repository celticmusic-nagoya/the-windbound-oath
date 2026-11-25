"""MAP-ASSET-PREP-01: Aidan home asset ledger tool (non-destructive).

Subcommands
  validate      Offline schema/license/canon checks. Exit 1 on any error.
  check-online  Re-query Poly Haven / ambientCG APIs; compare authors and file md5.
  fetch         Download planned maps for selected entries into --out (never into
                the repository), verify provider md5, write SHA-256 lock JSON.

Examples
  python3 tools/map_production/aidan_asset_ledger.py validate
  python3 tools/map_production/aidan_asset_ledger.py check-online --report /tmp/online.json
  python3 tools/map_production/aidan_asset_ledger.py fetch --locked-set \
      --out /tmp/aidan-assets --lock /tmp/aidan-assets/sha256.lock.json \
      --expect-lock docs/map-production/aidan_asset_sha256.lock.json

Nothing here approves an asset. CANDIDATE != adopted.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs/map-production/aidan_asset_ledger.json"
UA = {"User-Agent": "windbound-asset-ledger/1.0"}
STATUSES = {"CANDIDATE", "CANDIDATE_ATTRIBUTION_REQUIRED", "REFERENCE_ONLY",
            "REJECTED_FOR_AIDAN_HOME", "BLOCKED_LICENSE_RESTRICTED"}
REQUIRED = ["id", "role", "priority", "status", "provider", "kind", "asset_id", "url",
            "authors", "license", "license_evidence_url", "commercial_use",
            "modification", "redistribution", "attribution_required", "format",
            "fit_score", "fit_note"]
OPEN_LICENSES = {"CC0-1.0", "CC-BY-4.0"}
FORBIDDEN_ROOF_ROLES = ("thatch",)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path=LEDGER):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(ledger, repo_root=ROOT, check_reference_file=True):
    """Return list of error strings (empty == PASS)."""
    errors = []
    ref = ledger.get("canonical_reference", {})
    if check_reference_file:
        p = Path(repo_root) / ref.get("path", "")
        if not p.is_file():
            errors.append("canonical reference missing: %s" % ref.get("path"))
        elif sha256_file(p) != ref.get("sha256"):
            errors.append("canonical reference SHA-256 mismatch: %s" % ref.get("path"))
    forbidden = [x.lower() for x in ledger.get("roof_canon", {}).get("forbidden", [])]
    if "thatch" not in forbidden:
        errors.append("roof_canon.forbidden must list thatch (2026-11-14 slate canon)")
    seen = set()
    for a in ledger.get("assets", []):
        aid = a.get("id", "<no id>")
        for k in REQUIRED:
            if k not in a:
                errors.append("%s: missing field %s" % (aid, k))
        if aid in seen:
            errors.append("%s: duplicate id" % aid)
        seen.add(aid)
        st = a.get("status")
        if st not in STATUSES:
            errors.append("%s: unknown status %s" % (aid, st))
        lic = a.get("license", "")
        if st in ("CANDIDATE", "CANDIDATE_ATTRIBUTION_REQUIRED"):
            if lic not in OPEN_LICENSES:
                errors.append("%s: candidate with non-open/unknown license %r" % (aid, lic))
            if not a.get("license_evidence_url"):
                errors.append("%s: candidate without license evidence" % aid)
            if a.get("attribution_required") and st != "CANDIDATE_ATTRIBUTION_REQUIRED":
                errors.append("%s: attribution required but status lacks ATTRIBUTION flag" % aid)
            if any(r in a.get("role", "") for r in FORBIDDEN_ROOF_ROLES):
                errors.append("%s: thatch role cannot be a candidate under slate canon" % aid)
        if lic == "CC0-1.0" and not (a.get("commercial_use") and a.get("modification")
                                     and a.get("redistribution")) :
            errors.append("%s: CC0 flags inconsistent" % aid)
        if a.get("redistribution") is False and st == "CANDIDATE":
            errors.append("%s: non-redistributable asset cannot be CANDIDATE" % aid)
        fs = a.get("fit_score")
        if not isinstance(fs, int) or not 1 <= fs <= 5:
            errors.append("%s: fit_score must be int 1..5" % aid)
    return errors


def http_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(tmp, dest)


def check_online(ledger):
    results = []
    for a in ledger["assets"]:
        row = {"id": a["id"], "provider": a["provider"]}
        try:
            if a["provider"] == "Poly Haven":
                info = http_json("https://api.polyhaven.com/info/" + a["asset_id"])
                row["found"] = True
                row["authors_match"] = sorted(info["authors"]) == sorted(a["authors"])
                files = http_json("https://api.polyhaven.com/files/" + a["asset_id"])
                mism = []
                for k, m in (a.get("planned_maps_2k") or {}).items():
                    cur = files.get(k, {}).get("2k", {})
                    cur = cur.get("jpg") or cur.get("png") or {}
                    if cur.get("md5") != m["md5"]:
                        mism.append(k)
                row["md5_changed"] = mism
                row["status"] = "PASS" if row["authors_match"] and not mism else "CHANGED"
            elif a["provider"] == "ambientCG":
                d = http_json("https://ambientcg.com/api/v2/full_json?id=%s&include=downloadData" % a["asset_id"])
                row["found"] = d.get("numberOfResults", 0) == 1
                row["status"] = "PASS" if row["found"] else "NOT_FOUND"
            else:
                row["status"] = "MANUAL"  # Sketchfab/Kenney/Quaternius: manual or archive SHA
        except Exception as exc:  # report, do not hide
            row["status"] = "ERROR"
            row["error"] = "%s: %s" % (type(exc).__name__, exc)
        results.append(row)
    return results


def fetch(ledger, out, ids=None, priority=None):
    out = Path(out).resolve()
    if ROOT in out.parents or out == ROOT:
        raise SystemExit("refusing to download into the repository: %s" % out)
    lock = {"task": ledger["task"], "files": [], "errors": []}
    for a in ledger["assets"]:
        if ids and a["id"] not in ids:
            continue
        if priority is not None and a["priority"] != priority:
            continue
        if a["status"] not in ("CANDIDATE",):
            continue
        targets = []
        for k, m in (a.get("planned_maps_2k") or {}).items():
            targets.append((k, m["url"], m.get("md5")))
        if a.get("planned_gltf_1k"):
            g = a["planned_gltf_1k"]
            targets.append(("gltf", g["url"], g.get("md5")))
            for inc, m in (g.get("include") or {}).items():
                targets.append(("gltf_include:" + inc, m["url"], m.get("md5")))
        if a.get("planned_zip_2k"):
            z = a["planned_zip_2k"]
            targets.append(("zip", z["url"], z.get("md5")))
        for kind, url, md5 in targets:
            name = url.split("file=")[-1] if "file=" in url else url.rsplit("/", 1)[-1]
            if kind.startswith("gltf_include:"):
                name = kind.split(":", 1)[1]  # keep relative layout expected by .gltf
            if ".." in Path(name).parts or Path(name).is_absolute():
                lock["errors"].append("%s unsafe path %s" % (a["id"], name))
                continue
            dest = out / a["id"] / name
            try:
                download(url, dest)
                rec = {"asset": a["id"], "map": kind, "url": url, "path": str(dest.relative_to(out)),
                       "bytes": dest.stat().st_size, "sha256": sha256_file(dest)}
                if md5:
                    got = md5_file(dest)
                    rec["provider_md5"] = md5
                    rec["md5_ok"] = got == md5
                    if not rec["md5_ok"]:
                        lock["errors"].append("%s %s md5 mismatch" % (a["id"], kind))
                lock["files"].append(rec)
            except Exception as exc:
                lock["errors"].append("%s %s %s: %s" % (a["id"], kind, type(exc).__name__, exc))
    return lock


def locked_set_ids(ledger):
    return {x["id"] for x in ledger["assets"] if x["status"] == "CANDIDATE"
            and x["priority"] <= 2 and x["provider"] in ("Poly Haven", "ambientCG")}


def compare_locks(expected, actual):
    """Return reproducibility errors: same URL must give the same SHA-256."""
    exp = {f["url"]: f["sha256"] for f in expected.get("files", [])}
    act = {f["url"]: f["sha256"] for f in actual.get("files", [])}
    errs = ["sha256 changed: %s" % u for u in exp if u in act and act[u] != exp[u]]
    errs += ["missing from new fetch: %s" % u for u in exp if u not in act]
    return errs


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--ledger", default=str(LEDGER))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    c = sub.add_parser("check-online")
    c.add_argument("--report")
    f = sub.add_parser("fetch")
    f.add_argument("--out", required=True)
    f.add_argument("--lock", required=True)
    f.add_argument("--ids", nargs="*")
    f.add_argument("--priority", type=int)
    f.add_argument("--locked-set", action="store_true",
                   help="CANDIDATE, priority<=2, Poly Haven/ambientCG (the set in the committed lock)")
    f.add_argument("--expect-lock", help="committed lock; fail if any URL's SHA-256 differs")
    a = p.parse_args(argv)
    ledger = load(a.ledger)
    if a.cmd == "validate":
        errs = validate(ledger)
        for e in errs:
            print("ERROR:", e)
        print("LEDGER_VALIDATE:", "PASS" if not errs else "FAIL", "(%d assets)" % len(ledger["assets"]))
        return 1 if errs else 0
    if a.cmd == "check-online":
        res = check_online(ledger)
        bad = [r for r in res if r["status"] in ("CHANGED", "NOT_FOUND", "ERROR")]
        if a.report:
            Path(a.report).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
        for r in res:
            print(r["status"], r["id"], r.get("error", ""))
        print("ONLINE_CHECK:", "PASS" if not bad else "ATTENTION (%d)" % len(bad))
        return 1 if bad else 0
    if a.cmd == "fetch":
        ids = set(a.ids) if a.ids else None
        if a.locked_set:
            ids = locked_set_ids(ledger)
        lock = fetch(ledger, a.out, ids, a.priority)
        if a.expect_lock:
            lock["errors"] += compare_locks(json.loads(Path(a.expect_lock).read_text()), lock)
        Path(a.lock).parent.mkdir(parents=True, exist_ok=True)
        Path(a.lock).write_text(json.dumps(lock, indent=1, ensure_ascii=False) + "\n")
        print("FETCH: %d files, %d errors" % (len(lock["files"]), len(lock["errors"])))
        return 1 if lock["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
