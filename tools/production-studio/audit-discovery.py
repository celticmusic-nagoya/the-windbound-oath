#!/usr/bin/env python3
"""Read-only audit of candidate GitHub Actions artifacts; never downloads or publishes."""
import argparse
import json
import os
import pathlib
import subprocess
from collections import Counter

BRANCHES = {
    "feature/lind-cliff-rock-art-study-20261118": "cliff",
    "feature/morwen-artdirected-sculpt-20261119": "morwen",
    "feature/lind-home-01": "village",
    "feature/lind-buildings-01": "village",
    "feature/lind-village-world-integration-plan-01": "village",
}

def api(repo, suffix):
    return json.loads(subprocess.check_output(
        ["gh", "api", f"repos/{repo}/{suffix}"], text=True
    ))

def audit(repo, per_branch, published, pinned):
    known = {int(x["artifact_id"]) for x in pinned}
    # Count only metadata, not images: no assumption about asset license or publishability.
    rows = []
    for branch, category in BRANCHES.items():
        for page in range(1, 1 + (per_branch + 99) // 100):
            remaining = per_branch - (page - 1) * 100
            runs = api(repo, f"actions/runs?branch={branch}&status=success&per_page={min(remaining, 100)}&page={page}")["workflow_runs"]
            for run in runs:
                if run.get("head_branch") != branch or (run.get("head_repository") or {}).get("full_name") != repo:
                    continue
                for artifact in api(repo, f"actions/runs/{run['id']}/artifacts?per_page=100")["artifacts"]:
                    rows.append({
                        "branch": branch, "category": category,
                        "run_id": run["id"], "artifact_id": artifact["id"],
                        "head": run["head_sha"], "name": artifact["name"],
                        "expired": bool(artifact["expired"]),
                        "size_bytes": artifact["size_in_bytes"],
                        "already_pinned": artifact["id"] in known,
                    })
            if len(runs) < min(remaining, 100):
                break
    rows.sort(key=lambda x: (x["branch"], -x["run_id"], x["artifact_id"]))
    eligible = [x for x in rows if not x["expired"] and x["size_bytes"] > 0 and not x["already_pinned"]]
    return {
        "status": "METADATA_ONLY_NOT_APPROVED_FOR_PUBLICATION",
        "main_seed_manifest_entries": len(published["entries"]),
        "published_branch_entries": None,  # Not fetched: studio-published is a separate branch.
        "scanned_successful_runs_per_branch_max": per_branch,
        "artifacts_seen": len(rows),
        "unexpired_unpinned_artifacts": len(eligible),
        "unexpired_unpinned_by_category": dict(Counter(x["category"] for x in eligible)),
        "candidates": eligible,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-branch", type=int, default=10)
    parser.add_argument("--output", default="studio-discovery-audit.json")
    args = parser.parse_args()
    if not 1 <= args.per_branch <= 50:
        parser.error("--per-branch must be 1..50")
    root = pathlib.Path(__file__).resolve().parent
    repo = os.environ["GITHUB_REPOSITORY"]
    result = audit(repo, args.per_branch,
                   json.loads((root / "gallery-manifest.json").read_text()),
                   json.loads((root / "sync-selection.json").read_text()))
    pathlib.Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "candidates"}, ensure_ascii=False))

if __name__ == "__main__":
    main()
