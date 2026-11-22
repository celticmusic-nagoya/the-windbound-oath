#!/usr/bin/env python3
"""Cross-run restore of a session tarball: API lookup (id, digest, expiry, producing head), shared hash-verifying
download, then the tarball's own SHA-256 check. Usage: fetch_restore_tar.py REQUEST.json OUTDIR -> OUTDIR/session.tgz"""
import hashlib, json, os, sys, urllib.request, zipfile
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
if len(arts) != 1 or arts[0]["expired"] or arts[0]["workflow_run"]["head_sha"] != req["source_head_sha"]:
    raise SystemExit("RESTORE_ARTIFACT_MISSING_EXPIRED_OR_WRONG_HEAD")
a = arts[0]
out.mkdir(parents=True)
z = out / "artifact.zip"
info = download(repo, a["id"], token, z, (a.get("digest") or "").removeprefix("sha256:"))
with zipfile.ZipFile(z) as f:
    data = f.read("session.tgz")
    want = f.read("session.tgz.sha256").decode().split()[0]
if hashlib.sha256(data).hexdigest() != want:
    raise SystemExit("SESSION_TARBALL_SHA_MISMATCH")
(out / "session.tgz").write_bytes(data)
rec = {"source_run_id": int(req["source_run_id"]), "artifact_id": a["id"], "zip_digest": a.get("digest"),
       "expires_at": a["expires_at"], "source_head_sha": req["source_head_sha"], "session_tgz_sha256": want, "download": info}
(out / "restore_provenance.json").write_text(json.dumps(rec, indent=1))
print("TWO_RESTORE_OK", json.dumps(rec))
