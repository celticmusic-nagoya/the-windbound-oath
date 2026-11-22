#!/usr/bin/env python3
"""Fetch the requested owner artifact (digest-verified) and make a disposable copy of its native file.
Usage: fetch_real_asset.py REQUEST.json OUTDIR  -> OUTDIR/copy/<native>.COPY.blend"""
import hashlib, json, os, sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "production_qa"))
from download_actions_artifact import download  # noqa: E402
r = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True)
z = out / "source.zip"
download(os.environ["GITHUB_REPOSITORY"], int(r["artifact_id"]), os.environ["GH_TOKEN"], z, r["zip_sha256"])
with zipfile.ZipFile(z) as f:
    data = f.read(r["native"])
if hashlib.sha256(data).hexdigest() != r["native_sha256"]:
    raise SystemExit("NATIVE_SHA_MISMATCH")
(out / "copy").mkdir()
dst = out / "copy" / (Path(r["native"]).stem + ".COPY.blend")
dst.write_bytes(data)
print("TWO_REAL_ASSET_COPY", dst, r["native_sha256"])
