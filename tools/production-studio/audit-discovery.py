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
    "infra/native-env-qualification-20261123": "hairharpy",
    "infra/morwen-native-dispatch-20261121": "reference",
    "main": "mixed",
}

def api(repo, suffix):
    return json.loads(subprocess.check_output(
        ["gh", "api", f"repos/{repo}/{suffix}"], text=True
    ))

def classify_new_source(branch, category, run, artifact):
    """Classify only evidenced producer workflows; references are not approved blueprints."""
    workflow = run.get("path", "").split("@", 1)[0]
    name = artifact.get("name", "").lower()
    if branch == "main":
        if workflow == ".github/workflows/morwen-vroid-macos-probe.yml" and name == "morwen-isolated-vroid-reopen-review":
            return "morwen"
        if workflow == ".github/workflows/all-character-reference-zip.yml" and name == "the_windbound_oath_all_character_references":
            return "reference"
        return None
    if category == "hairharpy":
        return "morwen" if workflow == ".github/workflows/two-native-env-qualification.yml" and name.startswith("two-hairharpy-volume-") else None
    if category == "reference":
        return "reference" if workflow == ".github/workflows/all-character-reference-zip.yml" and name == "the_windbound_oath_all_character_references" else None
    return category

def audit(repo, per_branch, published, pinned, live_published=None):
    known = {int(x["artifact_id"]) for x in pinned}
    published_ids = {int(e["artifact_id"]) for e in (live_published or {}).get("entries", []) if str(e.get("artifact_id", "")).isdigit()}
    # Count only metadata, not images: no assumption about asset license or publishability.
    rows = []
    for branch, category in BRANCHES.items():
        # Main has frequent Pages runs; inspect a wider bounded window without
        # downloading or querying artifacts from unrelated workflows.
        limit = 100 if branch == "main" else per_branch
        for page in range(1, 1 + (limit + 99) // 100):
            remaining = limit - (page - 1) * 100
            runs = api(repo, f"actions/runs?branch={branch}&status=success&per_page={min(remaining, 100)}&page={page}")["workflow_runs"]
            for run in runs:
                if run.get("head_branch") != branch or (run.get("head_repository") or {}).get("full_name") != repo:
                    continue
                if branch == "main" and run.get("path", "").split("@", 1)[0] not in (".github/workflows/morwen-vroid-macos-probe.yml", ".github/workflows/all-character-reference-zip.yml"):
                    continue
                for artifact in api(repo, f"actions/runs/{run['id']}/artifacts?per_page=100")["artifacts"]:
                    classified = classify_new_source(branch, category, run, artifact)
                    if classified is None:
                        continue
                    rows.append({
                        "branch": branch, "category": classified,
                        "workflow": run.get("path"), "publication": "REVIEW_REQUIRED",
                        "run_id": run["id"], "artifact_id": artifact["id"],
                        "head": run["head_sha"], "name": artifact["name"],
                        "expired": bool(artifact["expired"]),
                        "size_bytes": artifact["size_in_bytes"],
                        "already_pinned": artifact["id"] in known,
                        "already_published_artifact": artifact["id"] in published_ids,
                    })
            if len(runs) < min(remaining, 100):
                break
    rows.sort(key=lambda x: (x["branch"], -x["run_id"], x["artifact_id"]))
    eligible = [x for x in rows if not x["expired"] and x["size_bytes"] > 0 and not x["already_pinned"] and not x["already_published_artifact"]]
    return {
        "status": "METADATA_ONLY_NOT_APPROVED_FOR_PUBLICATION",
        "main_seed_manifest_entries": len(published["entries"]),
        "published_branch_entries": len(live_published["entries"]) if live_published is not None else None,
        "scanned_successful_runs_per_branch_max": per_branch,
        "scanned_main_runs_max": 100,
        "reference_archives_are_not_approved_blueprints": True,
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
    try:
        live_published = api(repo, "contents/gallery-manifest.json?ref=studio-published")
        import base64
        live_published = json.loads(base64.b64decode(live_published["content"]).decode())
    except (subprocess.CalledProcessError, KeyError, ValueError) as exc:
        print(f"WARNING: published manifest unavailable: {exc}", file=__import__("sys").stderr)
        live_published = None
    result = audit(repo, args.per_branch,
                   json.loads((root / "gallery-manifest.json").read_text()),
                   json.loads((root / "sync-selection.json").read_text()), live_published)
    pathlib.Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "candidates"}, ensure_ascii=False))

if __name__ == "__main__":
    main()
