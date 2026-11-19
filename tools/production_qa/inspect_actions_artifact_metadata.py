#!/usr/bin/env python3
"""Read-only inspection of Actions Artifact metadata for an explicit run ID.

Metadata is not evidence that downloaded bytes match an output manifest.
No dispatch, cancellation, mutations, or implicit latest-success selection.
"""
import argparse
import json
import os
import re
from urllib.request import Request, urlopen

REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def get_json(url, token):
    request = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "TWO-read-only-artifact-inspector",
    })
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def inspect(repo, run_id, artifact_name, token, get=get_json):
    if not isinstance(repo, str) or REPO.fullmatch(repo) is None:
        raise ValueError("invalid repository")
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("explicit positive run ID required")
    if not isinstance(artifact_name, str) or not artifact_name.strip():
        raise ValueError("explicit artifact name required")
    if not isinstance(token, str) or not token:
        raise ValueError("authentication token required")
    base = "https://api.github.com/repos/" + repo
    run = get(base + "/actions/runs/" + str(run_id), token)
    if run.get("id") != run_id or run.get("repository", {}).get("full_name") != repo:
        raise ValueError("run identity/repository mismatch")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError("run is not completed successfully")
    found = []
    page = 1
    while page <= 5:
        payload = get(base + "/actions/runs/" + str(run_id) +
                      "/artifacts?per_page=100&page=" + str(page), token)
        batch = payload.get("artifacts")
        if not isinstance(batch, list):
            raise ValueError("invalid artifact API response")
        found.extend(a for a in batch if a.get("name") == artifact_name)
        total = payload.get("total_count")
        if type(total) is not int or total < 0:
            raise ValueError("missing artifact total_count")
        if page * 100 >= total:
            break
        page += 1
    else:
        raise ValueError("artifact listing exceeded 5-page inspection bound")
    if len(found) != 1:
        raise ValueError("expected exactly one matching artifact on specified run")
    artifact = found[0]
    if artifact.get("expired") is not False or type(artifact.get("size_in_bytes")) is not int or artifact["size_in_bytes"] <= 0:
        raise ValueError("artifact expired or empty")
    if artifact.get("workflow_run", {}).get("id") != run_id:
        raise ValueError("artifact workflow run ID mismatch")
    return {
        "read_only": True,
        "repository": repo,
        "run_id": run_id,
        "head_sha": run.get("head_sha"),
        "head_branch": run.get("head_branch"),
        "artifact_id": artifact.get("id"),
        "artifact_name": artifact_name,
        "size_in_bytes": artifact["size_in_bytes"],
        "expired": False,
        "metadata_accessible": True,
        "artifact_bytes_verified": False,
        "output_contract_verified": False,
        "safe_to_reuse": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--artifact-name", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.repo, args.run_id, args.artifact_name,
                             os.environ.get("GH_TOKEN", "")), sort_keys=True))


if __name__ == "__main__":
    main()
