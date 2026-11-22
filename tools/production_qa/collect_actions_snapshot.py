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
PAGE_SIZE = 100
RUN_FIELDS = (
    "name", "workflow_id", "head_branch", "head_sha", "path", "event",
    "status", "conclusion", "created_at", "updated_at", "html_url", "run_attempt",
)


def get_json(url, token):
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": "Bearer " + token,
        "User-Agent": "two-readonly-actions-audit",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def collect(repo, token, pages=2, get=get_json, *, complete=False):
    if not isinstance(repo, str) or not REPO_PATTERN.fullmatch(repo) or any(
        part in (".", "..") for part in repo.split("/")
    ):
        raise ValueError("invalid owner/repository")
    if not token:
        raise ValueError("GH_TOKEN is required; do not use unauthenticated polling")
    if complete:
        return collect_complete(repo, token, get)
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


def collect_complete(repo, token, get):
    """Require two matching unfiltered traversals before returning observations."""
    def traverse():
        runs = []
        seen = set()
        page = 1
        total = None
        while True:
            query = urllib.parse.urlencode({"per_page": PAGE_SIZE, "page": page})
            payload = get(f"https://api.github.com/repos/{repo}/actions/runs?{query}", token)
            if not isinstance(payload, dict):
                raise ValueError("invalid Actions response")
            count = payload.get("total_count")
            batch = payload.get("workflow_runs")
            if type(count) is not int or count < 0 or not isinstance(batch, list):
                raise ValueError("invalid Actions count or run list")
            if total is None:
                total = count
            expected = min(PAGE_SIZE, total - len(runs))
            if count != total or len(batch) != expected:
                raise ValueError(f"Actions pagination changed or is incomplete at page {page}")
            if not batch:
                return runs
            for run in batch:
                if not isinstance(run, dict):
                    raise ValueError("invalid Actions run")
                run_id = run.get("id")
                if type(run_id) is not int or run_id <= 0 or run_id in seen:
                    raise ValueError("invalid or duplicate Actions run ID")
                if any(not isinstance(run.get(field), str) or not run[field]
                       for field in ("event", "status", "head_sha", "path")):
                    raise ValueError("missing Actions run identity or status")
                if run["status"] == "completed" and not run.get("conclusion"):
                    raise ValueError("completed Actions run is missing its conclusion")
                seen.add(run_id)
                runs.append({"run_id": run_id, **{key: run.get(key) for key in RUN_FIELDS}})
            page += 1

    first = traverse()
    second = traverse()
    if first != second:
        raise ValueError("Actions observations changed between traversals")
    return {"repository": repo, "read_only": True, "complete": True,
            "scope": "repository_all_events", "runs": second,
            "note": "Matching observations do not reserve a writer or verify an artifact"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--pages", type=int, help="legacy bounded audit (1–5 pages)")
    scope.add_argument("--complete", action="store_true", help="complete all-event scan (default)")
    args = parser.parse_args()
    try:
        pages = 2 if args.pages is None else args.pages
        snapshot = collect(args.repo, os.environ.get("GH_TOKEN", ""), pages,
                           complete=args.complete or args.pages is None)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"BLOCKED_ACTIONS_SNAPSHOT: {exc}\n")
    print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
