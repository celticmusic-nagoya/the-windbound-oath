"""Budget-aware sequential controller using the shared planner.
Adapter callbacks must enforce the supplied monotonic deadline (bounded_operation
on POSIX), verify native reopen and return checkpoint metadata.
No automatic takeover; retain lease on failure until reconciled.
"""
import time
from session_plan import ready,sha
from shared_asset_lease import acquire,assert_owned,release
from shared_session_contract import asset_key

def run(remote,asset,commit,root,stages,completed,execute,persist,budget=19800,reserve=1800):
    if not 0<reserve<budget<=21600: raise ValueError('invalid budget')
    asset_key(asset)
    started=time.monotonic()
    end=started+budget
    def durable(records,token):
        if time.monotonic()>=end:raise TimeoutError('handoff budget exhausted')
        if persist(records,token,end) is not True:raise RuntimeError('durability unconfirmed')
        if time.monotonic()>=end:raise TimeoutError('handoff deadline exceeded')
        assert_owned(remote,asset,token)
    token=acquire(remote,asset,commit)
    executed=[]
    while True:
        assert_owned(remote,asset,token)
        available=ready(stages,completed,root,budget-(time.monotonic()-started),reserve)
        if not available:break
        stage=next(s for s in stages if s['id']==available[0])
        deadline=min(started+budget-reserve,time.monotonic()+stage['seconds'])
        result=execute(stage,token,deadline)
        if time.monotonic()>deadline:raise TimeoutError('stage deadline exceeded; reconcile retained lease')
        assert_owned(remote,asset,token)
        p=(root/result['path']).resolve()
        if not p.is_relative_to(root.resolve()) or result.get('reopened') is not True or sha(p)!=result.get('sha256') or result.get('fingerprint')!=stage['fingerprint']:raise RuntimeError('invalid checkpoint')
        updated={**completed,stage['id']:result}
        # Must confirm durable off-runner persistence before advancing.
        durable(updated,token)
        completed.update(updated)
        executed.append(stage['id'])
    durable(completed,token)
    release(remote,asset,token)
    return executed
