"""Budget-aware sequential controller using the shared planner.
Adapter callbacks must enforce the supplied monotonic deadline (bounded_operation
on POSIX), verify native reopen and return checkpoint metadata.
No automatic takeover; retain lease on failure until reconciled.
"""
import time
from session_plan import ready,sha
from shared_asset_lease import acquire,assert_owned,claim_reservation,release
from shared_blueprint_contract import measurement_issues, target_issues
from shared_session_contract import asset_key

def run(remote,asset,commit,root,stages,completed,execute,persist,budget=19800,reserve=1800,
        *, reservation=None, fenced=False, blueprint_targets=None):
    """Carry a dispatch reservation into the worker and use the returned fence at each stage.

    In fenced mode, persist must atomically publish a changed ledger and return
    its new lease token. It must also confirm an unchanged ledger when no stage
    was executed by returning the current token after verifying durability.
    """
    if not 0<reserve<budget<=21600: raise ValueError('invalid budget')
    asset_key(asset)
    started=time.monotonic()
    end=started+budget
    def durable(records,token,changed):
        if time.monotonic()>=end:raise TimeoutError('handoff budget exhausted')
        confirmation = persist(records,token,end)
        if fenced:
            if not isinstance(confirmation, str) or (changed and confirmation == token):
                raise RuntimeError('atomic checkpoint publication unconfirmed')
            token = confirmation
        elif confirmation is not True:
            raise RuntimeError('durability unconfirmed')
        if time.monotonic()>=end:raise TimeoutError('handoff deadline exceeded')
        assert_owned(remote,asset,token)
        return token
    if reservation is None:
        token=acquire(remote,asset,commit)
    else:
        if not fenced:
            raise ValueError('dispatch reservations require fenced publication')
        token=claim_reservation(remote,asset,reservation,commit)
    executed=[]
    while True:
        assert_owned(remote,asset,token)
        available=ready(stages,completed,root,budget-(time.monotonic()-started),reserve)
        if not available:break
        stage=next(s for s in stages if s['id']==available[0])
        blueprint = (blueprint_targets or {}).get(stage["id"])
        if blueprint is not None:
            target, request = blueprint
            if request.get("asset_id") != asset or request.get("head_sha") != commit or request.get("stage") != stage["id"]:
                raise ValueError("blueprint request does not match the session stage")
            issues = target_issues(target, request)
            if issues:
                raise ValueError("blueprint target blocked: " + ", ".join(issues))
        deadline=min(started+budget-reserve,time.monotonic()+stage['seconds'])
        result=execute(stage,token,deadline)
        if time.monotonic()>deadline:raise TimeoutError('stage deadline exceeded; reconcile retained lease')
        assert_owned(remote,asset,token)
        p=(root/result['path']).resolve()
        if not p.is_relative_to(root.resolve()) or result.get('reopened') is not True or sha(p)!=result.get('sha256') or result.get('fingerprint')!=stage['fingerprint']:raise RuntimeError('invalid checkpoint')
        if blueprint is not None:
            observation = result.get("observation")
            issues = measurement_issues(target, request, observation)
            if issues or observation["native_sha256"] != result["sha256"]:
                raise RuntimeError("blueprint checkpoint blocked: " + ", ".join(issues or ["native_sha256"]))
        # Invalidate descendants even if an upstream stage reused its nominal fingerprint.
        invalid={stage['id']}
        while True:
            expanded=invalid | {s['id'] for s in stages if set(s['deps']) & invalid}
            if expanded==invalid:break
            invalid=expanded
        updated={k:v for k,v in completed.items() if k not in invalid}
        updated[stage['id']]=result
        # Must confirm durable off-runner persistence before advancing.
        token=durable(updated,token,changed=True)
        completed.clear()
        completed.update(updated)
        executed.append(stage['id'])
    if not fenced or not executed:
        token=durable(completed,token,changed=False)
    release(remote,asset,token)
    return executed
