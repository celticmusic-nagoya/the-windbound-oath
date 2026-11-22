"""Fail-closed plan for a new QA dispatch; never submits requests."""
import re

def plan(request, branch_head, runs, workflow_on_default, lease_free):
    if set(request)!={"asset","branch","head","workflow","minutes"}:
        raise ValueError("invalid request keys")
    from shared_session_contract import asset_key
    asset_key(request["asset"])
    if not re.fullmatch(r"[0-9a-f]{40}",request["head"]) or request["head"]!=branch_head:
        raise ValueError("stale head")
    if not isinstance(request["minutes"],int) or isinstance(request["minutes"],bool) or not 1<=request["minutes"]<=10:
        raise ValueError("isolated QA budget only")
    allowed={"MORWEN":("feature/morwen-artdirected-sculpt-20261119","morwen-shared-isolated-qa.yml")}
    if allowed.get(request["asset"])!=(request["branch"],request["workflow"]):
        raise ValueError("workflow not allowlisted")
    if not lease_free:
        return "BLOCKED_LEASE"
    for run in runs:
        if run["status"]!="completed":
            return "BLOCKED_ACTIVE_RUN"
        if run["head_sha"]==request["head"] and run["conclusion"]=="success":
            return "REUSE_SUCCESS"
    if not workflow_on_default:
        return "BLOCKED_DEFAULT_REGISTRATION"
    return "READY_FOR_AUTHORIZED_DISPATCH"

if __name__=="__main__":
    q=dict(asset="MORWEN",branch="feature/morwen-artdirected-sculpt-20261119",head="a"*40,workflow="morwen-shared-isolated-qa.yml",minutes=10)
    assert plan(q,q["head"],[],True,True)=="READY_FOR_AUTHORIZED_DISPATCH"
    assert plan(q,q["head"],[],False,True)=="BLOCKED_DEFAULT_REGISTRATION"
    assert plan(q,q["head"],[],True,False)=="BLOCKED_LEASE"
    assert plan(q,q["head"],[dict(status="queued")],True,True)=="BLOCKED_ACTIVE_RUN"
    assert plan(q,q["head"],[dict(status="completed",head_sha=q["head"],conclusion="success")],False,True)=="REUSE_SUCCESS"
    try: plan(q,"b"*40,[],True,True)
    except ValueError: pass
    else: raise AssertionError("stale head accepted")
    print("DISPATCH_PREFLIGHT_PASS")
