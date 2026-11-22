"""Connect live Actions observations to the shared CAS reservation.

The caller supplies the owner-confirmed writer inventory and a fenced worker.
A reservation alone is not permission to dispatch an unmigrated writer.
"""
from urllib.parse import quote

from classify_actions_jobs import classify, fingerprint
from collect_actions_snapshot import collect, get_json
from reconcile_actions_snapshot import reconcile
from shared_artifact_reuse import verify_reuse
from shared_asset_lease import acquire, assert_owned, release
from shared_production_readiness import handoff_digest, readiness_issues
from shared_session_contract import asset_key


def reserve(repo, remote, request, ledger, writer_paths, token,
            *, writers_migrated, handoff=None, get=get_json, verify_artifact=verify_reuse):
    """Return a decision and, only on eligibility, an owned fencing token."""
    asset = asset_key(request["asset_id"])
    if writers_migrated is not True or not writer_paths:
        return {"decision": "BLOCKED_WRITER_MIGRATION"}
    if request["workflow_path"] not in writer_paths:
        raise ValueError("requested workflow is absent from the writer inventory")
    issues = readiness_issues(request, handoff, writer_paths)
    if issues:
        return {"decision": "BLOCKED_PRODUCTION_READINESS", "missing_or_mismatched": issues}
    evidence = handoff_digest(handoff)
    branch = quote(request["branch"], safe="")
    branch_url = f"https://api.github.com/repos/{repo}/branches/{branch}"

    def current_head():
        return get(branch_url, token)["commit"]["sha"]

    snapshot = collect(repo, token, get=get, complete=True)
    if snapshot.get("scope") != "repository_all_events" or snapshot.get("complete") is not True:
        raise ValueError("complete repository snapshot required")
    writers = {run["run_id"]: run for run in snapshot["runs"]
               if run["path"] in writer_paths}
    if any(run["status"] != "completed" for run in writers.values()):
        return {"decision": "BLOCKED_ACTIVE_WRITER"}
    relevant = [entry for entry in ledger if entry["asset_id"] == asset]
    recorded_ids = {entry.get("run_id") for entry in relevant}
    if any(run["head_sha"] == request["head_sha"]
           and run["head_branch"] == request["branch"]
           and run["path"] == request["workflow_path"]
           and run["run_id"] not in recorded_ids for run in writers.values()):
        return {"decision": "REVIEW_REQUIRED"}
    if current_head() != request["head_sha"]:
        return {"decision": "BLOCKED_STALE_HEAD"}
    checked = []
    for entry in relevant:
        record = dict(entry)
        run = writers.get(record.get("run_id"))
        if run is None or record.get("workflow_path") != run["path"]:
            return {"decision": "REVIEW_REQUIRED"}
        if record["status"] == "SUCCESS":
            if fingerprint(record) != fingerprint(request):
                if record["stage"] == request["stage"]:
                    return {"decision": "REVIEW_REQUIRED"}
                continue
            if (run["head_sha"] != request["head_sha"]
                    or run["head_branch"] != request["branch"]
                    or run["path"] != request["workflow_path"]):
                return {"decision": "REVIEW_REQUIRED"}
            if verify_artifact(repo, token, record["artifact"], run,
                               request["output_contract"]) is not True:
                return {"decision": "BLOCKED_ARTIFACT"}
            record.update(artifact_sha256_verified=True, artifact_accessible=True,
                          output_contract_verified=True)
        checked.append(record)
    if reconcile(checked, snapshot)["review_count"]:
        return {"decision": "REVIEW_REQUIRED"}
    decision = classify(request, checked)
    if decision["decision"] != "RUN_ELIGIBLE":
        return decision
    lease = acquire(remote, asset, request["head_sha"])
    assert_owned(remote, asset, lease)
    try:
        latest = collect(repo, token, get=get, complete=True)
        unchanged = latest == snapshot and current_head() == request["head_sha"]
    except (OSError, ValueError, KeyError, TypeError):
        release(remote, asset, lease)
        raise
    if not unchanged:
        release(remote, asset, lease)
        return {"decision": "BLOCKED_SNAPSHOT_CHANGED"}
    assert_owned(remote, asset, lease)
    return {"decision": "RESERVED", "token": lease,
            "fingerprint": decision["fingerprint"], "handoff_sha256": evidence}
