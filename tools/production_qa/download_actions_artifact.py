#!/usr/bin/env python3
"""Download an explicitly identified GitHub Actions artifact ZIP without extraction.

This tool does not trust ZIP contents or set safe_to_reuse. It never dispatches
jobs, modifies GitHub, or follows arbitrary cross-origin redirects.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download(repo, artifact_id, token, output, expected_zip_sha256,
             max_bytes=500 * 1024 * 1024, opener=None):
    if not isinstance(repo, str) or not REPO.fullmatch(repo):
        raise ValueError("invalid repository")
    if type(artifact_id) is not int or artifact_id <= 0:
        raise ValueError("explicit artifact ID required")
    if not token:
        raise ValueError("authentication required")
    if not isinstance(expected_zip_sha256, str) or not SHA.fullmatch(expected_zip_sha256):
        raise ValueError("expected ZIP SHA-256 required from trusted manifest")
    if type(max_bytes) is not int or not 0 < max_bytes <= 1024**3:
        raise ValueError("invalid download limit")
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("refusing to overwrite output")
    if not output.parent.is_dir():
        raise ValueError("output parent must exist")
    opener = opener or build_opener(NoRedirect())
    api = "https://api.github.com/repos/" + repo + "/actions/artifacts/" + str(artifact_id) + "/zip"
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "TWO-artifact-read-only"}
    try:
        redirect = opener.open(Request(api, headers=headers), timeout=30)
        try:
            if redirect.status not in (301, 302, 303, 307, 308):
                raise ValueError("expected GitHub archive redirect")
            target = redirect.headers.get("Location")
        finally:
            redirect.close()
        parsed = urlparse(target or "")
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError("invalid archive redirect")
        if parsed.hostname not in ("productionresultssa0.blob.core.windows.net",
                                   "pipelines.actions.githubusercontent.com") and not (
                parsed.hostname and parsed.hostname.endswith(".blob.core.windows.net")):
            raise ValueError("untrusted archive host")
        # Do not forward the GitHub bearer token to storage.
        response = opener.open(Request(target, headers={"User-Agent": "TWO-artifact-read-only"}), timeout=60)
        digest = hashlib.sha256()
        count = 0
        try:
            if response.status != 200:
                raise ValueError("archive download failed")
            with output.open("xb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > max_bytes:
                        raise ValueError("archive exceeds size limit")
                    digest.update(chunk)
                    handle.write(chunk)
        finally:
            response.close()
        if count == 0 or digest.hexdigest() != expected_zip_sha256:
            raise ValueError("archive ZIP SHA-256 mismatch or empty")
        return {"zip_sha256_verified": True, "artifact_id": artifact_id,
                "bytes": count, "path": str(output),
                "zip_extracted": False, "safe_to_reuse": False}
    except BaseException:
        output.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-zip-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(download(args.repo, args.artifact_id,
                              os.environ.get("GH_TOKEN", ""), args.output,
                              args.expected_zip_sha256), sort_keys=True))


if __name__ == "__main__":
    main()
