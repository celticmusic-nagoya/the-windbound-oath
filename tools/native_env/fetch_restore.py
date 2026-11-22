#!/usr/bin/env python3
"""Cross-run restore input: resolve the requested prior run's artifact via the API (id, digest, expiry,
producing head SHA), download with the shared hash-verifying downloader, then extract with path checks
and verify the embedded SHA256SUMS. Usage: fetch_restore.py REQUEST.json OUTDIR"""
import hashlib
import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "production_qa"))
from download_actions_artifact import download  # noqa: E402

req = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2]).resolve()
repo, token = os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"]
api = "https://api.github.com/repos/%s/actions/runs/%d/artifacts?per_page=100" % (repo, int(req["source_run_id"]))
r = urllib.request.urlopen(urllib.request.Request(api, headers={"Authorization": "Bearer " + token,
                                                              "Accept": "application/vnd.github+json"}), timeout=30)
arts = [a for a in json.loads(r.read())["artifacts"] if a["name"] == req["artifact_name"]]
if len(arts) != 1 or arts[0]["expired"]:
    raise SystemExit("RESTORE_ARTIFACT_MISSING_OR_EXPIRED")
a = arts[0]
digest = (a.get("digest") or "").removeprefix("sha256:")
if a["workflow_run"]["head_sha"] != req["source_head_sha"]:
    raise SystemExit("RESTORE_SOURCE_HEAD_MISMATCH")
out.mkdir(parents=True, exist_ok=False)
zpath = out.parent / (out.name + ".zip")
info = download(repo, a["id"], token, zpath, digest)
with zipfile.ZipFile(zpath) as z:
    for m in z.infolist():
        p = (out / m.filename).resolve()
        if not p.is_relative_to(out):
            raise SystemExit("UNSAFE_ZIP_ENTRY")
    z.extractall(out)
sums = out / "ckpt" / "SHA256SUMS"
bad = []
for line in sums.read_text().splitlines():
    h, rel = line.split("  ", 1)
    p = (out / "ckpt" / rel).resolve()
    if not p.is_relative_to(out) or hashlib.sha256(p.read_bytes()).hexdigest() != h:
        bad.append(rel)
if bad:
    raise SystemExit("RESTORE_SHA_MISMATCH:%s" % bad)
rec = {"source_run_id": int(req["source_run_id"]), "artifact_id": a["id"], "artifact_name": a["name"],
       "zip_sha256": digest, "expires_at": a["expires_at"], "source_head_sha": a["workflow_run"]["head_sha"],
       "download": info, "files_verified": len(sums.read_text().splitlines())}
(out.parent / "restore_provenance.json").write_text(json.dumps(rec, indent=1))
print("TWO_RESTORE_OK", json.dumps(rec))
