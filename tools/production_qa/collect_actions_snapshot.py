#!/usr/bin/env python3
"""Read-only GitHub Actions run snapshot; never dispatches, cancels or writes to GitHub.

Uses GitHub REST with a read-only token. Outputs JSON to stdout. This is an
observation snapshot, NOT an authoritative shared job ledger or mutex.
"""
import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def get_json(url, token):
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": "Bearer " + token,
        "User-Agent": "two-readonly-actions-audit",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def collect(repo, token, pages=2, get=get_json):
    if not REPO_PATTERN.fullmatch(repo):
        raise ValueError("invalid owner/repository")
    if not token:
        raise ValueError("GH_TOKEN is required; do not use unauthenticated polling")
    if not 1 <= pages <= 5:
        raise ValueError("pages must be between 1 and 5")
    result = []
    seen = set()
    for page in range(1, pages + 1):
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        url = "https://api.github.com/repos/" + repo + "/actions/runs?" + query
        payload = get(url, token)
        runs = payload.get("workflow_runs")
        if not isinstance(runs, list):
            raise ValueError("invalid GitHub workflow runs response")
        for run in runs:
            run_id = run.get("id")
            if not isinstance(run_id, int) or run_id in seen:
                continue
            seen.add(run_id)
            result.append({
                "run_id": run_id, "name": run.get("name"),
                "workflow_id": run.get("workflow_id"),
                "head_branch": run.get("head_branch"),
                "head_sha": run.get("head_sha"),
                "event": run.get("event"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "created_at": run.get("created_at"),
                "updated_at": run.get("updated_at"),
                "html_url": run.get("html_url"),
            })
        if len(runs) < 100:
            break
    return {"repository": repo, "read_only": True, "runs": result,
            "incomplete_if_more_than_pages": True,
            "note": "Run snapshot is not an atomic deduplication lock or verified artifact cache"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pages", type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(collect(args.repo, os.environ.get("GH_TOKEN", ""), args.pages),
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
