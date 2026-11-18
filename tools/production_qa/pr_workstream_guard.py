#!/usr/bin/env python3
"""Read-only PR inventory and duplicate-workstream gate for TWO.

Uses GitHub REST GET and GITHUB_TOKEN. No branch, PR or issue mutation.
Example: python3 tools/production_qa/pr_workstream_guard.py --repo owner/repo --output report.json
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

WORKSTREAMS = {
    "morwen": re.compile(r"morwen", re.I),
    "lind": re.compile(r"lind|cliff|rock.art|world.terrain", re.I),
    "aidan-home": re.compile(r"aidan.?s?.?home|aidan.home", re.I),
}
def classify(title, branch):
    s = title + " " + branch
    return [k for k, pattern in WORKSTREAMS.items() if pattern.search(s)]

def fetch_all(repo, token):
    out = []
    for page in range(1, 51):
        url = f"https://api.github.com/repos/{repo}/pulls?state=open&per_page=100&page={page}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "TWO-read-only-production-audit",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.load(resp)
        if not isinstance(batch, list):
            raise ValueError("Unexpected GitHub API response")
        out.extend(batch)
        if len(batch) < 100:
            return out
    raise RuntimeError("PR inventory exceeded 5000; refusing incomplete PASS")

def analyze(prs):
    groups = defaultdict(list)
    for pr in prs:
        head = pr.get("head") or {}
        branch = head.get("ref", "")
        for workstream in classify(pr.get("title", ""), branch):
            groups[workstream].append({
                "number": pr["number"], "title": pr["title"],
                "branch": branch, "head_sha": (head.get("sha") or ""),
                "url": pr.get("html_url", ""), "draft": pr.get("draft", False),
            })
    return {
        "total_open_prs": len(prs),
        "groups": dict(groups),
        "multi_pr_workstreams": {k: len(v) for k, v in groups.items() if len(v) > 1},
        "note": "Grouping is a broad search heuristic, not proof of duplicate asset-stage ownership. Review manually before cleanup.",
        "read_only": True,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        ap.error("Invalid owner/repo")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        ap.error("GITHUB_TOKEN required; no unauthenticated fallback")
    report = analyze(fetch_all(args.repo, token))
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"PR_INVENTORY_COMPLETE open={report['total_open_prs']}")
    print("Candidate overlaps:", report["multi_pr_workstreams"])

if __name__ == "__main__":
    main()
